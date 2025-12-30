"""
Main FastAPI application for SRE Incident Triage Agent
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from loguru import logger

from app.api import incidents, rag, health
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService


# Global services
rag_service = None
llm_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global rag_service, llm_service
    
    logger.info("🚀 Starting SRE Incident Triage Agent...")
    
    # Initialize RAG service
    try:
        rag_service = RAGService()
        logger.info("✅ RAG service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG service: {e}")
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        logger.info("✅ LLM service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM service: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SRE Incident Triage Agent API",
    description="AI-powered incident triage and resolution system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SRE Incident Triage Agent",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "incidents": "/api/incidents",
            "rag": "/api/rag"
        }
    }


# Make services available to routers
@app.middleware("http")
async def add_services_to_request(request, call_next):
    """Add services to request state"""
    request.state.rag_service = rag_service
    request.state.llm_service = llm_service
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

