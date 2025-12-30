"""
Generate mock cloud billing data for demo purposes
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_aws_billing(output_path: str, num_records: int = 500):
    """Generate mock AWS billing data for Disney-like services"""
    records = []
    
    # Disney-specific services: E-commerce, streaming, parks, cruise
    services = ['AmazonEC2', 'AmazonS3', 'AmazonRDS', 'AmazonVPC', 'AmazonCloudWatch', 
                'AmazonElastiCache', 'AmazonRoute53', 'AmazonCloudFront', 'AWSLambda']
    regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
    instance_types = ['t3.medium', 't3.large', 'm5.xlarge', 'm5.2xlarge', 'c5.4xlarge', 'r5.2xlarge']
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_records):
        date = start_date + timedelta(days=random.randint(0, 29))
        service = random.choice(services)
        region = random.choice(regions)
        
        if service == 'AmazonEC2':
            instance_type = random.choice(instance_types)
            # Realistic EC2 costs: $50-$2000/month per instance
            cost = random.uniform(50.0, 2000.0)
            resource_id = f"i-{random.randint(100000000000, 999999999999)}"
        elif service == 'AmazonS3':
            # S3 storage costs: $5-$500/month
            cost = random.uniform(5.0, 500.0)
            resource_id = f"s3-bucket-{random.randint(1000, 9999)}"
            instance_type = ''
        elif service == 'AmazonRDS':
            # RDS costs: $100-$1500/month
            cost = random.uniform(100.0, 1500.0)
            resource_id = f"db-{random.randint(1000, 9999)}"
            instance_type = 'db.t3.medium'
        else:
            cost = random.uniform(10.0, 300.0)
            resource_id = f"resource-{random.randint(1000, 9999)}"
            instance_type = ''
        
        records.append({
            'lineItem/UsageStartDate': date.strftime('%Y-%m-%d'),
            'lineItem/ProductCode': service,
            'lineItem/ResourceId': resource_id,
            'lineItem/UnblendedCost': round(cost, 4),
            'lineItem/UsageType': f'{service.lower()}-usage',
            'lineItem/Operation': 'RunInstances' if service == 'AmazonEC2' else 'Usage',
            'lineItem/AvailabilityZone': f'{region}a',
            'product/InstanceType': instance_type,
            'resourceTags/User:Project': random.choice(['disney-parks', 'disney-cruise', 'disney-store', 'disney-plus', 'disney-vacation-club', ''])
        })
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"✅ Generated AWS billing data: {output_path} ({num_records} records)")


def generate_gcp_billing(output_path: str, num_records: int = 500):
    """Generate mock GCP billing data for Disney-like services"""
    records = []
    
    # Disney-specific: Analytics, ML, BigQuery for guest data
    services = ['Compute Engine', 'Cloud Storage', 'Cloud SQL', 'Cloud Load Balancing',
                'BigQuery', 'Cloud Functions', 'Cloud Pub/Sub', 'Cloud CDN']
    regions = ['us-central1', 'us-east1', 'europe-west1', 'asia-southeast1']
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_records):
        date = start_date + timedelta(days=random.randint(0, 29))
        service = random.choice(services)
        region = random.choice(regions)
        
        if service == 'Compute Engine':
            # GCP Compute: $40-$1800/month per instance
            cost = random.uniform(40.0, 1800.0)
        elif service == 'Cloud Storage':
            # GCP Storage: $5-$400/month
            cost = random.uniform(5.0, 400.0)
        elif service == 'Cloud SQL':
            # GCP SQL: $80-$1200/month
            cost = random.uniform(80.0, 1200.0)
        else:
            cost = random.uniform(10.0, 250.0)
        
        records.append({
            'usage_start_time': date.strftime('%Y-%m-%dT%H:%M:%S'),
            'service.description': service,
            'resource.name': f'projects/disney-{random.randint(100, 999)}/{service.lower().replace(" ", "-")}-{random.randint(1000, 9999)}',
            'cost': round(cost, 4),
            'sku.description': f'{service} usage',
            'location.region': region,
            'project.id': random.choice(['disney-parks-prod', 'disney-cruise-dev', 'disney-store-staging', 'disney-plus-prod', 'disney-analytics'])
        })
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"✅ Generated GCP billing data: {output_path} ({num_records} records)")


def generate_azure_billing(output_path: str, num_records: int = 500):
    """Generate mock Azure billing data for Disney-like services"""
    records = []
    
    # Disney-specific: Enterprise apps, Office 365 integration, hybrid cloud
    services = ['Virtual Machines', 'Storage', 'SQL Database', 'Load Balancer',
                'Azure Functions', 'Azure CDN', 'Azure Redis Cache', 'Azure Cosmos DB']
    regions = ['East US', 'West US', 'West Europe', 'Southeast Asia']
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_records):
        date = start_date + timedelta(days=random.randint(0, 29))
        service = random.choice(services)
        region = random.choice(regions)
        
        if service == 'Virtual Machines':
            # Azure VMs: $45-$1600/month per VM
            cost = random.uniform(45.0, 1600.0)
        elif service == 'Storage':
            # Azure Storage: $5-$350/month
            cost = random.uniform(5.0, 350.0)
        elif service == 'SQL Database':
            # Azure SQL: $90-$1100/month
            cost = random.uniform(90.0, 1100.0)
        else:
            cost = random.uniform(10.0, 200.0)
        
        records.append({
            'Date': date.strftime('%Y-%m-%d'),
            'ServiceName': service,
            'ResourceId': f'/subscriptions/sub-{random.randint(100, 999)}/resourceGroups/rg-{random.randint(1, 10)}/providers/Microsoft.Compute/{service.lower().replace(" ", "")}/{random.randint(1000, 9999)}',
            'Cost': round(cost, 4),
            'MeterCategory': f'{service} Meter',
            'ResourceLocation': region,
            'SubscriptionId': f'sub-{random.randint(100, 999)}',
            'ResourceGroup': random.choice(['disney-parks-rg', 'disney-cruise-rg', 'disney-store-rg', 'disney-plus-rg', 'disney-enterprise-rg'])
        })
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"✅ Generated Azure billing data: {output_path} ({num_records} records)")


def main():
    """Generate all mock billing data"""
    data_dir = Path(__file__).parent.parent.parent / "data" / "billing"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Generating mock cloud billing data...")
    print("📊 Targeting realistic costs that scale to $9M FY26 savings potential...")
    
    # Generate more records for realistic monthly costs
    # With ~800 records per provider at $50-$2000 each, we get ~$500K-$1.6M per provider
    # Total: ~$1.5M-$4.8M/month = realistic multi-cloud spend
    # 30% savings = ~$450K-$1.4M/month = $5.4M-$17M/year (includes $9M target)
    generate_aws_billing(str(data_dir / "aws_billing.csv"), 800)
    generate_gcp_billing(str(data_dir / "gcp_billing.csv"), 700)
    generate_azure_billing(str(data_dir / "azure_billing.csv"), 500)
    
    print("✅ All mock billing data generated!")
    print("💡 Note: These costs are designed to demonstrate $9M+ annual savings potential")


if __name__ == "__main__":
    main()

