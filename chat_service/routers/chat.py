from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI, APIError
from typing import List, Dict, Any
from shared_utils.openai_client import get_openai_client
from shared_utils.chroma_client import get_chroma_client
import logging
import os
import numpy as np
from models.chat import ChatRequest, ChatResponse
from models.rag_config import QwenRAGConfig, QwenPromptTemplates, QwenRAGOptimizer

router = APIRouter(prefix="/chat")

logger = logging.getLogger(__name__)

# Initialize Qwen-2.5 RAG configuration
qwen_config = QwenRAGConfig()
prompt_templates = QwenPromptTemplates()
qwen_optimizer = QwenRAGOptimizer()

_OPENAI_MODEL_DEFAULT = "qwen2.5-0.5b-instruct"
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL", _OPENAI_MODEL_DEFAULT)
# CHROMADB_URL = os.getenv("CHROMADB_URL", "http://chromadb:5100")
CHROMADB_HOST = os.getenv("CHROMADB_HOST")
CHROMADB_PORT = os.getenv("CHROMADB_PORT")


def serialize_chroma_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ChromaDB query results to JSON-serializable format"""

    serialized = {}
    
    for key, value in results.items():
        if key == 'embeddings' and value is not None:
            # Convert numpy arrays to lists for embeddings
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], np.ndarray):
                    serialized[key] = [emb.tolist() for emb in value]
                elif isinstance(value[0], list):
                    # Already in list format
                    serialized[key] = value
                else:
                    serialized[key] = value
            else:
                serialized[key] = value
        elif key == 'distances' and value is not None:
            # Handle distances (might be numpy arrays)
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], np.ndarray):
                    serialized[key] = [dist.tolist() for dist in value]
                else:
                    serialized[key] = value
            else:
                serialized[key] = value
        else:
            # Handle other fields normally
            serialized[key] = value
    
    return serialized


def prepare_retrieval_results(results: Dict[str, Any]) -> List [Dict[str, Any]]:
    """Convert ChromaDB results to structured chunks for RAG"""
    chunks = []
    
    if not results or not results.get('documents'):
        return chunks
    
    # Get the first (and typically only) query results
    documents = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results.get('metadatas') else []
    distances = results['distances'][0] if results.get('distances') else []
    ids = results['ids'][0] if results.get('ids') else []
    
    for i, doc in enumerate(documents):
        chunk = {
            'content': doc,
            'chunk_id': ids[i] if i < len(ids) else f"chunk_{i}",
            'similarity_score': 1 - distances[i] if i < len(distances) else 0.0,  # Convert distance to similarity
            'metadata': metadatas[i] if i < len(metadatas) else {}
        }
        chunks.append(chunk)
    
    # Filter chunks by minimum similarity if configured
    if qwen_config.min_similarity_score > 0:
        chunks = [chunk for chunk in chunks if chunk['similarity_score'] >= qwen_config.min_similarity_score]
    
    return chunks


async def perform_rag_query(
    query: str, 
    collection_name: str, 
    top_k: int = 5,
    query_type: str = "general"
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Perform complete RAG query: retrieve relevant chunks and generate response
    """
    try:
        chroma_client = await get_chroma_client()
        # Step 1: Retrieve relevant chunks from ChromaDB
        collection = await chroma_client.get_collection(collection_name)
        
        results = await collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["distances", "documents", "metadatas", "embeddings"]
        )
        
        # Step 2: Process retrieval results
        chunks = prepare_retrieval_results(results)
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: {query}")
            return "I couldn't find any relevant information in the document collection to answer your question.", []
        
        # Step 3: Optimize chunks for Qwen-2.5
        optimized_chunks, context = qwen_optimizer.optimize_chunks_for_qwen(
            chunks, 
            max_context_length=qwen_config.max_context_length
        )

        logger.info(f"Relevant chunks: f{optimized_chunks}")
        
        logger.info(f"Using {len(optimized_chunks)} chunks for context (total length: {len(context)} chars)")
        
        logger.info(f"Query type: {query_type}")
        # Step 4: Auto-detect query type if not provided
        if query_type == "general":
            query_type = qwen_optimizer.detect_query_type(query)
            logger.info(f"Auto-detected query type: {query_type}")
        
        # Step 5: Prepare system and user prompts
        system_prompt = prompt_templates.get_system_prompt(query_type)
        user_prompt = prompt_templates.format_user_prompt(query, context, query_type)
        logger.info(f"System prompt: {system_prompt}")
        logger.info(f"User prompt: {user_prompt}")

        return user_prompt, optimized_chunks, system_prompt
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/", status_code=201, response_model=ChatResponse)
async def handle_chat(
    chat_request: ChatRequest,
    client: OpenAI = Depends(get_openai_client),
):
    """
    Handle incoming chat requests and return AI responses.
    """
    try:
        logger.info(chat_request.collection_name)

        # results = collection.query(
        #     query_texts=[chat_request.message],
        #     n_results=chat_request.top_k,
        #     include=["distances", "documents",  "metadatas", "embeddings"]
        # )

        # serialized_results = serialize_chroma_results(results)

        # Perform RAG query to get context and relevant chunks
        user_prompt, relevant_chunks, system_prompt = await perform_rag_query(
            query=chat_request.message,
            collection_name=chat_request.collection_name,
            top_k=chat_request.top_k,
            query_type=chat_request.query_type or "general"
        )
        
        # Prepare messages for Qwen-2.5
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": user_prompt
                # "content": chat_request.message
            }
        ]

        response = await run_in_threadpool(
            client.chat.completions.create,
            model=OPENAI_MODEL_NAME,
            messages=messages,
            **qwen_config.generation_params,
        )
    except APIError as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not response.choices:
        logger.error("No choices found in OpenAI response: %s", response)
        raise HTTPException(
            status_code=500,
            detail="AI service returned no choices or an unexpected response format.",
        )

    first_choice = response.choices[0]
    if not first_choice.message or first_choice.message.content is None:
        logger.error("Malformed choice in OpenAI response: %s", first_choice)
        raise HTTPException(
            status_code=500,
            detail="AI service response choice is malformed or lacks content.",
        )
    
    # Post-process the response
    raw_response = first_choice.message.content
    processed_response = qwen_optimizer.post_process_qwen_response(
        raw_response, 
        chat_request.message
    )
    
    # Prepare metadata for response
    metadata = {
        "query_type": chat_request.query_type or qwen_optimizer.detect_query_type(chat_request.message),
        "chunks_used": len(relevant_chunks),
        "total_context_length": len(user_prompt),
        "model_used": OPENAI_MODEL_NAME,
        "collection_name": chat_request.collection_name,
        "generation_params": qwen_config.generation_params
    }
    
    # Return structured response
    return ChatResponse(
        response=processed_response,
        relevant_chunks=relevant_chunks,
        metadata=metadata
    )

    # return {"response": first_choice.message.content}
