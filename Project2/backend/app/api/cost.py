"""
Cost Analysis API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.services.data_sources import DataSourceRegistry
from app.services.cost_normalizer import CostNormalizer
from app.services.cost_analyzer import CostAnalyzer
from app.services.price_monitor import PriceMonitor

router = APIRouter()


@router.post("/analyze")
async def analyze_costs(
    request: Request,
    source_names: Optional[list] = None,
    query_params: Optional[Dict[str, Any]] = None
):
    """
    Analyze costs across all or specific data sources
    
    Args:
        source_names: List of source names to analyze (None = all)
        query_params: Query parameters for data sources
    """
    registry: DataSourceRegistry = request.state.data_registry
    normalizer: CostNormalizer = request.state.cost_normalizer
    analyzer: CostAnalyzer = request.state.cost_analyzer
    
    if query_params is None:
        query_params = {"limit": 1000}
    
    # Get sources to query
    if source_names is None:
        source_names = list(registry.sources.keys())
    
    # Query all sources
    all_records = []
    for source_name in source_names:
        try:
            raw_records = registry.query_source(source_name, query_params)
            
            # Normalize records
            provider = source_name.lower()
            if provider == 'aws':
                normalized = normalizer.normalize_batch(raw_records, 'aws')
            elif provider == 'gcp':
                normalized = normalizer.normalize_batch(raw_records, 'gcp')
            elif provider == 'azure':
                normalized = normalizer.normalize_batch(raw_records, 'azure')
            else:
                normalized = normalizer.normalize_batch(raw_records, provider)
            
            all_records.extend(normalized)
        except Exception as e:
            logger.warning(f"Failed to process {source_name}: {e}")
            continue
    
    # Analyze costs
    analysis = analyzer.analyze_costs(all_records)
    
    return {
        "analysis": analysis,
        "records_analyzed": len(all_records),
        "sources_analyzed": source_names
    }


@router.get("/opportunities")
async def get_optimization_opportunities(
    request: Request,
    limit: int = 20
):
    """Get top optimization opportunities"""
    registry: DataSourceRegistry = request.state.data_registry
    normalizer: CostNormalizer = request.state.cost_normalizer
    analyzer: CostAnalyzer = request.state.cost_analyzer
    
    # Query all sources
    all_records = []
    for source_name in registry.sources.keys():
        try:
            raw_records = registry.query_source(source_name, {"limit": 1000})
            provider = source_name.lower()
            normalized = normalizer.normalize_batch(raw_records, provider)
            all_records.extend(normalized)
        except Exception as e:
            logger.warning(f"Failed to process {source_name}: {e}")
            continue
    
    # Analyze and get opportunities
    analysis = analyzer.analyze_costs(all_records)
    
    opportunities = analysis.get("opportunities", [])[:limit]
    
    return {
        "opportunities": opportunities,
        "total_potential_savings": analysis.get("total_potential_savings", 0),
        "total_cost": analysis.get("total_cost", 0),
        "savings_percentage": analysis.get("savings_percentage", 0)
    }


@router.get("/summary")
async def get_cost_summary(request: Request):
    """Get cost summary across all sources"""
    registry: DataSourceRegistry = request.state.data_registry
    normalizer: CostNormalizer = request.state.cost_normalizer
    
    summary = {
        "sources": [],
        "total_cost": 0.0,
        "by_provider": {},
        "by_category": {}
    }
    
    for source_name in registry.sources.keys():
        try:
            raw_records = registry.query_source(source_name, {"limit": 1000})
            provider = source_name.lower()
            normalized = normalizer.normalize_batch(raw_records, provider)
            
            source_cost = sum(r.cost_usd for r in normalized)
            summary["total_cost"] += source_cost
            summary["by_provider"][provider] = source_cost
            
            summary["sources"].append({
                "name": source_name,
                "cost": source_cost,
                "records": len(normalized)
            })
        except Exception as e:
            logger.warning(f"Failed to summarize {source_name}: {e}")
            continue
    
    return summary


@router.get("/check-prices")
async def check_price_changes(request: Request):
    """
    Check for price changes across all cloud providers using REAL price scraper
    
    This endpoint:
    1. Scrapes current prices from AWS, GCP, Azure
    2. Compares with historical prices
    3. Detects changes >5%
    4. Matches to your actual resources
    
    Called by:
    - N8N scheduled workflow (every 6 hours)
    - Manual trigger from dashboard
    - Webhook from cloud provider (when available)
    """
    price_monitor = request.state.price_monitor
    
    try:
        # Get current resources to match changes against
        registry: DataSourceRegistry = request.state.data_registry
        normalizer: CostNormalizer = request.state.cost_normalizer
        
        # Query current resources
        all_resources = []
        for source_name in registry.sources.keys():
            try:
                raw_records = registry.query_source(source_name, {"limit": 1000})
                provider = source_name.lower()
                normalized = normalizer.normalize_batch(raw_records, provider)
                all_resources.extend([r.to_dict() for r in normalized])
            except Exception as e:
                logger.warning(f"Failed to get resources from {source_name}: {e}")
        
        # Check all providers for price changes (with resource matching)
        opportunities = await price_monitor.check_all_providers(resources=all_resources)
        
        # Filter by savings threshold (only significant opportunities)
        # Lowered threshold to $10/month for demo purposes
        significant_opportunities = [
            opp for opp in opportunities 
            if opp.get('potential_savings', 0) > 10
        ]
        
        # Calculate total potential savings
        total_savings = sum(
            opp.get('potential_savings', 0) 
            for opp in significant_opportunities
        )
        
        # Categorize by priority
        high_priority = [opp for opp in significant_opportunities if opp.get('priority') == 'high']
        medium_priority = [opp for opp in significant_opportunities if opp.get('priority') == 'medium']
        
        return {
            "opportunities": significant_opportunities,
            "total_potential_savings": total_savings,
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "checked_at": datetime.utcnow().isoformat(),
            "next_check_recommended": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
            "scraping_method": "real_pricing_data",
            "providers_checked": ["aws", "gcp", "azure"]
        }
    except Exception as e:
        logger.error(f"❌ Price check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

