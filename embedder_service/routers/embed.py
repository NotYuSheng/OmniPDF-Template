# For data chunking and embedding

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import uuid
# import numpy as np
from models.embed import ProcessingConfig, DataRequest
# from unstructured.partition.pdf import partition_pdf
# from unstructured.staging.base import elements_to_json

# Langchain components
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
# from langchain.text_splitter import MarkdownTextSplitter
from langchain_core.documents import Document

# Sentence transformers
from sentence_transformers import SentenceTransformer

# ChromaDB
import chromadb
# from chromadb.utils import embedding_functions

router = APIRouter()
logger = logging.getLogger(__name__)


# Method 1: Using Sentence Transformer for embedding of chunked data
# Custom Embeddings class for Sentence Transformers
class SentenceTransformerEmbeddings(Embeddings):
    """Custom embeddings class for Sentence Transformers"""

    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


# 
async def initialize_tools(config: ProcessingConfig):
    """Helper function to get tools based on current request's config"""
    emb_model = SentenceTransformerEmbeddings(config.embedding_model)
    sem_chunker = SemanticChunker(emb_model, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)
    chroma_client = chromadb.Client() # data stored in memory, not on disk
    return sem_chunker, chroma_client


async def chunking_and_embedding(request:DataRequest, chunker) -> List[Dict[str, Any]]:
    """Perform chunking / splitting and embedding of data via Semantic Chunking using LangChain's SemanticChunker,
    and reject by raising HTTP Error 400 if PDF document has no content"""

    logger.info("Starting chunking process...")

    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="No text content found in PDF")

        # Create a Document object
        doc = Document(page_content=request.text.strip())

        # Use semantic chunker
        chunks = chunker.split_documents([doc])
        logger.info(f"Number of chunks: {len(chunks)}")

        chunk_data = []
        current_pos = 0

        for i, chunk in enumerate(chunks):
            # First iteration: Extract first chunk of doc.page_content
            chunk_content = chunk.page_content
            logger.info(f"Length of chunk {i+1}:", len(chunk_content.strip()))
            # First iteration: Start from first chunk of doc.page_context
            chunk_start = request.text.find(chunk_content, current_pos)

            if chunk_start == -1:
                chunk_start = current_pos

            chunk_end = chunk_start + len(chunk_content)

            # # Find which page this chunk belongs to
            # page_number = None
            # for page_info in request.pages_info:
            #     if (chunk_start >= page_info['char_start'] and
            #             chunk_start < page_info['char_end']):
            #         page_number = page_info['page_number']
            #         break

            # Include doc_id in metadata
            chunk_metadata = chunk.metadata.copy()
            chunk_metadata["doc_id"] = request.doc_id
            # "metadata": {
            #     "text_chunk_key": f"text_chunk_{page_number + 1}_{chunk_idx + 1}",
            #     "type": "text",
            # },

            # Skip chunks that are too small or too large (if necessary)
            # if (len(chunk_content.strip()) < request.config.min_chunk_size) or (len(chunk_content.strip()) > request.config.max_chunk_size):
            #     current_pos = chunk_end
            #     continue

            # else:
            chunk_data.append({
            'chunk_id': str(uuid.uuid4()),
            'content': chunk_content.strip(),
            'start_char': chunk_start,
            'end_char': chunk_end,
            'page_number': None,
            'chunk_index': len(chunk_data),
            'metadata': chunk_metadata # {"doc_id": request.doc_id}
            })

            current_pos = chunk_end

        logger.info("Chunk data:", chunk_data)
        return chunk_data
    except Exception as e:
        logger.error(f"Semantic chunking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


async def vectorize_chromadb(chunk_data: List[Dict[str, Any]], config: ProcessingConfig, chroma_client):
    """Store vector embeddings of data chunks extracted from PDF document into ChromaDB"""

    logger.info("Starting vectorization process...")

    try:
        try:
            logger.info("Getting collection...")
            collection = chroma_client.get_or_create_collection(name=config.collection_name)
            logger.info(f"Using existing collection: {config.collection_name}")
        except Exception as e:
            logger.error(f"Collection retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=f"Collection retrieval failed: {str(e)}")
        
        for chunk in chunk_data:
            collection.add(
                ids=[chunk['chunk_id']],
                documents=[chunk["content"]],
                metadatas=[chunk["metadata"]]
            )
            logger.info(f"Added chunk {chunk['chunk_id']} to collection")

        return {
            "collection_name": config.collection_name,
            "total_chunks_added": len(chunk_data)
        }

        # Part of the Chat Service
        # results = collection.query(
        #     query_texts=["They keep moving."],
        #     n_results=min(2, len(chunk_data)),
        #     include=["distances", "documents",  "metadatas", "embeddings"]
        # )

        # serialized_results = serialize_chroma_results(results)

        # return {
        #     "collection_name": config.collection_name,
        #     "total_chunks_added": len(chunk_data),
        #     "sample_query_results": serialized_results
        # }

    except Exception as e:
        logger.error(f"Embedding process failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


# def serialize_chroma_results(results: Dict[str, Any]) -> Dict[str, Any]:
#     """Convert ChromaDB query results to JSON-serializable format"""

#     serialized = {}
    
#     for key, value in results.items():
#         if key == 'embeddings' and value is not None:
#             # Convert numpy arrays to lists for embeddings
#             if isinstance(value, list) and len(value) > 0:
#                 if isinstance(value[0], np.ndarray):
#                     serialized[key] = [emb.tolist() for emb in value]
#                 elif isinstance(value[0], list):
#                     # Already in list format
#                     serialized[key] = value
#                 else:
#                     serialized[key] = value
#             else:
#                 serialized[key] = value
#         elif key == 'distances' and value is not None:
#             # Handle distances (might be numpy arrays)
#             if isinstance(value, list) and len(value) > 0:
#                 if isinstance(value[0], np.ndarray):
#                     serialized[key] = [dist.tolist() for dist in value]
#                 else:
#                     serialized[key] = value
#             else:
#                 serialized[key] = value
#         else:
#             # Handle other fields normally
#             serialized[key] = value
    
#     return serialized


@router.post("/embed")
async def pdf_embedder_service(request: DataRequest):
    "Chunk up and embed data from PDF document into ChromaDB"

    semantic_chunker, chroma_client = await initialize_tools(request.config)
    
    try:
        # Extracted data has to be chunked up and embedded first before being stored into ChromaDB
        chunk_embeddings = await chunking_and_embedding(request, semantic_chunker)

        if not chunk_embeddings:
            raise HTTPException(status_code=400, detail="No chunks were created from the input text") 
        
        embed_results = await vectorize_chromadb(chunk_embeddings, request.config, chroma_client)
        
        return {
                "status": "success",
                "doc_id": request.doc_id,
                "chunks_created": len(chunk_embeddings),
                "embedding_results": embed_results,
                "chunk_details": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["content"],
                        "content_length": len(chunk["content"]),
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"]
                    }
                    for chunk in chunk_embeddings
                ]
            }
    except Exception as e:
        logger.error(f"PDF embedder service failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service failed: {str(e)}")
    

@router.get("/status/{doc_id}")
async def verify_document_embedding(doc_id: str, collection_name: str = "my_documents"):
    """Verify if a document's data chunks have been successfully embedded into ChromaDB"""

    _, chroma_client = initialize_tools(config=ProcessingConfig)
    
    try:
        if chroma_client is None:
            raise HTTPException(status_code=500, detail="ChromaDB client not initialized")
        
        collection = chroma_client.get_collection(name=collection_name)
        
        # Query by doc_id in metadata
        results = collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas", "embeddings"]
        )
        
        if not results['ids']:
            return {
                "doc_id": doc_id,
                "status": "not_found",
                "chunks_found": 0,
                "message": f"No chunks found for document {doc_id}"
            }
        
        return {
            "doc_id": doc_id,
            "status": "found",
            "chunks_found": len(results['ids']),
            "chunk_ids": results['ids'],
            "chunks_have_embeddings": len(results.get('embeddings', [])) > 0,
            "sample_content": results['documents']if results['documents'] else None
        }
        
    except Exception as e:
        logger.error(f"Document verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
