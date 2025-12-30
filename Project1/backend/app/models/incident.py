"""
Incident data models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    P0 = "P0"  # Critical - Service down
    P1 = "P1"  # High - Major impact
    P2 = "P2"  # Medium - Moderate impact
    P3 = "P3"  # Low - Minor impact


class IncidentStatus(str, Enum):
    """Incident status"""
    DETECTED = "detected"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentCreate(BaseModel):
    """Model for creating an incident"""
    title: str = Field(..., description="Incident title")
    description: str = Field(..., description="Incident description")
    service: Optional[str] = Field(None, description="Affected service")
    severity: Optional[IncidentSeverity] = Field(IncidentSeverity.P2, description="Severity level")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class IncidentResponse(BaseModel):
    """Model for incident response"""
    id: str
    title: str
    description: str
    service: Optional[str]
    severity: IncidentSeverity
    status: IncidentStatus
    assigned_to: Optional[str]
    detected_at: datetime
    triaged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    root_cause: Optional[str]
    resolution_steps: Optional[List[str]]
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class IncidentTriageResult(BaseModel):
    """Result of AI triage analysis"""
    incident_id: str
    severity: IncidentSeverity
    suggested_category: str
    likely_root_cause: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    relevant_docs: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class ResolutionSuggestion(BaseModel):
    """AI-generated resolution suggestion"""
    incident_id: str
    suggestion: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    steps: List[str] = Field(default_factory=list)
    relevant_documentation: List[Dict[str, Any]] = Field(default_factory=list)

