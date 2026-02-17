"""
Document embedder for generating vector representations.
Uses sentence-transformers for semantic embeddings.
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentEmbedder:
    """Generate embeddings for text using sentence transformers."""
    
    def __init__(self):
        """Initialize the embedding model."""
        model_name = settings.embedding_model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            
        Returns:
            Array of embeddings (shape: [num_texts, embedding_dim])
        """
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.model.get_sentence_embedding_dimension()
