from typing import List
from models.embed import ProcessingConfig

# Langchain components
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
# Sentence transformers
from sentence_transformers import SentenceTransformer

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
    

def chunker(config: ProcessingConfig):
    """Helper function to get tools based on current request's config"""
    emb_model = SentenceTransformerEmbeddings(config.embedding_model)
    sem_chunker = SemanticChunker(
        emb_model, 
        breakpoint_threshold_type=config.breakpoint_threshold_type, 
        breakpoint_threshold_amount=config.breakpoint_threshold_amount
    )
    
    return sem_chunker