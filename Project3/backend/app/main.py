"""
Main FastAPI application for Vulnerability Management Agent
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.api import vulnerabilities, health
from app.services.vulnerability_prioritizer import VulnerabilityPrioritizer
from app.services.ownership_assigner import OwnershipAssigner
from app.services.rag_security_service import SecurityRAGService
from app.services.llm_service import LLMService


# Global services
vulnerability_prioritizer = None
ownership_assigner = None
rag_service = None
llm_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global vulnerability_prioritizer, ownership_assigner, rag_service, llm_service
    
    logger.info("🚀 Starting Vulnerability Management Agent...")
    
    # Initialize services
    vulnerability_prioritizer = VulnerabilityPrioritizer()
    ownership_assigner = OwnershipAssigner()
    
    # Initialize RAG service
    try:
        rag_service = SecurityRAGService()
        logger.info("✅ Security RAG service initialized")
    except Exception as e:
        logger.warning(f"⚠️ RAG service not available: {e}")
        rag_service = None
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        logger.info("✅ LLM service initialized")
    except Exception as e:
        logger.warning(f"⚠️ LLM service not available: {e}")
        llm_service = None
    
    logger.info("✅ Vulnerability Management Agent initialized")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vulnerability Management Agent API",
    description="AI-driven vulnerability prioritization and ownership assignment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["vulnerabilities"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Vulnerability Management Agent",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "vulnerabilities": "/api/vulnerabilities"
        }
    }


# Make services available to routers
@app.middleware("http")
async def add_services_to_request(request, call_next):
    """Add services to request state"""
    request.state.vulnerability_prioritizer = vulnerability_prioritizer
    request.state.ownership_assigner = ownership_assigner
    request.state.rag_service = rag_service
    request.state.llm_service = llm_service
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

