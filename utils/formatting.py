from typing import List, Dict, Any

def format_retrieval_results(results: List[Dict[str, Any]]) -> str:
    """
    Format retrieval results as context string with citations.
    
    Args:
        results: List of result dictionaries from MCP server
        
    Returns:
        Formatted string with sources
    """
    if not results:
        return ""
    
    context_parts = []
    for i, result in enumerate(results, 1):
        source = result.get('source', 'unknown')
        text = result.get('text', '')
        score = result.get('score', 0.0)
        
        context_parts.append(
            f"[Source {i}: {source} (relevance: {score:.2f})]\n{text}\n"
        )
    
    return "\n".join(context_parts)
