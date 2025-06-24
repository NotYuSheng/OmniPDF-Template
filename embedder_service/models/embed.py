from pydantic import BaseModel, Field
from typing import List, Dict
import os

_EMBEDDING_MODEL_DEFAULT = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", _EMBEDDING_MODEL_DEFAULT)
print(EMBEDDING_MODEL_NAME)


class ProcessingConfig(BaseModel):
    """Config model for embed API endpoint."""

    chunk_size: int = Field(
        default=512, description="Target chunk size in characters")
    overlap: int = Field(
        default=50, description="Overlap between chunks in characters")
    # Default embedding model provided by Sentence Transformers
    embedding_model: str = Field(
        default=EMBEDDING_MODEL_NAME, description="Sentence Transformer model")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1000, description="Maximum chunk size")
    store_in_chroma: bool = Field(
        default=True, description="Store embeddings in ChromaDB")
    collection_name: str = Field(
        default="my_documents", description="ChromaDB collection name")


class DataRequest(BaseModel):
    """Request model for embed API endpoint."""
    
    doc_id: str
    text: str # to be received in JSON format from PDF Extraction Service
    config: ProcessingConfig
    pages_info: List[Dict]
