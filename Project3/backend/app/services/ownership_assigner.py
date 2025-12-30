"""
AI-driven Ownership Assignment Engine
Eliminates manual triage by automatically assigning vulnerabilities to teams
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import re


class OwnershipAssigner:
    """AI-driven ownership assignment based on codebase analysis"""
    
    def __init__(self):
        # Team mappings based on component/service patterns
        self.team_patterns = {
            "sre": {
                "keywords": ["kubernetes", "docker", "infrastructure", "monitoring", "observability", "prometheus", "grafana"],
                "services": ["k8s", "cluster", "node", "pod"]
            },
            "backend": {
                "keywords": ["api", "service", "microservice", "rest", "graphql", "endpoint"],
                "services": ["api", "service", "backend"]
            },
            "frontend": {
                "keywords": ["react", "vue", "angular", "ui", "frontend", "web"],
                "services": ["web", "ui", "frontend"]
            },
            "database": {
                "keywords": ["database", "postgres", "mysql", "mongodb", "redis", "sql"],
                "services": ["db", "database", "postgres", "mysql"]
            },
            "security": {
                "keywords": ["auth", "authentication", "authorization", "oauth", "jwt", "security"],
                "services": ["auth", "security", "identity"]
            },
            "devops": {
                "keywords": ["ci/cd", "pipeline", "jenkins", "gitlab", "github actions", "deployment"],
                "services": ["pipeline", "ci", "cd"]
            },
            "data": {
                "keywords": ["dataflow", "bigquery", "data", "analytics", "etl", "pipeline"],
                "services": ["data", "analytics", "etl"]
            }
        }
        
        logger.info("✅ Ownership assigner initialized")
    
    def assign_ownership(
        self,
        vulnerability_id: str,
        affected_components: List[str],
        cve_id: str,
        description: str,
        codebase_evidence: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assign ownership based on affected components and codebase analysis
        
        Args:
            vulnerability_id: Vulnerability ID
            affected_components: List of affected components/services
            cve_id: CVE identifier
            description: Vulnerability description
            codebase_evidence: Optional codebase file paths/evidence
            
        Returns:
            Ownership assignment with team, owner, and confidence
        """
        # Analyze affected components
        component_scores = self._analyze_components(affected_components, description)
        
        # Analyze codebase evidence if available
        codebase_scores = {}
        if codebase_evidence:
            codebase_scores = self._analyze_codebase(codebase_evidence)
        
        # Combine scores
        combined_scores = self._combine_scores(component_scores, codebase_scores)
        
        # Get top team
        if not combined_scores:
            # Default fallback
            assigned_team = "sre"
            confidence = 0.3
            reason = "No clear ownership pattern detected, defaulting to SRE team"
        else:
            assigned_team = max(combined_scores.items(), key=lambda x: x[1])[0]
            confidence = combined_scores[assigned_team] / 100.0
            reason = self._generate_assignment_reason(assigned_team, affected_components, codebase_evidence)
        
        return {
            "vulnerability_id": vulnerability_id,
            "assigned_team": assigned_team,
            "assigned_to": None,  # Can be enhanced with team member lookup
            "assignment_reason": reason,
            "confidence": min(confidence, 1.0),
            "codebase_evidence": codebase_evidence or [],
            "component_analysis": component_scores,
            "codebase_analysis": codebase_scores
        }
    
    def _analyze_components(self, components: List[str], description: str) -> Dict[str, float]:
        """Analyze affected components to determine team ownership"""
        scores = {team: 0.0 for team in self.team_patterns.keys()}
        
        # Check each component against team patterns
        for component in components:
            component_lower = component.lower()
            
            for team, patterns in self.team_patterns.items():
                # Check keywords
                for keyword in patterns["keywords"]:
                    if keyword in component_lower:
                        scores[team] += 10.0
                
                # Check service names
                for service in patterns["services"]:
                    if service in component_lower:
                        scores[team] += 15.0
        
        # Check description for additional context
        description_lower = description.lower()
        for team, patterns in self.team_patterns.items():
            for keyword in patterns["keywords"]:
                if keyword in description_lower:
                    scores[team] += 5.0
        
        return scores
    
    def _analyze_codebase(self, codebase_evidence: List[str]) -> Dict[str, float]:
        """Analyze codebase file paths to determine ownership"""
        scores = {team: 0.0 for team in self.team_patterns.keys()}
        
        for file_path in codebase_evidence:
            file_lower = file_path.lower()
            
            # Check file path patterns
            for team, patterns in self.team_patterns.items():
                for keyword in patterns["keywords"]:
                    if keyword in file_lower:
                        scores[team] += 8.0
                
                for service in patterns["services"]:
                    if service in file_lower:
                        scores[team] += 12.0
            
            # Check directory patterns
            if "/infrastructure/" in file_lower or "/k8s/" in file_lower:
                scores["sre"] += 10.0
            elif "/api/" in file_lower or "/services/" in file_lower:
                scores["backend"] += 10.0
            elif "/frontend/" in file_lower or "/ui/" in file_lower:
                scores["frontend"] += 10.0
            elif "/database/" in file_lower or "/db/" in file_lower:
                scores["database"] += 10.0
        
        return scores
    
    def _combine_scores(self, component_scores: Dict[str, float], codebase_scores: Dict[str, float]) -> Dict[str, float]:
        """Combine component and codebase scores"""
        combined = {}
        
        for team in self.team_patterns.keys():
            component_score = component_scores.get(team, 0.0)
            codebase_score = codebase_scores.get(team, 0.0)
            
            # Weight codebase evidence higher (more reliable)
            combined[team] = component_score + (codebase_score * 1.5)
        
        return combined
    
    def _generate_assignment_reason(
        self,
        team: str,
        components: List[str],
        codebase_evidence: Optional[List[str]]
    ) -> str:
        """Generate human-readable assignment reason"""
        reasons = []
        
        if components:
            reasons.append(f"Affected components: {', '.join(components[:3])}")
        
        if codebase_evidence:
            reasons.append(f"Codebase evidence: {len(codebase_evidence)} files")
        
        team_descriptions = {
            "sre": "infrastructure and platform services",
            "backend": "backend services and APIs",
            "frontend": "frontend applications",
            "database": "database systems",
            "security": "authentication and security services",
            "devops": "CI/CD pipelines and deployment",
            "data": "data pipelines and analytics"
        }
        
        reason = f"Assigned to {team.upper()} team based on {team_descriptions.get(team, 'component analysis')}"
        if reasons:
            reason += f" ({'; '.join(reasons)})"
        
        return reason
    
    def get_team_members(self, team: str) -> List[str]:
        """Get team members for a team (can be enhanced with real team data)"""
        # Mock team members - in production, would query team directory
        team_members = {
            "sre": ["sre-engineer-1", "sre-engineer-2"],
            "backend": ["backend-engineer-1", "backend-engineer-2"],
            "frontend": ["frontend-engineer-1"],
            "database": ["dba-1"],
            "security": ["security-engineer-1"],
            "devops": ["devops-engineer-1"],
            "data": ["data-engineer-1"]
        }
        
        return team_members.get(team.lower(), [])

