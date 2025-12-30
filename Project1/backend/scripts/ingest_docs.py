"""
Script to ingest documentation into RAG pipeline
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService
from loguru import logger


def load_text_file(file_path: Path) -> str:
    """Load text from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return ""


def ingest_directory(rag_service: RAGService, docs_dir: Path, doc_type: str):
    """Ingest all files from a directory"""
    if not docs_dir.exists():
        logger.warning(f"Directory not found: {docs_dir}")
        return
    
    files_ingested = 0
    for file_path in docs_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.py', '.yaml', '.yml', '.json']:
            try:
                content = load_text_file(file_path)
                if content:
                    metadata = {
                        "source": str(file_path.relative_to(docs_dir.parent)),
                        "type": doc_type,
                        "filename": file_path.name,
                        "extension": file_path.suffix
                    }
                    chunks = rag_service.ingest_document(content, metadata)
                    files_ingested += 1
                    logger.info(f"✅ Ingested {file_path.name} ({chunks} chunks)")
            except Exception as e:
                logger.error(f"❌ Failed to ingest {file_path}: {e}")
    
    logger.info(f"📚 Ingested {files_ingested} files from {doc_type}")


def main():
    """Main ingestion function"""
    logger.info("🚀 Starting document ingestion...")
    
    # Initialize RAG service
    try:
        rag_service = RAGService()
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG service: {e}")
        logger.error("Make sure ChromaDB is running: docker-compose up chromadb")
        return
    
    # Get docs directory (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    docs_dir = project_root / "docs"
    
    if not docs_dir.exists():
        logger.warning(f"📁 Creating docs directory: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample documentation
        create_sample_docs(docs_dir)
    
    # Ingest different types of documentation
    ingest_directory(rag_service, docs_dir / "kubernetes", "kubernetes")
    ingest_directory(rag_service, docs_dir / "docker", "docker")
    ingest_directory(rag_service, docs_dir / "aws", "aws")
    ingest_directory(rag_service, docs_dir / "troubleshooting", "troubleshooting")
    
    # Get final stats
    stats = rag_service.get_collection_stats()
    logger.info(f"✅ Ingestion complete! Total chunks: {stats.get('total_chunks', 0)}")


def create_sample_docs(docs_dir: Path):
    """Create sample documentation if none exists"""
    logger.info("📝 Creating sample documentation...")
    
    # Kubernetes docs
    k8s_dir = docs_dir / "kubernetes"
    k8s_dir.mkdir(parents=True, exist_ok=True)
    
    (k8s_dir / "pod-troubleshooting.md").write_text("""
# Kubernetes Pod Troubleshooting

## Common Issues

### Pod Crash Loop
- Check logs: `kubectl logs <pod-name>`
- Check events: `kubectl describe pod <pod-name>`
- Common causes: Out of memory, missing dependencies, configuration errors

### Pod Not Starting
- Verify image exists and is accessible
- Check resource limits and requests
- Review pod events for errors

### High Memory Usage
- Check memory limits in deployment
- Review application memory leaks
- Consider increasing memory requests
""")
    
    # Docker docs
    docker_dir = docs_dir / "docker"
    docker_dir.mkdir(parents=True, exist_ok=True)
    
    (docker_dir / "container-issues.md").write_text("""
# Docker Container Troubleshooting

## Container Won't Start
- Check Docker logs: `docker logs <container-id>`
- Verify image is correct: `docker images`
- Check port conflicts

## Container Crashes
- Review exit code: `docker inspect <container-id>`
- Check resource limits
- Review application logs inside container
""")
    
    # AWS docs
    aws_dir = docs_dir / "aws"
    aws_dir.mkdir(parents=True, exist_ok=True)
    
    (aws_dir / "ec2-troubleshooting.md").write_text("""
# AWS EC2 Troubleshooting

## Instance Not Accessible
- Check security groups allow SSH/RDP
- Verify instance is running
- Check network ACLs

## High CPU Usage
- Use CloudWatch metrics
- Check for runaway processes
- Consider instance type upgrade
""")
    
    # Troubleshooting guides
    troubleshooting_dir = docs_dir / "troubleshooting"
    troubleshooting_dir.mkdir(parents=True, exist_ok=True)
    
    (troubleshooting_dir / "database-connections.md").write_text("""
# Database Connection Issues

## Connection Pool Exhausted
- Increase pool size in configuration
- Check for connection leaks
- Review connection timeout settings

## Connection Timeouts
- Verify network connectivity
- Check database server status
- Review firewall rules
""")
    
    logger.info("✅ Sample documentation created")


if __name__ == "__main__":
    main()

