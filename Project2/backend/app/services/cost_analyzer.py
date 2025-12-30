"""
Cost Analysis and Optimization Engine
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict

from app.services.cost_normalizer import UnifiedCostRecord


class CostAnalyzer:
    """Analyzes costs and identifies optimization opportunities"""
    
    def __init__(self):
        logger.info("✅ Cost analyzer initialized")
    
    def analyze_costs(
        self,
        records: List[UnifiedCostRecord],
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze costs and identify optimization opportunities
        
        Args:
            records: List of unified cost records
            analysis_period_days: Number of days to analyze
            
        Returns:
            Analysis results with opportunities
        """
        if not records:
            return {
                "total_cost": 0.0,
                "opportunities": [],
                "summary": {}
            }
        
        # Calculate total cost
        total_cost = sum(r.cost_usd for r in records)
        
        # Group by cloud provider
        by_provider = defaultdict(list)
        for record in records:
            by_provider[record.cloud_provider].append(record)
        
        # Identify opportunities
        opportunities = []
        
        # 1. Idle resources
        idle_opportunities = self._find_idle_resources(records)
        opportunities.extend(idle_opportunities)
        
        # 2. Over-provisioned resources
        over_provisioned = self._find_over_provisioned(records)
        opportunities.extend(over_provisioned)
        
        # 3. Unattached storage
        unattached_storage = self._find_unattached_storage(records)
        opportunities.extend(unattached_storage)
        
        # 4. Reserved instance opportunities
        reserved_opportunities = self._find_reserved_instance_opportunities(records)
        opportunities.extend(reserved_opportunities)
        
        # 5. Cross-region cost differences
        region_opportunities = self._find_region_optimizations(records)
        opportunities.extend(region_opportunities)
        
        # 6. Price change opportunities (provider discounts, price reductions)
        price_change_opportunities = self._find_price_change_opportunities(records)
        opportunities.extend(price_change_opportunities)
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x.get('potential_savings', 0), reverse=True)
        
        # Calculate total potential savings
        total_potential_savings = sum(opp.get('potential_savings', 0) for opp in opportunities)
        
        return {
            "total_cost": total_cost,
            "total_potential_savings": total_potential_savings,
            "savings_percentage": (total_potential_savings / total_cost * 100) if total_cost > 0 else 0,
            "opportunities": opportunities[:20],  # Top 20
            "summary": {
                "by_provider": {
                    provider: sum(r.cost_usd for r in records)
                    for provider, records in by_provider.items()
                },
                "by_category": self._summarize_by_category(records),
                "total_resources": len(records)
            }
        }
    
    def _find_idle_resources(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """Find idle or unused resources"""
        opportunities = []
        
        # Group by resource ID
        by_resource = defaultdict(list)
        for record in records:
            if record.resource_id:
                by_resource[record.resource_id].append(record)
        
        for resource_id, resource_records in by_resource.items():
            total_cost = sum(r.cost_usd for r in resource_records)
            
            # Check if resource has low/no usage metrics
            has_usage = any(
                r.usage_metrics and any(
                    'cpu' in str(v).lower() or 'utilization' in str(v).lower()
                    for v in r.usage_metrics.values()
                )
                for r in resource_records
            )
            
            # If no usage data and cost > $10/month, flag as potentially idle
            if not has_usage and total_cost > 10:
                opportunities.append({
                    "type": "idle_resource",
                    "resource_id": resource_id,
                    "cloud_provider": resource_records[0].cloud_provider,
                    "current_cost": total_cost,
                    "potential_savings": total_cost * 0.9,  # Assume 90% savings if removed
                    "recommendation": "Review resource usage. Consider terminating if unused.",
                    "priority": "high" if total_cost > 100 else "medium"
                })
        
        return opportunities
    
    def _find_over_provisioned(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """Find over-provisioned resources"""
        opportunities = []
        
        # Look for large instance types with low utilization
        for record in records:
            if record.resource_type == 'vm' and record.cost_usd > 50:
                instance_type = record.usage_metrics.get('instance_type', '')
                
                # If it's a large instance type, suggest downsizing
                if any(size in instance_type.lower() for size in ['xlarge', '2xlarge', '4xlarge', '8xlarge']):
                    potential_savings = record.cost_usd * 0.3  # Assume 30% savings from downsizing
                    
                    opportunities.append({
                        "type": "over_provisioned",
                        "resource_id": record.resource_id,
                        "cloud_provider": record.cloud_provider,
                        "current_cost": record.cost_usd,
                        "potential_savings": potential_savings,
                        "recommendation": f"Consider downsizing {instance_type} to smaller instance type",
                        "priority": "medium"
                    })
        
        return opportunities
    
    def _find_unattached_storage(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """Find unattached storage volumes"""
        opportunities = []
        
        for record in records:
            if record.resource_type == 'storage' and record.cost_usd > 5:
                # Check if storage is attached (would have tags or resource_id pattern)
                is_attached = bool(record.tags) or 'attached' in str(record.resource_id).lower()
                
                if not is_attached:
                    opportunities.append({
                        "type": "unattached_storage",
                        "resource_id": record.resource_id,
                        "cloud_provider": record.cloud_provider,
                        "current_cost": record.cost_usd,
                        "potential_savings": record.cost_usd,
                        "recommendation": "Delete unattached storage volume",
                        "priority": "medium"
                    })
        
        return opportunities
    
    def _find_reserved_instance_opportunities(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """Find opportunities for reserved instances"""
        opportunities = []
        
        # Group by instance type and region
        by_instance = defaultdict(list)
        for record in records:
            if record.resource_type == 'vm':
                instance_type = record.usage_metrics.get('instance_type', '')
                key = f"{record.cloud_provider}:{instance_type}:{record.region}"
                by_instance[key].append(record)
        
        for key, instance_records in by_instance.items():
            total_cost = sum(r.cost_usd for r in instance_records)
            
            # If consistent usage > $100/month, suggest reserved instance
            if total_cost > 100 and len(instance_records) > 20:  # Consistent usage
                # Reserved instances typically save 30-70%
                potential_savings = total_cost * 0.4
                
                opportunities.append({
                    "type": "reserved_instance",
                    "resource_id": key,
                    "cloud_provider": instance_records[0].cloud_provider,
                    "current_cost": total_cost,
                    "potential_savings": potential_savings,
                    "recommendation": "Consider purchasing reserved instances for consistent workloads",
                    "priority": "high" if total_cost > 500 else "medium"
                })
        
        return opportunities
    
    def _find_region_optimizations(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """Find cost differences across regions"""
        opportunities = []
        
        # Group by service and resource type
        by_service = defaultdict(lambda: defaultdict(list))
        for record in records:
            key = f"{record.service_category}:{record.resource_type}"
            by_service[key][record.region].append(record)
        
        for service_key, regions in by_service.items():
            if len(regions) < 2:
                continue
            
            # Calculate average cost per region
            region_costs = {
                region: sum(r.cost_usd for r in records)
                for region, records in regions.items()
            }
            
            if region_costs:
                max_cost_region = max(region_costs.items(), key=lambda x: x[1])
                min_cost_region = min(region_costs.items(), key=lambda x: x[1])
                
                if max_cost_region[1] > min_cost_region[1] * 1.2:  # 20% difference
                    potential_savings = max_cost_region[1] - min_cost_region[1]
                    
                    opportunities.append({
                        "type": "region_optimization",
                        "resource_id": service_key,
                        "cloud_provider": "multi",
                        "current_cost": max_cost_region[1],
                        "potential_savings": potential_savings * 0.8,  # 80% of difference (accounting for migration costs)
                        "recommendation": f"Consider migrating from {max_cost_region[0]} to {min_cost_region[0]}",
                        "priority": "low"
                    })
        
        return opportunities
    
    def _find_price_change_opportunities(self, records: List[UnifiedCostRecord]) -> List[Dict[str, Any]]:
        """
        Detect price changes and discount opportunities from cloud providers
        
        This identifies:
        - Recent price reductions by providers
        - New discount programs (spot instances, savings plans)
        - Promotional pricing opportunities
        - Instance type price drops
        """
        opportunities = []
        
        # Mock price change detection (in production, would query pricing APIs)
        # This simulates detecting price reductions or new discount programs
        
        # Group by instance type and provider to detect patterns
        by_instance_type = defaultdict(list)
        for record in records:
            if record.resource_type == 'vm' and record.usage_metrics.get('instance_type'):
                instance_type = record.usage_metrics.get('instance_type', '')
                key = f"{record.cloud_provider}:{instance_type}"
                by_instance_type[key].append(record)
        
        # Simulate price reduction detection
        # In production, this would compare current prices vs historical prices
        price_reductions = {
            # AWS: Recent price cuts on certain instance types
            'aws:m5.xlarge': {'reduction_pct': 15, 'new_discount': 'Savings Plans available'},
            'aws:t3.large': {'reduction_pct': 10, 'new_discount': 'Spot instances 60% cheaper'},
            # GCP: New discount programs
            'gcp:n1-standard-4': {'reduction_pct': 20, 'new_discount': 'Committed Use Discounts'},
            # Azure: Promotional pricing
            'azure:Standard_D4s_v3': {'reduction_pct': 12, 'new_discount': 'Reserved Instances 40% off'}
        }
        
        for key, records_list in by_instance_type.items():
            if key.lower() in price_reductions:
                reduction_info = price_reductions[key.lower()]
                total_cost = sum(r.cost_usd for r in records_list)
                
                # Calculate potential savings from price reduction
                reduction_pct = reduction_info['reduction_pct'] / 100.0
                potential_savings = total_cost * reduction_pct
                
                if potential_savings > 50:  # Only flag if savings > $50/month
                    provider, instance_type = key.split(':', 1)
                    
                    opportunities.append({
                        "type": "price_change_opportunity",
                        "resource_id": f"{provider}:{instance_type}",
                        "cloud_provider": provider,
                        "current_cost": total_cost,
                        "potential_savings": potential_savings,
                        "price_reduction_pct": reduction_info['reduction_pct'],
                        "recommendation": f"Take advantage of {reduction_info['new_discount']}. Price reduced by {reduction_info['reduction_pct']}%",
                        "priority": "high" if potential_savings > 200 else "medium",
                        "action_required": "Switch to discounted pricing or enroll in discount program"
                    })
        
        # Detect spot instance opportunities (significant savings)
        for record in records:
            if record.resource_type == 'vm' and record.cost_usd > 100:
                instance_type = record.usage_metrics.get('instance_type', '')
                # Spot instances typically 60-90% cheaper
                if 'spot' not in str(record.resource_id).lower() and 'spot' not in str(instance_type).lower():
                    # Check if workload is fault-tolerant (could use spot)
                    # In production, would analyze workload characteristics
                    spot_savings = record.cost_usd * 0.7  # 70% savings with spot
                    
                    if spot_savings > 50:
                        opportunities.append({
                            "type": "spot_instance_opportunity",
                            "resource_id": record.resource_id,
                            "cloud_provider": record.cloud_provider,
                            "current_cost": record.cost_usd,
                            "potential_savings": spot_savings,
                            "price_reduction_pct": 70,
                            "recommendation": f"Consider switching to spot instances for fault-tolerant workloads. Save up to 70%",
                            "priority": "medium",
                            "action_required": "Evaluate workload fault tolerance and migrate to spot instances"
                        })
        
        return opportunities
    
    def _summarize_by_category(self, records: List[UnifiedCostRecord]) -> Dict[str, float]:
        """Summarize costs by service category"""
        by_category = defaultdict(float)
        for record in records:
            by_category[record.service_category] += record.cost_usd
        return dict(by_category)

