# For data chunking and embedding

import chromadb
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import io
import boto3
import logging
from datetime import datetime
import uuid

# Langchain components
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOllama

# Sentence transformers
from sentence_transformers import SentenceTransformer

router = APIRouter()
logger = logging.getLogger(__name__)


class ProcessingConfig(BaseModel):
    chunk_size: int = Field(
        default=512, description="Target chunk size in characters")
    overlap: int = Field(
        default=50, description="Overlap between chunks in characters")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformer model")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1000, description="Maximum chunk size")
    store_in_chroma: bool = Field(
        default=True, description="Store embeddings in ChromaDB")
    collection_name: str = Field(
        default="documents", description="ChromaDB collection name")


class ChunkData(BaseModel):
    chunk_id: str
    content: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    embedding: List[float]
    metadata: Dict[str, Any] = {}


class ProcessingResult(BaseModel):
    doc_id: str
    filename: str
    total_chunks: int
    chunks: List[ChunkData]
    processing_time: float
    metadata: Dict[str, Any] = {}


class Request(BaseModel):
    doc_id: str
    config: ProcessingConfig
    pages_info: Optional[List[Dict]]


class TestRequest(BaseModel):
    text: str
    config: ProcessingConfig
    pages_info: Optional[List[Dict]]


# Method 1: Using Sentence Transformer for embedding of chunked data
# Custom Embeddings class for Sentence Transformers
class SentenceTransformerEmbeddings(Embeddings):
    """Custom embeddings class for Sentence Transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


# Global instances
embedding_model = None
semantic_chunker = None
chroma_client = None
embeddings_instance = None


async def initialize_models():
    """Initialize models and components"""
    global embedding_model, semantic_chunker, chroma_client, embeddings_instance

    if embedding_model is None:
        logger.info("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings_instance = SentenceTransformerEmbeddings('all-MiniLM-L6-v2')

    if semantic_chunker is None:
        logger.info("Initializing semantic chunker...")
        semantic_chunker = SemanticChunker(embeddings_instance)

    if chroma_client is None:
        logger.info("Initializing ChromaDB client...")
        chroma_client = chromadb.Client()


@router.post("/embed")
# def download_file_from_s3(key: str) -> Optional[bytes]:
#     """Download file from S3 and return content as bytes"""
#     try:
#         s3_client = boto3.client('s3')  # Configure with your credentials
#         response = s3_client.get_object(Bucket='your-bucket-name', Key=key)
#         return response['Body'].read()
#     except Exception as e:
#         logger.error(f"Failed to download file from S3: {e}")
#         return None
def chunking(request: TestRequest) -> List[Dict[str, Any]]:
    """Perform semantic chunking using LangChain's SemanticChunker"""
    try:
        # # Download PDF from S3
        # key = f"{request.doc_id}.pdf"
        # pdf_content = download_file_from_s3(key)
        # if not pdf_content:
        #     raise HTTPException(status_code=404, detail="PDF file not found")

        # # Extract text and page info from PDF
        # text, pages_info = extract_text_from_pdf(pdf_content)

        # if not text.strip():
        #     raise HTTPException(
        #         status_code=400, detail="No text content found in PDF")

        # Create a Document object
        doc = Document(page_content=request.text)

        # Use semantic chunker
        chunks = semantic_chunker.split_documents([doc])

        chunk_data = []
        current_pos = 0

        for i, chunk in enumerate(chunks):
            chunk_content = chunk.page_content
            chunk_start = request.text.find(chunk_content, current_pos)

            if chunk_start == -1:
                # Fallback: estimate position
                chunk_start = current_pos

            chunk_end = chunk_start + len(chunk_content)

            # Find which page this chunk belongs to
            page_number = None
            for page_info in request.pages_info:
                if (chunk_start >= page_info['char_start'] and
                        chunk_start < page_info['char_end']):
                    page_number = page_info['page_number']
                    break

            # Skip chunks that are too small
            if len(chunk_content.strip()) < request.config.min_chunk_size:
                current_pos = chunk_end
                continue

            chunk_data.append({
                'chunk_id': str(uuid.uuid4()),
                'content': chunk_content.strip(),
                'start_char': chunk_start,
                'end_char': chunk_end,
                'page_number': page_number,
                'chunk_index': len(chunk_data),
                'metadata': chunk.metadata
            })

            current_pos = chunk_end

        return chunk_data

    except Exception as e:
        logger.error(f"Semantic chunking failed: {e}")
        # Fallback to simple chunking
        # return simple_chunk_text(text, config, pages_info)

