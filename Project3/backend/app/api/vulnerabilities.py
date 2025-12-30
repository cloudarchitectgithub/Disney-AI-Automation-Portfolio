"""
Vulnerability Management API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from loguru import logger

from app.models.vulnerability import (
    VulnerabilityCreate,
    VulnerabilityResponse,
    VulnerabilityTriageResult,
    OwnershipAssignment,
    RemediationPlan,
    VulnerabilityStatus,
    VulnerabilitySeverity
)

router = APIRouter()

# In-memory storage (in production, use a database)
vulnerabilities_db = {}


@router.post("/", response_model=VulnerabilityResponse)
async def create_vulnerability(vulnerability: VulnerabilityCreate, request: Request):
    """Create a new vulnerability"""
    vuln_id = str(uuid.uuid4())
    
    # Determine severity from CVSS score
    prioritizer = request.state.vulnerability_prioritizer
    severity = prioritizer.determine_severity(vulnerability.cvss_score)
    
    vuln_data = VulnerabilityResponse(
        id=vuln_id,
        cve_id=vulnerability.cve_id,
        title=vulnerability.title,
        description=vulnerability.description,
        cvss_score=vulnerability.cvss_score,
        severity=severity,
        status=VulnerabilityStatus.DETECTED,
        affected_components=vulnerability.affected_components or [],
        assigned_to=None,
        assigned_team=None,
        recommended_team=None,
        recommended_owner=None,
        detected_at=vulnerability.detected_at or datetime.utcnow(),
        triaged_at=None,
        remediated_at=None,
        sla_deadline=None,
        priority_score=0.0,
        business_impact=None,
        remediation_steps=None,
        metadata=vulnerability.metadata
    )
    
    vulnerabilities_db[vuln_id] = vuln_data
    
    logger.info(f"🔒 New vulnerability detected: {vuln_id} - {vulnerability.cve_id}")
    
    return vuln_data


@router.get("/", response_model=List[VulnerabilityResponse])
async def list_vulnerabilities(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    team: Optional[str] = None
):
    """List all vulnerabilities, optionally filtered"""
    vulnerabilities = list(vulnerabilities_db.values())
    
    if status:
        vulnerabilities = [v for v in vulnerabilities if v.status.value == status.lower()]
    
    if severity:
        vulnerabilities = [v for v in vulnerabilities if v.severity.value == severity.upper()]
    
    if team:
        vulnerabilities = [v for v in vulnerabilities if v.assigned_team == team]
    
    # Sort by priority score (highest first)
    return sorted(vulnerabilities, key=lambda x: x.priority_score, reverse=True)


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(vulnerability_id: str):
    """Get a specific vulnerability"""
    if vulnerability_id not in vulnerabilities_db:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    return vulnerabilities_db[vulnerability_id]


@router.post("/{vulnerability_id}/triage", response_model=VulnerabilityTriageResult)
async def triage_vulnerability(vulnerability_id: str, request: Request):
    """Use AI to triage and prioritize a vulnerability"""
    if vulnerability_id not in vulnerabilities_db:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    vulnerability = vulnerabilities_db[vulnerability_id]
    
    # Get services
    prioritizer = request.state.vulnerability_prioritizer
    rag_service = request.state.rag_service
    
    # Query RAG for relevant security documentation
    rag_context = rag_service.search_vulnerability_info(
        cve_id=vulnerability.cve_id,
        affected_component=vulnerability.affected_components[0] if vulnerability.affected_components else None,
        n_results=5
    )
    
    # Triage vulnerability
    triage_result = prioritizer.triage_vulnerability(
        vulnerability=VulnerabilityCreate(
            cve_id=vulnerability.cve_id,
            title=vulnerability.title,
            description=vulnerability.description,
            cvss_score=vulnerability.cvss_score,
            affected_components=vulnerability.affected_components
        ),
        rag_context=rag_context
    )
    
    # Update vulnerability with triage results
    vulnerability.status = VulnerabilityStatus.TRIAGED
    vulnerability.triaged_at = datetime.utcnow()
    vulnerability.priority_score = triage_result.priority_score
    vulnerability.severity = triage_result.severity
    vulnerability.business_impact = triage_result.business_impact
    vulnerability.sla_deadline = datetime.utcnow() + timedelta(days=triage_result.sla_days)
    
    # Store recommended team/owner from triage (if available)
    # If triage doesn't provide it, we'll get it from ownership assigner
    if not triage_result.recommended_team:
        # Use ownership assigner to get recommendation
        ownership_assigner = request.state.ownership_assigner
        assignment = ownership_assigner.assign_ownership(
            vulnerability_id=vulnerability_id,
            affected_components=vulnerability.affected_components,
            cve_id=vulnerability.cve_id,
            description=vulnerability.description
        )
        vulnerability.recommended_team = assignment["assigned_team"]
        vulnerability.recommended_owner = assignment.get("assigned_to")
    else:
        vulnerability.recommended_team = triage_result.recommended_team
        vulnerability.recommended_owner = triage_result.recommended_owner
    
    # Set triage result ID
    triage_result.vulnerability_id = vulnerability_id
    
    logger.info(f"🔍 Vulnerability {vulnerability_id} triaged: Priority {triage_result.priority_score:.1f}, Severity {triage_result.severity.value}")
    
    return triage_result


@router.post("/{vulnerability_id}/assign", response_model=OwnershipAssignment)
async def assign_ownership(vulnerability_id: str, request: Request):
    """Assign vulnerability ownership using AI"""
    if vulnerability_id not in vulnerabilities_db:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    vulnerability = vulnerabilities_db[vulnerability_id]
    ownership_assigner = request.state.ownership_assigner
    
    # Assign ownership
    assignment = ownership_assigner.assign_ownership(
        vulnerability_id=vulnerability_id,
        affected_components=vulnerability.affected_components,
        cve_id=vulnerability.cve_id,
        description=vulnerability.description
    )
    
    # Update vulnerability
    vulnerability.assigned_team = assignment["assigned_team"]
    vulnerability.assigned_to = assignment.get("assigned_to")
    vulnerability.status = VulnerabilityStatus.ASSIGNED
    
    logger.info(f"👤 Vulnerability {vulnerability_id} assigned to {assignment['assigned_team']} team")
    
    return OwnershipAssignment(**assignment)


@router.post("/{vulnerability_id}/remediation-plan", response_model=RemediationPlan)
async def get_remediation_plan(vulnerability_id: str, request: Request):
    """Get AI-generated remediation plan"""
    if vulnerability_id not in vulnerabilities_db:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    vulnerability = vulnerabilities_db[vulnerability_id]
    rag_service = request.state.rag_service
    llm_service = request.state.llm_service
    
    # Get remediation guidance from RAG
    remediation_docs = rag_service.search_remediation_guidance(
        cve_id=vulnerability.cve_id,
        component=vulnerability.affected_components[0] if vulnerability.affected_components else "",
        n_results=5
    )
    
    # Use LLM to generate remediation plan
    if llm_service:
        plan = await llm_service.generate_remediation_plan(
            vulnerability=vulnerability,
            rag_context=remediation_docs
        )
    else:
        # Fallback plan
        plan = RemediationPlan(
            vulnerability_id=vulnerability_id,
            plan="Review vulnerability details and apply recommended patches",
            steps=[
                "1. Review CVE details",
                "2. Identify affected components",
                "3. Apply security patches",
                "4. Test remediation",
                "5. Verify fix"
            ],
            estimated_effort_hours=4.0,
            risk_level="medium"
        )
    
    return plan


@router.get("/stats/sla-compliance")
async def get_sla_compliance(request: Request):
    """Get SLA compliance statistics"""
    vulnerabilities = list(vulnerabilities_db.values())
    
    total = len(vulnerabilities)
    within_sla = 0
    overdue = 0
    
    for vuln in vulnerabilities:
        if vuln.sla_deadline:
            if datetime.utcnow() < vuln.sla_deadline:
                within_sla += 1
            else:
                overdue += 1
    
    return {
        "total_vulnerabilities": total,
        "within_sla": within_sla,
        "overdue": overdue,
        "compliance_rate": (within_sla / total * 100) if total > 0 else 0
    }

