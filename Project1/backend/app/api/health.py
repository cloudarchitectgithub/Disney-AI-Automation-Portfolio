"""
Health check endpoints
"""
from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter()


@router.get("/")
async def health_check(request: Request):
    """Basic health check"""
    try:
        # Check RAG service
        rag_status = "healthy"
        if hasattr(request.state, "rag_service") and request.state.rag_service:
            stats = request.state.rag_service.get_collection_stats()
            rag_status = stats.get("status", "unknown")
        
        # Check LLM service
        llm_status = "healthy"
        if hasattr(request.state, "llm_service") and request.state.llm_service:
            llm_status = "healthy" if request.state.llm_service.config.openrouter_api_key else "no_api_key"
        
        return {
            "status": "healthy",
            "services": {
                "rag": rag_status,
                "llm": llm_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/detailed")
async def detailed_health(request: Request):
    """Detailed health check with service stats"""
    try:
        rag_stats = {}
        if hasattr(request.state, "rag_service") and request.state.rag_service:
            rag_stats = request.state.rag_service.get_collection_stats()
        
        llm_info = {}
        if hasattr(request.state, "llm_service") and request.state.llm_service:
            llm_info = {
                "model": request.state.llm_service.config.openrouter_model,
                "api_configured": bool(request.state.llm_service.config.openrouter_api_key)
            }
        
        return {
            "status": "healthy",
            "rag": rag_stats,
            "llm": llm_info
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

