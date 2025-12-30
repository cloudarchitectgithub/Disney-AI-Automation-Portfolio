"""
RAG API endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5
    filter_metadata: Dict[str, Any] = None


class IngestRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]


@router.post("/search")
async def search_documents(request: Request, search: SearchRequest):
    """Search for relevant documents using RAG"""
    rag_service = request.state.rag_service
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        results = rag_service.search(
            query=search.query,
            n_results=search.n_results,
            filter_metadata=search.filter_metadata
        )
        return {
            "query": search.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_document(request: Request, ingest: IngestRequest):
    """Ingest a document into the RAG system"""
    rag_service = request.state.rag_service
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        chunks_ingested = rag_service.ingest_document(
            content=ingest.content,
            metadata=ingest.metadata
        )
        return {
            "status": "success",
            "chunks_ingested": chunks_ingested,
            "metadata": ingest.metadata
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats(request: Request):
    """Get RAG system statistics"""
    rag_service = request.state.rag_service
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        stats = rag_service.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_rag_collection(request: Request):
    """Clear all documents from RAG collection (use with caution)"""
    rag_service = request.state.rag_service
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        rag_service.clear_collection()
        return {"status": "cleared", "message": "All documents removed from collection"}
    except Exception as e:
        logger.error(f"Failed to clear collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

