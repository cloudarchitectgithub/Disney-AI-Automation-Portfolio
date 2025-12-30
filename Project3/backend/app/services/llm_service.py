"""
LLM Service for Vulnerability Remediation Planning
"""
import os
import httpx
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.vulnerability import VulnerabilityResponse, RemediationPlan


class LLMService:
    """Service for interacting with LLM via OpenRouter"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        
        if not self.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not set. LLM features will be limited.")
            self.client = None
        else:
            self.client = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/disney-vulnerability-agent",
                    "X-Title": "Disney Vulnerability Agent"
                }
            )
            logger.info(f"✅ LLM Service initialized with model: {self.openrouter_model}")
    
    async def generate_remediation_plan(
        self,
        vulnerability: VulnerabilityResponse,
        rag_context: List[Dict[str, Any]]
    ) -> RemediationPlan:
        """Generate remediation plan using LLM"""
        if not self.client:
            return self._fallback_remediation_plan(vulnerability)
        
        # Build context from RAG
        context_text = ""
        if rag_context:
            context_text = "\n\nRelevant Documentation:\n"
            for doc in rag_context[:3]:
                context_text += f"- {doc.get('content', '')[:500]}\n"
        
        prompt = f"""Generate a detailed remediation plan for the following vulnerability:

CVE: {vulnerability.cve_id}
Title: {vulnerability.title}
Description: {vulnerability.description}
CVSS Score: {vulnerability.cvss_score}
Affected Components: {', '.join(vulnerability.affected_components)}

{context_text}

Provide a remediation plan in JSON format:
{{
    "plan": "overall remediation strategy",
    "steps": ["step1", "step2", "step3", "step4", "step5"],
    "estimated_effort_hours": 4.0,
    "risk_level": "low|medium|high",
    "rollback_plan": "how to rollback if needed",
    "testing_requirements": ["test1", "test2"]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are a security expert. Provide clear, actionable remediation plans. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.client.post(
                f"{self.openrouter_base_url}/chat/completions",
                json={
                    "model": self.openrouter_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1500
                }
            )
            response.raise_for_status()
            data = response.json()
            llm_response = data["choices"][0]["message"]["content"]
            
            # Parse JSON
            import json
            if "```json" in llm_response:
                llm_response = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                llm_response = llm_response.split("```")[1].split("```")[0].strip()
            
            plan_data = json.loads(llm_response)
            
            return RemediationPlan(
                vulnerability_id=vulnerability.id,
                plan=plan_data.get("plan", "Review and apply security patches"),
                steps=plan_data.get("steps", []),
                estimated_effort_hours=plan_data.get("estimated_effort_hours", 4.0),
                risk_level=plan_data.get("risk_level", "medium"),
                rollback_plan=plan_data.get("rollback_plan"),
                testing_requirements=plan_data.get("testing_requirements", [])
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to generate remediation plan: {e}")
            return self._fallback_remediation_plan(vulnerability)
    
    def _fallback_remediation_plan(self, vulnerability: VulnerabilityResponse) -> RemediationPlan:
        """Fallback remediation plan if LLM is unavailable"""
        return RemediationPlan(
            vulnerability_id=vulnerability.id,
            plan=f"Review {vulnerability.cve_id} and apply recommended security patches",
            steps=[
                "1. Review CVE details and affected components",
                "2. Identify required patches or updates",
                "3. Test patches in staging environment",
                "4. Apply patches to production",
                "5. Verify remediation and monitor"
            ],
            estimated_effort_hours=4.0,
            risk_level="medium"
        )
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

