# For data chunking and embedding

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
import uuid
import numpy as np
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
from chromadb.utils import embedding_functions

router = APIRouter()
logger = logging.getLogger(__name__)


class ProcessingConfig(BaseModel):
    chunk_size: int = Field(
        default=512, description="Target chunk size in characters")
    overlap: int = Field(
        default=50, description="Overlap between chunks in characters")
    # Default embedding model provided by Sentence Transformers
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformer model")
    # Better embedding model to be tested
    # embedding_model: str = Field(
    #     default="all-mpnet-base-v2", description="Sentence Transformer model")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1000, description="Maximum chunk size")
    store_in_chroma: bool = Field(
        default=True, description="Store embeddings in ChromaDB")
    collection_name: str = Field(
        default="my_documents", description="ChromaDB collection name")


class ChunkData(BaseModel):
    chunk_id: str
    source_file: Optional[str] = None
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


class DataRequest(BaseModel):
    doc_id: str
    text: str
    config: ProcessingConfig
    pages_info: List[Dict]
    

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


# Global instances
embedding_model = None
semantic_chunker = None
document_chunker = None
chroma_client = None

# Global instances
# embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# embedding_model = SentenceTransformer(DataRequest.config.embedding_model)
# embeddings_instance = SentenceTransformerEmbeddings(DataRequest.config.embedding_model)
# semantic_chunker = SemanticChunker(embeddings_instance, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)
# document_chunker = MarkdownTextSplitter(chunk_size = 40, chunk_overlap=0)
# chroma_client = chromadb.Client() # data stored in memory, not on disk


# Provision for retrieving PDF from local S3
# async def download_file_from_s3(key: str) -> Optional[bytes]:
#     """Download file from S3 and return content as bytes"""
#     try:
#         s3_client = boto3.client('s3')  # Configure with your credentials
#         response = s3_client.get_object(Bucket='your-bucket-name', Key=key)
#         return response['Body'].read()
#     except Exception as e:
#         logger.error(f"Failed to download file from S3: {e}")
#         return None


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


async def chunking(request:DataRequest) -> List[Dict[str, Any]]: # for Semantic
# def chunking() -> List[Dict[str, Any]]: # for Document-Based
    """Perform chunking / splitting of data via either Document-Based Chunking or Semantic Chunking"""
    global embedding_model, semantic_chunker, document_chunker

    print("Starting chunking process...")

    
    # METHOD 1: Semantic Chunking
    # Perform semantic chunking using LangChain's SemanticChunker
    # Reject by returning empty list if PDF document has no content
    try:
        # # Download PDF from S3
        # key = f"{request.doc_id}.pdf"
        # pdf_content = download_file_from_s3(key)
        # if not pdf_content:
        #     raise HTTPException(status_code=404, detail="PDF file not found")

        # # Extract text and page info from PDF
        # text, pages_info = extract_text_from_pdf(pdf_content)

        if not request.text.strip():
            raise HTTPException(status_code=400, detail="No text content found in PDF")

        # Create a Document object
        doc = Document(page_content=request.text.strip())
        # print("Text:", [doc])

        # Use semantic chunker
        chunks = semantic_chunker.split_documents([doc])
        # print("Chunks:", chunks)
        print("Number of chunks:", len(chunks))

        chunk_data = []
        current_pos = 0

        for i, chunk in enumerate(chunks):
            # First iteration: Extract first chunk of doc.page_content
            chunk_content = chunk.page_content
            print(f"Length of chunk {i+1}:", len(chunk_content.strip()))
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

            # Skip chunks that are too small or too large (if necessary)
            # if (len(chunk_content.strip()) < request.config.min_chunk_size) or (len(chunk_content.strip()) > request.config.max_chunk_size):
            #     current_pos = chunk_end
            #     print("Hi")
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

        print("Chunk data:", chunk_data)
        return chunk_data
    except Exception as e:
        logger.error(f"Semantic chunking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        # Fallback to simple chunking
        # return simple_chunk_text(text, config, pages_info)


async def embedding(chunk_data: List[Dict[str, Any]], config: ProcessingConfig):
    global embedding_model, chroma_client

    print("Starting embedding process...")
    await asyncio.sleep(1)

    try:
        try:
            print("Getting collection...")
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=config.embedding_model) # "all-MiniLM-L6-v2"
            collection = chroma_client.get_or_create_collection(name=config.collection_name, embedding_function=sentence_transformer_ef) # using default embedding function
            logger.info(f"Using embedding model: {config.embedding_model}")
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


