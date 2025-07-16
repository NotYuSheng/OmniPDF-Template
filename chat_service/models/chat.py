from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """
    Request model for chat API endpoints.
    """

    message: str
    id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    collection_name: str = Field(default="default_collection", description="ChromaDB collection name")
    query_type: Optional[str] = Field(default="general", description="Query type: general, factual, analytical, summarization (auto-detected if not provided)")


class ChatResponse(BaseModel):
    """
    Response model for chat API
    """
    response: str
    relevant_chunks: List[Dict[str, Any]] = Field(default_factory=List, description="Additional metadata about the RAG process")
    metadata: Dict[str, Any]
