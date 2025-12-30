"""
Main FastAPI application for Cost Optimization Agent
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.api import cost, data_sources, health
from app.services.data_sources import DataSourceRegistry
from app.services.cost_normalizer import CostNormalizer
from app.services.cost_analyzer import CostAnalyzer
from app.services.price_monitor import PriceMonitor


# Global services
data_registry = None
cost_normalizer = None
cost_analyzer = None
price_monitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global data_registry, cost_normalizer, cost_analyzer, price_monitor
    
    logger.info("🚀 Starting Cost Optimization Agent...")
    
    # Initialize services
    data_registry = DataSourceRegistry()
    cost_normalizer = CostNormalizer()
    cost_analyzer = CostAnalyzer()
    price_monitor = PriceMonitor()
    
    # Auto-register data sources if mock data exists
    try:
        from pathlib import Path
        # Try both possible paths
        data_dirs = [Path("/app/data/billing"), Path("/data/billing")]
        
        for data_dir in data_dirs:
            if data_dir.exists():
                logger.info(f"📁 Checking data directory: {data_dir}")
                
                if (data_dir / "aws_billing.csv").exists():
                    from app.services.data_sources import AWSDataSource
                    aws_source = AWSDataSource(str(data_dir / "aws_billing.csv"))
                    data_registry.register("aws", aws_source)
                    logger.info(f"✅ Auto-registered AWS data source")
                
                if (data_dir / "gcp_billing.csv").exists():
                    from app.services.data_sources import GCPDataSource
                    gcp_source = GCPDataSource(str(data_dir / "gcp_billing.csv"))
                    data_registry.register("gcp", gcp_source)
                    logger.info(f"✅ Auto-registered GCP data source")
                
                if (data_dir / "azure_billing.csv").exists():
                    from app.services.data_sources import AzureDataSource
                    azure_source = AzureDataSource(str(data_dir / "azure_billing.csv"))
                    data_registry.register("azure", azure_source)
                    logger.info(f"✅ Auto-registered Azure data source")
                
                break  # Found data directory, stop looking
    except Exception as e:
        logger.warning(f"⚠️ Failed to auto-register data sources: {e}")
    
    logger.info("✅ Cost Optimization Agent initialized")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Cost Optimization Agent API",
    description="Multi-cloud cost optimization with schema-agnostic data access",
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
app.include_router(data_sources.router, prefix="/api/data-sources", tags=["data-sources"])
app.include_router(cost.router, prefix="/api/cost", tags=["cost"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Cost Optimization Agent",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "data_sources": "/api/data-sources",
            "cost": "/api/cost"
        }
    }


# Make services available to routers
@app.middleware("http")
async def add_services_to_request(request, call_next):
    """Add services to request state"""
    request.state.data_registry = data_registry
    request.state.cost_normalizer = cost_normalizer
    request.state.cost_analyzer = cost_analyzer
    request.state.price_monitor = price_monitor
    response = await call_next(request)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

