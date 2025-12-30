"""
Ingest cost optimization documentation into RAG pipeline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_cost_service import CostOptimizationRAGService
from loguru import logger


def create_sample_docs():
    """Create sample cost optimization documentation"""
    docs = []
    
    # AWS Cost Optimization
    docs.append({
        "content": """
AWS EC2 Instance Right-Sizing Best Practices:

1. Monitor CPU utilization for at least 7 days
2. If CPU < 40% consistently, consider downsizing
3. Use CloudWatch metrics: CPUUtilization, NetworkIn/Out
4. For variable workloads, consider burstable instances (t3 family)
5. Reserved Instances: Purchase for consistent workloads (>$100/month)
6. Savings Plans: Better flexibility than Reserved Instances
7. Spot Instances: Use for fault-tolerant, flexible workloads

Cost Savings Potential:
- Right-sizing: 20-40% savings
- Reserved Instances: 30-72% savings (1-year) or 50-75% (3-year)
- Spot Instances: Up to 90% savings

Migration Steps:
1. Create new instance with smaller type
2. Test workload performance
3. Migrate traffic gradually
4. Monitor for 48 hours
5. Terminate old instance
        """,
        "metadata": {
            "provider": "aws",
            "category": "compute",
            "type": "best_practices",
            "source": "aws_well_architected"
        }
    })
    
    # GCP Cost Optimization
    docs.append({
        "content": """
GCP Compute Engine Cost Optimization:

1. Use Committed Use Discounts (CUD) for predictable workloads
2. Right-size VMs based on actual usage metrics
3. Use Preemptible VMs for fault-tolerant workloads (80% savings)
4. Optimize disk types: Standard vs SSD vs Local SSD
5. Use Sustained Use Discounts (automatic, up to 30% off)
6. Regional pricing differences: us-central1 is cheapest

Best Practices:
- Monitor for 14 days before making changes
- Use Cloud Monitoring to track utilization
- Consider machine families: E2 (general), N1 (legacy), N2 (high-mem)
- Use custom machine types for exact resource needs

Cost Savings:
- Committed Use Discounts: 20-57% savings
- Preemptible VMs: Up to 80% savings
- Right-sizing: 20-35% savings
        """,
        "metadata": {
            "provider": "gcp",
            "category": "compute",
            "type": "best_practices",
            "source": "gcp_cost_optimization"
        }
    })
    
    # Azure Cost Optimization
    docs.append({
        "content": """
Azure Virtual Machine Cost Optimization:

1. Use Reserved Instances for consistent workloads
2. Right-size VMs: Monitor CPU, Memory, Disk I/O
3. Use Spot VMs for flexible workloads (up to 90% savings)
4. Choose appropriate VM series: B-series (burstable), D-series (general)
5. Optimize storage: Standard HDD vs Premium SSD
6. Use Azure Hybrid Benefit for Windows/Linux licenses

Optimization Process:
1. Analyze usage for 30 days
2. Identify underutilized resources
3. Test smaller VM sizes
4. Purchase Reserved Instances for predictable workloads
5. Migrate to Spot VMs where possible

Cost Savings:
- Reserved Instances: 30-72% savings
- Spot VMs: Up to 90% savings
- Right-sizing: 25-40% savings
        """,
        "metadata": {
            "provider": "azure",
            "category": "compute",
            "type": "best_practices",
            "source": "azure_cost_management"
        }
    })
    
    # Storage Optimization
    docs.append({
        "content": """
Multi-Cloud Storage Optimization:

AWS S3:
- Use lifecycle policies to move to cheaper tiers
- Glacier for archival (70% cheaper)
- Intelligent-Tiering for automatic optimization
- Delete unused buckets and objects

GCP Cloud Storage:
- Use storage classes: Standard, Nearline, Coldline, Archive
- Lifecycle policies for automatic transitions
- Delete unused buckets

Azure Blob Storage:
- Access tiers: Hot, Cool, Archive
- Lifecycle management policies
- Delete unused containers

Best Practices:
- Regular audits for unused storage
- Set up lifecycle policies
- Use appropriate storage tiers
- Monitor storage costs monthly
        """,
        "metadata": {
            "provider": "multi",
            "category": "storage",
            "type": "best_practices",
            "source": "storage_optimization"
        }
    })
    
    return docs


def main():
    """Ingest cost optimization documentation"""
    logger.info("🚀 Ingesting cost optimization documentation...")
    
    try:
        rag_service = CostOptimizationRAGService()
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG service: {e}")
        logger.error("Make sure ChromaDB is running: docker-compose up chromadb")
        return
    
    # Create sample docs
    docs = create_sample_docs()
    
    # Ingest each document
    total_chunks = 0
    for doc in docs:
        try:
            chunks = rag_service.ingest_document(
                content=doc["content"],
                metadata=doc["metadata"]
            )
            total_chunks += chunks
            logger.info(f"✅ Ingested: {doc['metadata'].get('source', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Failed to ingest document: {e}")
    
    logger.info(f"✅ Ingestion complete! Total chunks: {total_chunks}")
    logger.info("💡 Cost optimization RAG is ready to enhance recommendations!")


if __name__ == "__main__":
    main()