# Fallback to simple chunking
# def simple_chunk_text(text: str, config: ProcessingConfig, pages_info: List[Dict]) -> List[Dict[str, Any]]:
#     """Fallback simple chunking method"""
#     chunks = []
#     start = 0
#     chunk_index = 0

#     while start < len(text):
#         end = min(start + config.chunk_size, len(text))

#         # Try to break at sentence boundaries
#         if end < len(text):
#             for i in range(end, max(start + config.min_chunk_size, end - 100), -1):
#                 if text[i] in '.!?':
#                     end = i + 1
#                     break

#         chunk_text = text[start:end].strip()

#         if len(chunk_text) >= config.min_chunk_size:
#             # Find page number
#             page_number = None
#             for page_info in pages_info:
#                 if (start >= page_info['char_start'] and
#                     start < page_info['char_end']):
#                     page_number = page_info['page_number']
#                     break

#             chunks.append({
#                 'chunk_id': str(uuid.uuid4()),
#                 'content': chunk_text,
#                 'start_char': start,
#                 'end_char': end,
#                 'page_number': page_number,
#                 'chunk_index': chunk_index,
#                 'metadata': {}
#             })
#             chunk_index += 1

#         start = end - config.overlap
#         if start >= end:
#             start = end

#     return chunks


# def embedding(doc_id: int):
#     # Work-in-progress
#     return {"doc_id": {doc_id}}


# Fallback code for data chunking and embedding
# DATA CHUNKING
# Method 1 (from OmniPDF sample)
# Split the filtered text into chunks for better translation
# "standard_deviation", "interquartile"
# text_splitter = SemanticChunker(
#     Embeddings(), breakpoint_threshold_type="percentile")
# text_chunks = text_splitter.split_text(filtered_text)

# translated_text = ""
# for chunk_idx, text_chunk in enumerate(text_chunks):
#     translated_text_chunk = translate_text(text_chunk, CLIENT)
#     translated_text += translated_text_chunk

#     # Add text documents
#     documents.append(
#         {
#             "page_content": translated_text_chunk,
#             "metadata": {
#                 "text_chunk_key": f"text_chunk_{page_number + 1}_{chunk_idx + 1}",
#                 "type": "text",
#             },
#         }
#     )

# Method 2 (online source)
# Percentile - all differences between sentences are calculated, and then any difference greater than the X percentile is split
# text_splitter = SemanticChunker(Embeddings())
# text_splitter = SemanticChunker(
#     # "standard_deviation", "interquartile"
#     Embeddings(), breakpoint_threshold_type="percentile"
# )
# documents = text_splitter.create_documents([text])
# print(documents)

# DATA EMBEDDING (from OmniPDF sample)
# class NomicEmbeddings(Embeddings):
#     def __init__(self, model: str):
#         self.model = model
#         self.client = CLIENT

#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         """Embed search docs."""
#         return [
#             self.client.embeddings.create(input=[_], model=self.model).data[0].embedding
#             for _ in texts
#         ]

#     def embed_query(self, text: str) -> List[float]:
#         """Embed query text."""
#         return self.embed_documents([text])[0]


# class RAGHelper:
#     """Helper for Retrieval Augmented Generation (RAG)."""

#     def __init__(self):
#         self.message = "Hello World, I am a helper class for RAG."
#         embedding_function = NomicEmbeddings(
#             model="text-embedding-nomic-embed-text-v1.5-embedding"
#         )
#         chromadb.api.client.SharedSystemClient.clear_system_cache()  # Clear cache to handle "could not connect to tenant default_tenant" error
#         self.vectorstore = Chroma("all_documents", embedding_function)

#     def get(self) -> str:
#         return self.message

#     def get_all_documents(self) -> List[Document]:
#         if self.vectorstore:
#             return self.vectorstore.get()

#     def add_docs_to_chromadb(self, docs: list[dict]) -> None:
#         if self.vectorstore:
#             self.vectorstore.reset_collection()

#         # Convert to Document type
#         docs = [
#             Document(page_content=doc["page_content"], metadata=doc["metadata"])
#             for doc in docs
#         ]
#         return self.vectorstore.add_documents(docs)

#     def retrieve_relevant_docs(self, user_query: str, top_k: int) -> list[Document]:
#         """Retrieve relevant documents from vector database based on user
#         query.

#         Parameters
#         ----------
#         user_query : str
#             The user query or prompt in "Chat with Omni".

#         Returns
#         -------
#         pd.DataFrame
#             The DataFrame that contains the documents with relevance score.
#         """

#         # Read vector database as DataFrame
#         results = self.vectorstore.similarity_search(
#             user_query,
#             k=top_k,
#         )

#         # Retrieve relevant docs
#         return results
