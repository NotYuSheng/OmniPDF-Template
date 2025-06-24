# For data chunking and embedding

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import uuid
from models.embed import ProcessingConfig, DataRequest
from models.helper import get_chunking_model, get_embedding_model
# from unstructured.partition.pdf import partition_pdf
# from unstructured.staging.base import elements_to_json
# import numpy as np

# from langchain.text_splitter import MarkdownTextSplitter
from langchain_core.documents import Document

# ChromaDB
import chromadb
# from chromadb.utils import embedding_functions

router = APIRouter()
logger = logging.getLogger(__name__)


# In-memory ChromaDB instance (data stored in memory)
chroma_client = chromadb.EphemeralClient()
# Persistent ChromaDB instance (data stored on disk)
# chroma_client = chromadb.HttpClient(host="localhost", port=5100)


async def data_chunking(request:DataRequest, chunker) -> List[Dict[str, Any]]:
    """Perform chunking / splitting of data via Semantic Chunking using LangChain's SemanticChunker,
    and reject by returning empty list if PDF document has no content"""

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
            logger.info(f"Length of chunk {i+1}: {len(chunk_content.strip())}")
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

            # Find page number for the chunk
            # page_number = None
            # for page_info in request.pages_info:
            #     # Ensure keys exist to avoid KeyErrors
            #     page_start = page_info.get('start_char')
            #     page_end = page_info.get('end_char')
            #     if page_start is not None and page_end is not None:
            #         if page_start <= chunk_start < page_end:
            #             page_number = page_info.get('page')
            #             break

            # Include doc_id in metadata
            chunk_metadata = chunk.metadata.copy()
            chunk_metadata["doc_id"] = request.doc_id
            
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
            'metadata': chunk_metadata
            })

            current_pos = chunk_end

        logger.info(chunk_data)
        return chunk_data
    except Exception as e:
        logger.error(f"Semantic chunking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


async def vectorize_chromadb(chunk_data: List[Dict[str, Any]], config: ProcessingConfig, emb_model):
    """Embed data chunks of PDF document into ChromaDB"""

    logger.info("Starting embedding process...")

    try:
        try:
            logger.info("Getting collection...")
            collection = chroma_client.get_or_create_collection(name=config.collection_name, embedding_function=emb_model)
            logger.info(f"Using existing collection: {config.collection_name}")
        except Exception as e:
            logger.error(f"Collection retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=f"Collection retrieval failed: {str(e)}")
        
        # for chunk in chunk_data:
        #     collection.add(
        #         ids=[chunk['chunk_id']],
        #         documents=[chunk["content"]],
        #         metadatas=[chunk["metadata"]]
        #     )
        #     logger.info(f"Added chunk {chunk['chunk_id']} to collection")

        ids = [chunk['chunk_id'] for chunk in chunk_data]
        documents = [chunk['content'] for chunk in chunk_data]
        metadatas = [chunk['metadata'] for chunk in chunk_data]

        if not ids:
            logger.warning("No chunks to add to the collection.")
            return
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} chunks to collection '{config.collection_name}'")

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

    semantic_chunker = get_chunking_model(request.config)
    embedding_model = get_embedding_model(request.config.embedding_model)
    
    try:
        # Extracted data has to be chunked up first before being embedded and stored into ChromaDB
        chunk_data = await data_chunking(request, semantic_chunker)

        if not chunk_data:
            raise HTTPException(status_code=400, detail="No chunks were created from the input text") 
        
        embed_results = await vectorize_chromadb(chunk_data, request.config, embedding_model)
        
        return {
                "status": "success",
                "doc_id": request.doc_id,
                "chunks_created": len(chunk_data),
                "embedding_results": embed_results,
                "chunk_details": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                        "content_length": len(chunk["content"]),
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"]
                    }
                    for chunk in chunk_data
                ]
            }
    except Exception as e:
        logger.error(f"PDF embedder service failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service failed: {str(e)}")
    

@router.get("/status/{doc_id}")
async def verify_document_embedding(doc_id: str, collection_name: str = "my_documents"):
    """Verify if a document's data chunks have been successfully embedded into ChromaDB"""
    
    try:
        if chroma_client is None:
            raise HTTPException(status_code=500, detail="ChromaDB client not initialized")
        
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
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
