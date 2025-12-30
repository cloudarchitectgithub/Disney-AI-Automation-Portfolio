"""
LLM Service using OpenRouter API
"""
import os
import httpx
from typing import List, Dict, Any, Optional
from loguru import logger


class LLMConfig:
    """LLM configuration"""
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


class LLMService:
    """Service for interacting with LLM via OpenRouter"""
    
    def __init__(self):
        self.config = LLMConfig()
        
        if not self.config.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not set. LLM features will be limited.")
        
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "HTTP-Referer": "https://github.com/disney-sre-agent",
                "X-Title": "Disney SRE Agent"
            }
        )
        logger.info(f"✅ LLM Service initialized with model: {self.config.openrouter_model}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send chat messages to LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        if not self.config.openrouter_api_key:
            return "LLM API key not configured. Please set OPENROUTER_API_KEY."
        
        try:
            response = await self.client.post(
                f"{self.config.openrouter_base_url}/chat/completions",
                json={
                    "model": self.config.openrouter_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPError as e:
            logger.error(f"❌ LLM API error: {e}")
            return f"Error calling LLM API: {str(e)}"
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM service: {e}")
            return f"Unexpected error: {str(e)}"
    
    async def triage_incident(
        self,
        incident_description: str,
        service: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to triage an incident
        
        Args:
            incident_description: Description of the incident
            service: Affected service name
            context: Relevant documentation context from RAG
            
        Returns:
            Triage analysis dict
        """
        context_text = ""
        if context:
            context_text = "\n\nRelevant Documentation:\n"
            for doc in context[:5]:  # Top 5 most relevant
                context_text += f"- {doc.get('content', '')[:500]}\n"
        
        prompt = f"""You are an expert SRE helping to triage an incident. Analyze the following incident and provide:

1. Severity level (P0=Critical, P1=High, P2=Medium, P3=Low)
2. Likely root cause category (e.g., "Kubernetes pod crash", "Database connection issue", "Network latency")
3. Brief explanation of the likely cause
4. Top 3 recommended immediate actions

Incident Description:
{incident_description}

Affected Service: {service or "Unknown"}

{context_text}

Respond in JSON format:
{{
    "severity": "P0|P1|P2|P3",
    "category": "brief category name",
    "root_cause": "explanation",
    "confidence": 0.0-1.0,
    "recommended_actions": ["action1", "action2", "action3"]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert SRE incident responder. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat(messages, temperature=0.3, max_tokens=1000)
        
        # Try to parse JSON from response
        try:
            import json
            # Extract JSON from response if wrapped in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response: {response}")
            # Fallback response
            return {
                "severity": "P2",
                "category": "Unknown",
                "root_cause": "Unable to analyze - LLM response parsing failed",
                "confidence": 0.0,
                "recommended_actions": ["Review incident manually", "Check service logs", "Contact on-call engineer"]
            }
    
    async def suggest_resolution(
        self,
        incident_description: str,
        root_cause: str,
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM to suggest resolution steps
        
        Args:
            incident_description: Incident description
            root_cause: Identified root cause
            context: Relevant documentation from RAG
            
        Returns:
            Resolution suggestion dict
        """
        context_text = "\n\nRelevant Documentation:\n"
        for doc in context[:5]:
            context_text += f"---\n{doc.get('content', '')[:800]}\n"
        
        prompt = f"""You are an expert SRE helping to resolve an incident. Based on the incident details and relevant documentation, provide:

1. A clear resolution strategy
2. Step-by-step resolution steps
3. Reasoning for each step
4. Confidence level (0.0-1.0)

Incident: {incident_description}
Root Cause: {root_cause}

{context_text}

Respond in JSON format:
{{
    "strategy": "overall resolution approach",
    "steps": ["step1", "step2", "step3"],
    "reasoning": "explanation of approach",
    "confidence": 0.0-1.0
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an expert SRE. Provide clear, actionable resolution steps. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat(messages, temperature=0.4, max_tokens=1500)
        
        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse resolution JSON: {e}")
            return {
                "strategy": "Manual investigation required",
                "steps": ["Review logs", "Check service health", "Verify configuration"],
                "reasoning": "Unable to generate automated resolution",
                "confidence": 0.0
            }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

