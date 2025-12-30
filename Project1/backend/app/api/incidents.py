"""
Incident management API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid
from loguru import logger

from app.models.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentTriageResult,
    ResolutionSuggestion,
    IncidentSeverity,
    IncidentStatus
)

router = APIRouter()

# In-memory storage (in production, use a database)
incidents_db = {}


@router.post("/", response_model=IncidentResponse)
async def create_incident(incident: IncidentCreate, request: Request):
    """Create a new incident"""
    incident_id = str(uuid.uuid4())
    
    incident_data = IncidentResponse(
        id=incident_id,
        title=incident.title,
        description=incident.description,
        service=incident.service,
        severity=incident.severity or IncidentSeverity.P2,
        status=IncidentStatus.DETECTED,
        assigned_to=None,
        detected_at=datetime.utcnow(),
        triaged_at=None,
        resolved_at=None,
        root_cause=None,
        resolution_steps=None,
        metadata=incident.metadata
    )
    
    incidents_db[incident_id] = incident_data
    
    logger.info(f"📢 New incident created: {incident_id} - {incident.title}")
    
    return incident_data


@router.post("/trigger", response_model=IncidentResponse)
async def trigger_test_incident(
    severity: Optional[str] = "high",
    service: Optional[str] = "kubernetes",
    request: Request = None
):
    """Trigger a test incident (for demo purposes)"""
    test_incidents = {
        "high": {
            "title": "Kubernetes Pod Crash Loop",
            "description": "Multiple pods in production namespace are crashing and restarting continuously. Error logs show 'OutOfMemoryError' and connection timeouts to database.",
            "severity": IncidentSeverity.P1
        },
        "medium": {
            "title": "Database Connection Pool Exhausted",
            "description": "Application experiencing slow response times. Database connection pool is at 95% capacity with multiple timeout errors in logs.",
            "severity": IncidentSeverity.P2
        },
        "low": {
            "title": "High CPU Usage on Worker Nodes",
            "description": "CPU utilization on worker nodes has been above 80% for the past hour. No service degradation reported yet.",
            "severity": IncidentSeverity.P3
        }
    }
    
    incident_template = test_incidents.get(severity.lower(), test_incidents["medium"])
    
    incident = IncidentCreate(
        title=incident_template["title"],
        description=incident_template["description"],
        service=service,
        severity=incident_template["severity"],
        metadata={"triggered_by": "demo", "test": True}
    )
    
    return await create_incident(incident, request)


@router.get("/", response_model=List[IncidentResponse])
async def list_incidents(status: Optional[str] = None):
    """List all incidents, optionally filtered by status"""
    incidents = list(incidents_db.values())
    
    if status:
        incidents = [i for i in incidents if i.status.value == status.lower()]
    
    return sorted(incidents, key=lambda x: x.detected_at, reverse=True)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """Get a specific incident"""
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return incidents_db[incident_id]


@router.post("/{incident_id}/triage", response_model=IncidentTriageResult)
async def triage_incident(incident_id: str, request: Request):
    """Use AI to triage an incident"""
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[incident_id]
    
    # Get RAG service and LLM service
    rag_service = request.state.rag_service
    llm_service = request.state.llm_service
    
    if not rag_service or not llm_service:
        raise HTTPException(status_code=503, detail="RAG or LLM service not available")
    
    # Search for relevant documentation
    query = f"{incident.description} {incident.service or ''}"
    relevant_docs = rag_service.search(query, n_results=5)
    
    # Use LLM to triage
    triage_result = await llm_service.triage_incident(
        incident_description=incident.description,
        service=incident.service,
        context=relevant_docs
    )
    
    # Update incident with triage results
    incident.status = IncidentStatus.TRIAGED
    incident.triaged_at = datetime.utcnow()
    incident.root_cause = triage_result.get("root_cause", "Unknown")
    incident.severity = IncidentSeverity(triage_result.get("severity", "P2"))
    
    # Create response
    result = IncidentTriageResult(
        incident_id=incident_id,
        severity=incident.severity,
        suggested_category=triage_result.get("category", "Unknown"),
        likely_root_cause=triage_result.get("root_cause", "Unknown"),
        confidence_score=triage_result.get("confidence", 0.5),
        relevant_docs=relevant_docs,
        recommended_actions=triage_result.get("recommended_actions", [])
    )
    
    logger.info(f"🔍 Incident {incident_id} triaged: {result.suggested_category} ({result.severity.value})")
    
    return result


@router.post("/{incident_id}/resolve", response_model=ResolutionSuggestion)
async def get_resolution_suggestion(incident_id: str, request: Request):
    """Get AI-suggested resolution steps"""
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[incident_id]
    
    rag_service = request.state.rag_service
    llm_service = request.state.llm_service
    
    if not rag_service or not llm_service:
        raise HTTPException(status_code=503, detail="RAG or LLM service not available")
    
    # Search for relevant troubleshooting docs
    query = f"how to fix {incident.root_cause or incident.description}"
    relevant_docs = rag_service.search(query, n_results=5)
    
    # Get resolution suggestion from LLM
    resolution = await llm_service.suggest_resolution(
        incident_description=incident.description,
        root_cause=incident.root_cause or "Unknown",
        context=relevant_docs
    )
    
    # Create response
    suggestion = ResolutionSuggestion(
        incident_id=incident_id,
        suggestion=resolution.get("strategy", "Manual investigation required"),
        confidence=resolution.get("confidence", 0.0),
        reasoning=resolution.get("reasoning", ""),
        steps=resolution.get("steps", []),
        relevant_documentation=relevant_docs
    )
    
    logger.info(f"💡 Resolution suggestion generated for incident {incident_id}")
    
    return suggestion


@router.post("/{incident_id}/assign")
async def assign_incident(incident_id: str, assigned_to: str):
    """Assign incident to an engineer"""
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[incident_id]
    incident.assigned_to = assigned_to
    incident.status = IncidentStatus.ASSIGNED
    
    logger.info(f"👤 Incident {incident_id} assigned to {assigned_to}")
    
    return {"status": "assigned", "assigned_to": assigned_to}


@router.post("/{incident_id}/resolve-manual")
async def mark_resolved(incident_id: str, resolution_steps: List[str]):
    """Mark incident as resolved with manual steps"""
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[incident_id]
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.utcnow()
    incident.resolution_steps = resolution_steps
    
    logger.info(f"✅ Incident {incident_id} marked as resolved")
    
    return {"status": "resolved", "resolved_at": incident.resolved_at}

