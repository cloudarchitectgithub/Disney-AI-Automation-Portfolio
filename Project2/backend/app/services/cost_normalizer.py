"""
Cost Normalization Service - Unifies multi-cloud billing data
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import pandas as pd


class UnifiedCostRecord:
    """Unified cost record schema across all cloud providers"""
    
    def __init__(self, data: Dict[str, Any]):
        self.resource_id = data.get('resource_id', '')
        self.cloud_provider = data.get('cloud_provider', '')
        self.service_category = data.get('service_category', '')
        self.resource_type = data.get('resource_type', '')
        self.cost_usd = float(data.get('cost_usd', 0.0))
        self.usage_metrics = data.get('usage_metrics', {})
        self.region = data.get('region', '')
        self.tags = data.get('tags', {})
        self.date = data.get('date', '')
        self.optimization_potential = data.get('optimization_potential', 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'resource_id': self.resource_id,
            'cloud_provider': self.cloud_provider,
            'service_category': self.service_category,
            'resource_type': self.resource_type,
            'cost_usd': self.cost_usd,
            'usage_metrics': self.usage_metrics,
            'region': self.region,
            'tags': self.tags,
            'date': self.date,
            'optimization_potential': self.optimization_potential
        }


class CostNormalizer:
    """Normalizes cloud-specific cost data to unified schema"""
    
    def __init__(self):
        logger.info("✅ Cost normalizer initialized")
    
    def normalize_aws(self, aws_record: Dict[str, Any]) -> UnifiedCostRecord:
        """Normalize AWS billing record to unified schema"""
        # Map AWS-specific fields to unified schema
        resource_id = aws_record.get('lineItem/ResourceId', '')
        cost = float(aws_record.get('lineItem/UnblendedCost', 0.0))
        service = aws_record.get('lineItem/ProductCode', '')
        usage_type = aws_record.get('lineItem/UsageType', '')
        region = aws_record.get('lineItem/AvailabilityZone', '')
        date = aws_record.get('lineItem/UsageStartDate', '')
        
        # Determine service category
        service_category = self._categorize_service(service, 'aws')
        
        # Determine resource type
        resource_type = self._determine_resource_type(service, usage_type, 'aws')
        
        # Extract tags
        tags = {}
        for key, value in aws_record.items():
            if key.startswith('resourceTags/'):
                tag_key = key.replace('resourceTags/', '')
                tags[tag_key] = value
        
        return UnifiedCostRecord({
            'resource_id': resource_id,
            'cloud_provider': 'aws',
            'service_category': service_category,
            'resource_type': resource_type,
            'cost_usd': cost,
            'usage_metrics': {
                'usage_type': usage_type,
                'operation': aws_record.get('lineItem/Operation', ''),
                'instance_type': aws_record.get('product/InstanceType', '')
            },
            'region': region.split('-')[0] if region else '',  # Extract region from AZ
            'tags': tags,
            'date': date
        })
    
    def normalize_gcp(self, gcp_record: Dict[str, Any]) -> UnifiedCostRecord:
        """Normalize GCP billing record to unified schema"""
        resource_id = gcp_record.get('resource.name', '')
        cost = float(gcp_record.get('cost', 0.0))
        service = gcp_record.get('service.description', '')
        region = gcp_record.get('location.region', '')
        date = gcp_record.get('usage_start_time', '')
        
        service_category = self._categorize_service(service, 'gcp')
        resource_type = self._determine_resource_type(service, gcp_record.get('sku.description', ''), 'gcp')
        
        tags = {
            'project': gcp_record.get('project.id', '')
        }
        
        return UnifiedCostRecord({
            'resource_id': resource_id,
            'cloud_provider': 'gcp',
            'service_category': service_category,
            'resource_type': resource_type,
            'cost_usd': cost,
            'usage_metrics': {
                'sku': gcp_record.get('sku.description', ''),
                'project': gcp_record.get('project.id', '')
            },
            'region': region,
            'tags': tags,
            'date': date
        })
    
    def normalize_azure(self, azure_record: Dict[str, Any]) -> UnifiedCostRecord:
        """Normalize Azure billing record to unified schema"""
        resource_id = azure_record.get('ResourceId', '')
        cost = float(azure_record.get('Cost', 0.0))
        service = azure_record.get('ServiceName', '')
        region = azure_record.get('ResourceLocation', '')
        date = azure_record.get('Date', '')
        
        service_category = self._categorize_service(service, 'azure')
        resource_type = self._determine_resource_type(service, azure_record.get('MeterCategory', ''), 'azure')
        
        tags = {
            'subscription': azure_record.get('SubscriptionId', '')
        }
        
        return UnifiedCostRecord({
            'resource_id': resource_id,
            'cloud_provider': 'azure',
            'service_category': service_category,
            'resource_type': resource_type,
            'cost_usd': cost,
            'usage_metrics': {
                'meter_category': azure_record.get('MeterCategory', ''),
                'resource_group': azure_record.get('ResourceGroup', '')
            },
            'region': region,
            'tags': tags,
            'date': date
        })
    
    def normalize_csv(self, csv_record: Dict[str, Any], cloud_provider: str) -> UnifiedCostRecord:
        """Normalize generic CSV record (for mock data)"""
        # Assume CSV has standard columns
        return UnifiedCostRecord({
            'resource_id': csv_record.get('resource_id', ''),
            'cloud_provider': cloud_provider,
            'service_category': csv_record.get('service_category', ''),
            'resource_type': csv_record.get('resource_type', ''),
            'cost_usd': float(csv_record.get('cost_usd', 0.0)),
            'usage_metrics': csv_record.get('usage_metrics', {}),
            'region': csv_record.get('region', ''),
            'tags': csv_record.get('tags', {}),
            'date': csv_record.get('date', '')
        })
    
    def _categorize_service(self, service: str, provider: str) -> str:
        """Categorize service into common categories"""
        service_lower = service.lower()
        
        # Compute services
        if any(x in service_lower for x in ['ec2', 'compute', 'vm', 'instance', 'virtual machine']):
            return 'compute'
        
        # Storage services
        if any(x in service_lower for x in ['s3', 'storage', 'blob', 'bucket']):
            return 'storage'
        
        # Database services
        if any(x in service_lower for x in ['rds', 'database', 'sql', 'dynamodb', 'cosmos']):
            return 'database'
        
        # Network services
        if any(x in service_lower for x in ['vpc', 'network', 'load balancer', 'nat', 'gateway']):
            return 'network'
        
        # Other
        return 'other'
    
    def _determine_resource_type(self, service: str, usage_type: str, provider: str) -> str:
        """Determine resource type from service and usage"""
        combined = f"{service} {usage_type}".lower()
        
        if any(x in combined for x in ['ec2', 'compute engine', 'virtual machine']):
            return 'vm'
        if any(x in combined for x in ['s3', 'storage', 'blob']):
            return 'storage'
        if any(x in combined for x in ['rds', 'sql', 'database']):
            return 'database'
        if any(x in combined for x in ['lambda', 'function', 'cloud function']):
            return 'function'
        
        return 'other'
    
    def normalize_batch(
        self,
        records: List[Dict[str, Any]],
        provider: str
    ) -> List[UnifiedCostRecord]:
        """Normalize a batch of records"""
        normalized = []
        for record in records:
            try:
                if provider == 'aws':
                    normalized.append(self.normalize_aws(record))
                elif provider == 'gcp':
                    normalized.append(self.normalize_gcp(record))
                elif provider == 'azure':
                    normalized.append(self.normalize_azure(record))
                else:
                    normalized.append(self.normalize_csv(record, provider))
            except Exception as e:
                logger.warning(f"⚠️ Failed to normalize record: {e}")
                continue
        
        return normalized

