"""
RAG Service for document ingestion and retrieval
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from loguru import logger
import hashlib


class RAGService:
    """Service for RAG pipeline using ChromaDB"""
    
    def __init__(self):
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=self.chromadb_host,
            port=self.chromadb_port
        )
        
        # Get or create collection
        self.collection_name = "sre_documentation"
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "SRE infrastructure documentation"}
            )
            logger.info(f"✅ Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> int:
        """
        Ingest a document into the vector database
        
        Args:
            content: Document content
            metadata: Document metadata (source, type, etc.)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Number of chunks ingested
        """
        # Split document into chunks
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode([chunk["text"] for chunk in chunks]).tolist()
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(
                f"{metadata.get('source', 'unknown')}_{i}".encode()
            ).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
        
        # Add to collection
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"✅ Ingested {len(chunks)} chunks from {metadata.get('source', 'unknown')}")
            return len(chunks)
        except Exception as e:
            logger.error(f"❌ Failed to ingest document: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant document chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Build where clause for filtering
        where = filter_metadata if filter_metadata else None
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
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
            
            logger.debug(f"🔍 Found {len(formatted_results)} relevant documents for query: {query[:50]}...")
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {
                "collection_name": self.collection_name,
                "total_chunks": 0,
                "status": "error",
                "error": str(e)
            }
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, str]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunk dicts with text and position
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": end
            })
            
            start = end - chunk_overlap
        
        return chunks
    
    def clear_collection(self):
        """Clear all documents from collection (use with caution)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "SRE infrastructure documentation"}
            )
            logger.warning("🗑️ Collection cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear collection: {e}")

