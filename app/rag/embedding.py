from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logger import logger

class EmbeddingEngine:
    def __init__(self):
        # Config se model name uthayenge, hardcoded kuch bhi nahi
        self.model_name = settings.EMBEDDING_MODEL
        logger.info(f"Initializing Embedding Engine with model: {self.model_name}")
        
        try:
            # SentenceTransformer automatically handle karega local caching aur loading
            self.model = SentenceTransformer(self.model_name)
            
            # FIXED: .success ki jagah standard .info use kiya taaki custom logger crash na kare
            logger.info(f"Embedding model '{self.model_name}' loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{self.model_name}': {str(e)}")
            raise RuntimeError(f"Embedding initialization error: {str(e)}")

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Input text strings ki list leta hai aur unke dense vector embeddings (NumPy Array) return karta hai.
        """
        if not texts:
            return np.array([])
            
        try:
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            # convert_to_numpy=True ensures compatibility with ChromaDB/Vector store injection
            embeddings = self.model.encode(
                texts, 
                show_progress_bar=False, 
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    def get_query_embedding(self, query: str) -> List[float]:
        """
        Single search query ko single vector list me convert karta hai (Similarity search ke liye).
        """
        try:
            embedding = self.model.encode(query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise RuntimeError(f"Query embedding failed: {str(e)}")