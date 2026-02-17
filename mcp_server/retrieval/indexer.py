"""
Document indexer for creating and managing FAISS vector index.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentIndexer:
    """Manage FAISS index for document retrieval."""
    
    def __init__(self, embedding_dim: int):
        """
        Initialize the indexer.
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.metadata = []
        logger.info(f"Initialized DocumentIndexer with embedding_dim={embedding_dim}")
    
    def create_index(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: Array of embeddings (shape: [num_docs, embedding_dim])
            metadata: List of metadata dicts for each embedding
        """
        logger.info(f"Creating FAISS index with {len(embeddings)} vectors")
        
        # Use L2 distance (Euclidean) which is more stable
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Add embeddings (convert to float32 for FAISS)
        embeddings_f32 = embeddings.astype('float32')
        self.index.add(embeddings_f32)
        
        self.metadata = metadata
        
        logger.info(f"FAISS index created with {self.index.ntotal} vectors")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (metadata, score) tuples
        """
        if self.index is None:
            logger.error("Index not initialized. Call create_index first.")
            return []
        
        # Reshape and convert to float32
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search (lower distance = more similar for L2)
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results - convert distance to similarity score
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata) and idx != -1:
                # Convert L2 distance to similarity score (inverse)
                similarity = 1.0 / (1.0 + distance)
                results.append((self.metadata[idx], float(similarity)))
        
        logger.info(f"Search returned {len(results)} results")
        return results
    
    def save(self, index_path: str, metadata_path: str):
        """
        Save index and metadata to disk.
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save metadata JSON
        """
        if self.index is None:
            logger.error("No index to save")
            return
        
        # Create directories if needed
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load(self, index_path: str, metadata_path: str):
        """
        Load index and metadata from disk.
        
        Args:
            index_path: Path to FAISS index
            metadata_path: Path to metadata JSON
        """
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        logger.info(f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        logger.info(f"Loaded {len(self.metadata)} metadata entries from {metadata_path}")
    
    @property
    def num_vectors(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal if self.index else 0