@router.post("/embed")
async def pdf_embedder_service(request: DataRequest):
    global embedding_model, chroma_client, semantic_chunker
    # global document_chunker

    if embedding_model is None:
        logger.info("Loading embedding model...")
        # embedding_model = SentenceTransformer(request.config.embedding_model)
        embedding_model = SentenceTransformerEmbeddings(request.config.embedding_model)
        logger.info(request.config.embedding_model)

    # Semantic Chunking
    if semantic_chunker is None:
        logger.info("Initializing semantic chunker...")
        semantic_chunker = SemanticChunker(embedding_model, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)

    # Alternative: Document-Based Chunking
    # if document_chunker is None:
    #     logger.info("Initializing document-based chunker...")
    #     document_chunker = MarkdownTextSplitter(chunk_size = 40, chunk_overlap=0)

    if chroma_client is None:
        logger.info("Initializing ChromaDB client...")
        chroma_client = chromadb.Client() # data stored in memory, not on disk

    try:
        # Extracted data has to be chunked up first before being embedded and stored into ChromaDB
        chunk_data = await chunking(request=request)

        if not chunk_data:
            raise HTTPException(status_code=400, detail="No chunks were created from the input text") 
        
        embed_results = await embedding(chunk_data, request.config)
        
        return {
                "status": "success",
                "doc_id": request.doc_id,
                "chunks_created": len(chunk_data),
                "embedding_results": embed_results,
                "chunk_details": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["content"],
                        "content_length": len(chunk["content"]),
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"]
                    }
                    for chunk in chunk_data
                ]
            }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"PDF embedder service failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service failed: {str(e)}")
    

@router.get("/status/{doc_id}")
async def verify_document_embedding(doc_id: str, collection_name: str = "my_documents"):
    """Verify if a document's chunks have been successfully embedded"""
    global chroma_client
    
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


    # METHOD 2: Level 3 Document-Based Chunking
    # """Perform document-based chunking"""
    # Source: https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb
    # filepath = "test"

    # raw_pdf_elements = partition_pdf(
    #     filename=filepath,
    #     extract_images_in_pdf=True,
    #     infer_table_structure=True,
    #     chunking_strategy="by_title",
    #     max_characters=4000,
    #     new_after_n_chars=3800,
    #     combine_text_under_n_chars=2000,
    #     image_output_dir_path="static/pdfImages/",
    # )

    # markdown_text = """
    # # Fun in California

    # ## Driving

    # Try driving on the 1 down to San Diego

    # ### Food

    # Make sure to eat a burrito while you're there

    # ## Hiking

    # Go to Yosemite
    # """
    # print([markdown_text])

    # try:
    #     chunks = document_chunker.create_documents([markdown_text])
    #     print("Chunks:", chunks)
    #     print("Number of chunks:", len(chunks))

    #     # # Reject by returning empty list if PDF document has no content
    #     if not markdown_text.strip():
    #         raise HTTPException(status_code=400, detail="No text content found in PDF")
    
    #     chunk_data = []
    #     current_pos = 0

    #     for i, chunk in enumerate(chunks):
    #         # First iteration: Extract first chunk of doc.page_content
    #         chunk_content = chunk.page_content
    #         print(f"Length of chunk {i+1}:", len(chunk_content.strip()))
    #         # First iteration: Start from first chunk of doc.page_context
    #         chunk_start = markdown_text.find(chunk_content, current_pos)

    #         if chunk_start == -1:
    #             chunk_start = current_pos

    #         chunk_end = chunk_start + len(chunk_content)

    #         # # Find which page this chunk belongs to
    #         # page_number = None
    #         # for page_info in request.pages_info:
    #         #     if (chunk_start >= page_info['char_start'] and
    #         #             chunk_start < page_info['char_end']):
    #         #         page_number = page_info['page_number']
    #         #         break

    #         # Skip chunks that are too small or too large (if necessary)
    #         # if (len(chunk_content.strip()) < request.config.min_chunk_size) or (len(chunk_content.strip()) > request.config.max_chunk_size):
    #         #     current_pos = chunk_end
    #         #     print("Hi")
    #         #     continue

    #         # else:
    #         chunk_data.append({
    #         'chunk_id': str(uuid.uuid4()),
    #         'content': chunk_content.strip(),
    #         'start_char': chunk_start,
    #         'end_char': chunk_end,
    #         'page_number': None,
    #         'chunk_index': len(chunk_data),
    #         'metadata': chunk.metadata
    #         })

    #         current_pos = chunk_end

    #     print("Chunk data:", chunk_data)
    #     return chunk_data

    # except Exception as e:
    #     logger.error(f"Document-based chunking failed: {e}")


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


# Fallback code for data chunking and embedding
# DATA CHUNKING
# Method 2 (source: https://python.langchain.com/docs/how_to/semantic-chunker/)
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

# RAGGING (part of chat service)
# def rag(chunks, collection_name):
#     # Load all data chunks into ChromaDB
#     vectorstore = Chroma.from_documents(
#         documents=documents,
#         collection_name=collection_name,
#         # embedding=Embeddings.ollama.OllamaEmbeddings(model='nomic-embed-text'),
#         embedding=Embeddings,
#     )
#     # To check ChromaDB
#     retriever = vectorstore.as_retriever()

#     prompt_template = """Answer the question based only on the following context:
#     {context}
#     Question: {question}
#     """
#     prompt = ChatPromptTemplate.from_template(prompt_template)

#     chain = (
#         {"context": retriever, "question": RunnablePassthrough()}
#         | prompt
#         | local_llm
#         | StrOutputParser()
#     )

#     # User prompt
#     result = chain.invoke("What is the use of Text Splitting?")
#     print(result)
