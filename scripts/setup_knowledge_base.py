"""
Script to setup knowledge base: chunk documents, create embeddings, and build FAISS index.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import re

from mcp_server.retrieval.embedder import DocumentEmbedder
from mcp_server.retrieval.indexer import DocumentIndexer
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Chunk text into smaller segments with sentence awareness.
    
    Args:
        text: Input text
        chunk_size: Target size in words
        overlap: Overlap in words
        
    Returns:
        List of text chunks
    """
    # Simply split by sentences (rudimentary) to avoid breaking mid-sentence
    # In production, use nltk or spacy
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        words = sentence.split()
        sentence_size = len(words)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append('. '.join(current_chunk) + '.')
            
            # Keep last few sentences for overlap
            overlap_sentences = []
            overlap_size = 0
            for s in reversed(current_chunk):
                s_len = len(s.split())
                if overlap_size + s_len <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += s_len
                else:
                    break
            current_chunk = overlap_sentences
            current_size = overlap_size
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks


def load_and_chunk_documents(raw_path: str) -> List[Dict[str, Any]]:
    """
    Load all markdown documents and chunk them.
    
    Args:
        raw_path: Path to raw documents directory
        
    Returns:
        List of chunk dictionaries with text, source, and chunk_id
    """
    raw_dir = Path(raw_path)
    all_chunks = []
    
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap
    
    logger.info(f"Loading documents from {raw_dir}")
    
    # Process each markdown file
    for md_file in sorted(raw_dir.glob("*.md")):
        logger.info(f"Processing {md_file.name}")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Chunk the document
        chunks = chunk_text(content, chunk_size, overlap)
        
        # Create metadata for each chunk
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk.strip(),
                "source": md_file.stem,
                "chunk_id": i
            })
        
        logger.info(f"  Created {len(chunks)} chunks from {md_file.name}")
    
    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks


def main():
    """Main setup function."""
    logger.info("=" * 60)
    logger.info("Starting Knowledge Base Setup")
    logger.info("=" * 60)
    
    # Get paths from config
    raw_path = settings.get('knowledge_base.raw_path')
    processed_path = settings.get('knowledge_base.processed_path')
    embeddings_file = settings.get('knowledge_base.embeddings_file')
    metadata_file = settings.get('knowledge_base.metadata_file')
    chunks_file = settings.get('knowledge_base.chunks_file')
    
    # Create processed directory
    Path(processed_path).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load and chunk documents
    logger.info("\n[Step 1/4] Loading and chunking documents...")
    chunks = load_and_chunk_documents(raw_path)
    
    # Save chunks for reference
    with open(chunks_file, 'w') as f:
        json.dump(chunks, f, indent=2)
    logger.info(f"Saved chunks to {chunks_file}")
    
    # Step 2: Initialize embedder
    logger.info("\n[Step 2/4] Initializing embedding model...")
    embedder = DocumentEmbedder()
    
    # Step 3: Generate embeddings
    logger.info("\n[Step 3/4] Generating embeddings...")
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedder.embed_batch(texts, batch_size=32)
    
    # Step 4: Create and save index
    logger.info("\n[Step 4/4] Creating FAISS index...")
    indexer = DocumentIndexer(embedder.embedding_dimension)
    indexer.create_index(embeddings, chunks)
    indexer.save(embeddings_file, metadata_file)
    
    logger.info("\n" + "=" * 60)
    logger.info("Knowledge Base Setup Complete!")
    logger.info("=" * 60)
    logger.info(f"Total documents processed: {len(set(c['source'] for c in chunks))}")
    logger.info(f"Total chunks: {len(chunks)}")
    logger.info(f"Embedding dimension: {embedder.embedding_dimension}")
    logger.info(f"Index size: {indexer.num_vectors} vectors")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
