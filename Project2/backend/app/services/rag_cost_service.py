"""
RAG Service for Cost Optimization - Enhances recommendations with best practices
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from loguru import logger


class CostOptimizationRAGService:
    """RAG service specifically for cost optimization knowledge"""
    
    def __init__(self):
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=self.chromadb_host,
            port=self.chromadb_port
        )
        
        # Get or create collection for cost optimization docs
        self.collection_name = "cost_optimization_docs"
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Cost optimization best practices and documentation"}
            )
            logger.info(f"✅ Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded for cost optimization RAG")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def search_optimization_strategies(
        self,
        opportunity_type: str,
        cloud_provider: str,
        resource_type: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant optimization strategies
        
        Args:
            opportunity_type: Type of opportunity (idle_resource, over_provisioned, etc.)
            cloud_provider: Cloud provider (aws, gcp, azure)
            resource_type: Resource type (vm, storage, database, etc.)
            n_results: Number of results to return
            
        Returns:
            List of relevant optimization strategies
        """
        # Build semantic query
        query = f"how to optimize {opportunity_type} {resource_type} {cloud_provider}"
        
        # Filter by provider if possible
        filter_metadata = {"provider": cloud_provider} if cloud_provider else None
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
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
            
            logger.debug(f"🔍 Found {len(formatted_results)} optimization strategies for {opportunity_type}")
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ RAG search failed: {e}")
            return []
    
    def search_best_practices(
        self,
        query: str,
        provider: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for general best practices"""
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        filter_metadata = {"provider": provider} if provider else None
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            formatted_results = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"❌ Best practices search failed: {e}")
            return []
    
    def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> int:
        """Ingest cost optimization documentation"""
        # Simple chunking (can be enhanced)
        chunks = [content[i:i+500] for i in range(0, len(content), 450)]
        
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        ids = [f"doc_{i}_{hash(content[:50])}" for i in range(len(chunks))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
        
        try:
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"✅ Ingested {len(chunks)} chunks of cost optimization docs")
            return len(chunks)
        except Exception as e:
            logger.error(f"❌ Failed to ingest document: {e}")
            raise

