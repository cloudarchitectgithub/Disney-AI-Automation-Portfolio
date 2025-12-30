"""
RAG Service for Security Documentation and Vulnerability Management
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from loguru import logger


class SecurityRAGService:
    """RAG service for security documentation and vulnerability management"""
    
    def __init__(self):
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=self.chromadb_host,
            port=self.chromadb_port
        )
        
        # Get or create collection for security docs
        self.collection_name = "security_documentation"
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Security documentation and vulnerability management"}
            )
            logger.info(f"✅ Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded for security RAG")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def search_vulnerability_info(
        self,
        cve_id: Optional[str] = None,
        vulnerability_type: Optional[str] = None,
        affected_component: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant vulnerability information
        
        Args:
            cve_id: CVE identifier
            vulnerability_type: Type of vulnerability
            affected_component: Affected component/service
            n_results: Number of results to return
            
        Returns:
            List of relevant security documentation
        """
        # Build semantic query
        query_parts = []
        if cve_id:
            query_parts.append(cve_id)
        if vulnerability_type:
            query_parts.append(vulnerability_type)
        if affected_component:
            query_parts.append(f"{affected_component} vulnerability")
        
        query = " ".join(query_parts) if query_parts else "vulnerability remediation"
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            logger.debug(f"🔍 Found {len(formatted_results)} security docs for query: {query[:50]}")
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ RAG search failed: {e}")
            return []
    
    def search_remediation_guidance(
        self,
        cve_id: str,
        component: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for remediation guidance for a specific CVE"""
        query = f"how to remediate {cve_id} {component} vulnerability patch update"
        
        return self.search_vulnerability_info(
            cve_id=cve_id,
            affected_component=component,
            n_results=n_results
        )
    
    def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> int:
        """Ingest security documentation"""
        # Simple chunking
        chunks = [content[i:i+500] for i in range(0, len(content), 450)]
        
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        import hashlib
        ids = [f"sec_doc_{i}_{hashlib.md5(content[:50].encode()).hexdigest()}" for i in range(len(chunks))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
        
        try:
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"✅ Ingested {len(chunks)} chunks of security documentation")
            return len(chunks)
        except Exception as e:
            logger.error(f"❌ Failed to ingest document: {e}")
            raise

