"""
Data Sources API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from typing import List, Dict, Any
from loguru import logger

from app.services.data_sources import DataSourceRegistry, AWSDataSource, GCPDataSource, AzureDataSource, CSVDataSource

router = APIRouter()


@router.get("/")
async def list_data_sources(request: Request):
    """List all registered data sources"""
    registry: DataSourceRegistry = request.state.data_registry
    return {
        "sources": registry.list_sources(),
        "count": len(registry.sources)
    }


@router.post("/register/aws")
async def register_aws_source(request: Request, file_path: str):
    """Register an AWS billing data source"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        source = AWSDataSource(file_path)
        registry.register("aws", source)
        return {
            "status": "registered",
            "name": "aws",
            "schema": source.get_schema()
        }
    except Exception as e:
        logger.error(f"Failed to register AWS source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/gcp")
async def register_gcp_source(request: Request, file_path: str):
    """Register a GCP billing data source"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        source = GCPDataSource(file_path)
        registry.register("gcp", source)
        return {
            "status": "registered",
            "name": "gcp",
            "schema": source.get_schema()
        }
    except Exception as e:
        logger.error(f"Failed to register GCP source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/azure")
async def register_azure_source(request: Request, file_path: str):
    """Register an Azure billing data source"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        source = AzureDataSource(file_path)
        registry.register("azure", source)
        return {
            "status": "registered",
            "name": "azure",
            "schema": source.get_schema()
        }
    except Exception as e:
        logger.error(f"Failed to register Azure source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/csv")
async def register_csv_source(request: Request, name: str, file_path: str):
    """Register a CSV data source"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        source = CSVDataSource(file_path)
        registry.register(name, source)
        return {
            "status": "registered",
            "name": name,
            "schema": source.get_schema()
        }
    except Exception as e:
        logger.error(f"Failed to register CSV source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{source_name}")
async def query_data_source(
    request: Request,
    source_name: str,
    query_params: Dict[str, Any]
):
    """Query a specific data source"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        results = registry.query_source(source_name, query_params)
        return {
            "source": source_name,
            "results": results,
            "count": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-all")
async def query_all_sources(
    request: Request,
    query_params: Dict[str, Any]
):
    """Query all registered data sources"""
    registry: DataSourceRegistry = request.state.data_registry
    
    try:
        results = registry.query_all_sources(query_params)
        return {
            "results": results,
            "sources_queried": list(results.keys())
        }
    except Exception as e:
        logger.error(f"Query all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

