"""
Document retriever combining embedding and indexing for semantic search.
"""

from typing import List, Dict, Any
from pathlib import Path

from mcp_server.retrieval.embedder import DocumentEmbedder
from mcp_server.retrieval.indexer import DocumentIndexer
from config.settings import settings
from utils.logger import get_logger
from utils.monitoring import PerformanceMonitor

logger = get_logger(__name__)


class DocumentRetriever:
    """High-level retrieval interface combining embedding and indexing."""
    
    def __init__(self):
        """Initialize retriever with embedder and indexer."""
        logger.info("Initializing DocumentRetriever")
        self.embedder = DocumentEmbedder()
        self.indexer = DocumentIndexer(self.embedder.embedding_dimension)
        self._load_index()
    
    def _load_index(self):
        """Load existing index or log warning if not found."""
        index_path = settings.get('knowledge_base.embeddings_file')
        metadata_path = settings.get('knowledge_base.metadata_file')
        
        if Path(index_path).exists() and Path(metadata_path).exists():
            logger.info("Loading existing index")
            self.indexer.load(index_path, metadata_path)
        else:
            logger.warning(f"Index not found at {index_path}. Run setup_knowledge_base.py first.")
    
    @PerformanceMonitor.track_latency("document_retrieval")
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results (defaults to config value)
            
        Returns:
            List of result dictionaries with text, source, score, and chunk_id
        """
        if top_k is None:
            top_k = settings.top_k
        
        logger.info(f"Retrieving documents for query: '{query[:100]}...' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search index
        results = self.indexer.search(query_embedding, top_k)
        
        # Format results
        formatted_results = []
        for metadata, score in results:
            formatted_results.append({
                "text": metadata.get("text", ""),
                "source": metadata.get("source", "unknown"),
                "chunk_id": metadata.get("chunk_id", 0),
                "score": round(score, 4)
            })
        
        logger.info(f"Retrieved {len(formatted_results)} documents")
        return formatted_results
    
    def retrieve_with_context(self, query: str, top_k: int = None) -> str:
        """
        Retrieve documents and format as context string.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Formatted context string with citations
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return "No relevant documents found."
        
        # Format as context with citations
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result['source']
            text = result['text']
            score = result['score']
            
            context_parts.append(
                f"[Source {i}: {source} (relevance: {score:.2f})]\n{text}\n"
            )
        
        context = "\n".join(context_parts)
        return context
    
    @property
    def is_ready(self) -> bool:
        """Check if retriever is ready (index loaded)."""
        return self.indexer.num_vectors > 0
