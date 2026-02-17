"""
Pydantic models for MCP protocol compliance.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""
    type: str = Field(..., description="Parameter type (e.g., 'string', 'number')")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")


class ToolDefinition(BaseModel):
    """MCP tool definition."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, ToolParameter] = Field(..., description="Tool parameters")


class ToolListResponse(BaseModel):
    """Response for listing available tools."""
    tools: List[ToolDefinition] = Field(..., description="List of available tools")


class ToolInvocationRequest(BaseModel):
    """Request to invoke a tool."""
    tool_name: str = Field(..., description="Name of tool to invoke")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")


class RetrievalResult(BaseModel):
    """Single retrieval result."""
    text: str = Field(..., description="Retrieved text snippet")
    source: str = Field(..., description="Source document name")
    chunk_id: int = Field(..., description="Chunk identifier")
    score: float = Field(..., description="Relevance score")


class ToolInvocationResponse(BaseModel):
    """Response from tool invocation."""
    tool_name: str = Field(..., description="Name of invoked tool")
    results: List[RetrievalResult] = Field(..., description="Retrieval results")
    status: str = Field(default="success", description="Invocation status")
    message: Optional[str] = Field(default=None, description="Optional message")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    index_loaded: bool = Field(..., description="Whether index is loaded")
    num_documents: int = Field(..., description="Number of indexed documents")
