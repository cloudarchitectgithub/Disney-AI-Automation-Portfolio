"""
Initialize data sources with mock billing data
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.data_sources import DataSourceRegistry, AWSDataSource, GCPDataSource, AzureDataSource
from loguru import logger


def main():
    """Initialize data sources"""
    logger.info("🚀 Initializing cost optimization data sources...")
    
    # Get data directory
    data_dir = Path(__file__).parent.parent.parent / "data" / "billing"
    
    # Initialize registry
    registry = DataSourceRegistry()
    
    # Register AWS
    aws_file = data_dir / "aws_billing.csv"
    if aws_file.exists():
        try:
            aws_source = AWSDataSource(str(aws_file))
            registry.register("aws", aws_source)
            logger.info(f"✅ Registered AWS data source: {len(aws_source.df)} records")
        except Exception as e:
            logger.error(f"❌ Failed to register AWS: {e}")
    else:
        logger.warning(f"⚠️ AWS billing file not found: {aws_file}")
    
    # Register GCP
    gcp_file = data_dir / "gcp_billing.csv"
    if gcp_file.exists():
        try:
            gcp_source = GCPDataSource(str(gcp_file))
            registry.register("gcp", gcp_source)
            logger.info(f"✅ Registered GCP data source: {len(gcp_source.df)} records")
        except Exception as e:
            logger.error(f"❌ Failed to register GCP: {e}")
    else:
        logger.warning(f"⚠️ GCP billing file not found: {gcp_file}")
    
    # Register Azure
    azure_file = data_dir / "azure_billing.csv"
    if azure_file.exists():
        try:
            azure_source = AzureDataSource(str(azure_file))
            registry.register("azure", azure_source)
            logger.info(f"✅ Registered Azure data source: {len(azure_source.df)} records")
        except Exception as e:
            logger.error(f"❌ Failed to register Azure: {e}")
    else:
        logger.warning(f"⚠️ Azure billing file not found: {azure_file}")
    
    logger.info(f"✅ Data source initialization complete! Registered {len(registry.sources)} sources")


if __name__ == "__main__":
    main()

