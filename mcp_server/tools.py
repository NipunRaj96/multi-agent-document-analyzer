"""
MCP tool implementations.
"""

from typing import Dict, Any, List
from mcp_server.models import ToolDefinition, ToolParameter, RetrievalResult
from mcp_server.retrieval.retriever import DocumentRetriever
from utils.logger import get_logger
from utils.monitoring import log_event

logger = get_logger(__name__)


class DocumentRetrieverTool:
    """MCP tool for document retrieval."""
    
    def __init__(self):
        """Initialize the tool with retriever."""
        self.retriever = DocumentRetriever()
        logger.info("DocumentRetrieverTool initialized")
    
    @staticmethod
    def get_definition() -> ToolDefinition:
        """Get MCP tool definition."""
        return ToolDefinition(
            name="document_retriever",
            description="Retrieves relevant text snippets from the knowledge base based on a search query. "
                       "Returns top-k most relevant document chunks with source attribution.",
            parameters={
                "query": ToolParameter(
                    type="string",
                    description="The search query to find relevant documents",
                    required=True
                ),
                "top_k": ToolParameter(
                    type="integer",
                    description="Number of results to return (default: 5)",
                    required=False
                )
            }
        )
    
    def invoke(self, parameters: Dict[str, Any]) -> List[RetrievalResult]:
        """
        Invoke the document retriever tool.
        
        Args:
            parameters: Tool parameters (query, optional top_k)
            
        Returns:
            List of retrieval results
        """
        # Validate and sanitize query
        query = parameters.get("query", "").strip()
        
        if not query:
            logger.error("Empty query provided to document_retriever")
            raise ValueError("Query parameter is required and cannot be empty")
        
        if len(query) > 1000:
            logger.warning(f"Query too long ({len(query)} chars), truncating to 1000")
            query = query[:1000]
        
        # Validate top_k
        top_k = parameters.get("top_k")
        if top_k is not None:
            if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
                logger.warning(f"Invalid top_k={top_k}, using default")
                top_k = None
        
        # Log the tool invocation
        log_event("TOOL_INVOCATION", {
            "tool": "document_retriever",
            "query": query[:100],
            "top_k": top_k
        })
        
        # Perform retrieval
        results = self.retriever.retrieve(query, top_k)
        
        # Convert to Pydantic models
        retrieval_results = [
            RetrievalResult(**result) for result in results
        ]
        
        logger.info(f"document_retriever returned {len(retrieval_results)} results")
        return retrieval_results
    
    @property
    def is_ready(self) -> bool:
        """Check if tool is ready to use."""
        return self.retriever.is_ready


# Tool registry
TOOLS = {
    "document_retriever": DocumentRetrieverTool()
}


def get_tool(tool_name: str) -> DocumentRetrieverTool:
    """Get tool by name."""
    return TOOLS.get(tool_name)


def list_tools() -> List[ToolDefinition]:
    """List all available tools."""
    return [tool.get_definition() for tool in TOOLS.values()]
