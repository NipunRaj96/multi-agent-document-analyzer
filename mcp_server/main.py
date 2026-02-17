"""
FastAPI MCP Server - Main application.
Implements Model Context Protocol endpoints for document retrieval.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from mcp_server.models import (
    ToolListResponse,
    ToolInvocationRequest,
    ToolInvocationResponse,
    HealthResponse
)
from mcp_server.tools import list_tools, get_tool
from utils.logger import get_logger
from utils.monitoring import log_event, PerformanceMonitor

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Tool Server",
    description="Model Context Protocol server for document retrieval",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("=" * 60)
    logger.info("MCP Tool Server Starting")
    logger.info("=" * 60)
    log_event("SERVER_STARTUP", {"status": "initializing"})


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("MCP Tool Server Shutting Down")
    log_event("SERVER_SHUTDOWN", {"status": "complete"})


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MCP Tool Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    tool = get_tool("document_retriever")
    
    return HealthResponse(
        status="healthy" if tool.is_ready else "degraded",
        index_loaded=tool.is_ready,
        num_documents=tool.retriever.indexer.num_vectors if tool.is_ready else 0
    )


@app.get("/mcp/v1/tools", response_model=ToolListResponse)
async def list_available_tools():
    """
    MCP endpoint: List available tools.
    
    Returns:
        List of tool definitions
    """
    logger.info("Listing available tools")
    tools = list_tools()
    
    log_event("TOOLS_LISTED", {"count": len(tools)})
    
    return ToolListResponse(tools=tools)


@app.post("/mcp/v1/tools/invoke", response_model=ToolInvocationResponse)
async def invoke_tool(request: ToolInvocationRequest):
    """
    MCP endpoint: Invoke a tool.
    
    Args:
        request: Tool invocation request
        
    Returns:
        Tool invocation response with results
    """
    tool_name = request.tool_name
    parameters = request.parameters
    
    logger.info(f"Invoking tool: {tool_name}")
    log_event("TOOL_INVOKE_REQUEST", {
        "tool": tool_name,
        "parameters": parameters
    })
    
    # Get tool
    tool = get_tool(tool_name)
    if not tool:
        logger.error(f"Tool not found: {tool_name}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Check if tool is ready
    if not tool.is_ready:
        logger.error(f"Tool not ready: {tool_name}")
        raise HTTPException(
            status_code=503,
            detail=f"Tool '{tool_name}' not ready. Index may not be loaded."
        )
    
    # Invoke tool
    try:
        results = tool.invoke(parameters)
        
        response = ToolInvocationResponse(
            tool_name=tool_name,
            results=results,
            status="success",
            message=f"Retrieved {len(results)} results"
        )
        
        log_event("TOOL_INVOKE_SUCCESS", {
            "tool": tool_name,
            "results_count": len(results)
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Tool invocation failed: {str(e)}", exc_info=True)
        log_event("TOOL_INVOKE_ERROR", {
            "tool": tool_name,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Tool invocation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    uvicorn.run(
        app,
        host=settings.mcp_host,
        port=settings.mcp_port,
        log_level="info"
    )
