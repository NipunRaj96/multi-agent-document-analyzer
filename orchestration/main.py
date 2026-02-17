"""
A2A Orchestration - Main script for Multi-Agent workflow.
Coordinates Manager Agent, MCP Tool Server, and Specialist Agent.
"""

import sys
import time
import httpx
from typing import Dict, Any

from agents.manager import ManagerAgent
from agents.specialist import SpecialistAgent
from config.settings import settings
from utils.logger import get_logger
from utils.monitoring import log_event, PerformanceMonitor
from utils.formatting import format_retrieval_results

logger = get_logger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent document analysis workflow."""
    
    def __init__(self, mcp_server_url: str = None):
        """
        Initialize orchestrator.
        
        Args:
            mcp_server_url: URL of MCP server (defaults to config)
        """
        self.manager = ManagerAgent()
        self.specialist = SpecialistAgent()
        
        if mcp_server_url is None:
            host = settings.mcp_host
            port = settings.mcp_port
            mcp_server_url = f"http://{host}:{port}"
        
        self.mcp_server_url = mcp_server_url
        
        # Validate MCP server is reachable
        self._validate_mcp_server()
        
        logger.info(f"MultiAgentOrchestrator initialized with MCP server: {mcp_server_url}")
    
    def _validate_mcp_server(self):
        """Validate MCP server is running and healthy."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.mcp_server_url}/health")
                response.raise_for_status()
                health = response.json()
                
                if not health.get('index_loaded'):
                    logger.warning("MCP server is running but index not loaded")
                else:
                    logger.info(f"MCP server healthy: {health.get('num_documents')} documents indexed")
        except Exception as e:
            logger.error(f"MCP server health check failed: {e}")
            logger.error("Please start MCP server: uvicorn mcp_server.main:app --port 8000")
            raise RuntimeError("MCP server not available") from e
    
    @PerformanceMonitor.track_latency("mcp_tool_call")
    def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP tool server.
        
        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool response
        """
        logger.info(f"Calling MCP tool: {tool_name}")
        log_event("MCP_TOOL_CALL", {
            "tool": tool_name,
            "parameters": parameters
        })
        
        url = f"{self.mcp_server_url}/mcp/v1/tools/invoke"
        payload = {
            "tool_name": tool_name,
            "parameters": parameters
        }
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                
                logger.info(f"MCP tool call successful: {len(result.get('results', []))} results")
                log_event("MCP_TOOL_SUCCESS", {
                    "tool": tool_name,
                    "results_count": len(result.get('results', []))
                })
                
                return result
                
            except httpx.HTTPStatusError as e:
                # Retry on 5xx errors
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"MCP call failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"MCP tool call failed: {str(e)}", exc_info=True)
                log_event("MCP_TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                raise
            except Exception as e:
                logger.error(f"MCP tool call failed: {str(e)}", exc_info=True)
                log_event("MCP_TOOL_ERROR", {"tool": tool_name, "error": str(e)})
                raise
    

    
    @PerformanceMonitor.track_latency("end_to_end_query")
    def process_query(self, user_query: str) -> str:
        """
        Process user query through the multi-agent workflow.
        
        Args:
            user_query: User's question
            
        Returns:
            Final answer from Specialist Agent
        """
        logger.info("=" * 60)
        logger.info(f"Processing query: {user_query}")
        logger.info("=" * 60)
        
        log_event("QUERY_START", {"query": user_query})
        
        # Step 1: Manager analyzes query
        logger.info("\n[Step 1/3] Manager Agent analyzing query...")
        decision = self.manager.analyze_query(user_query)
        
        retrieved_context = None
        
        # Step 2: Retrieve documents if needed
        if decision.get('needs_retrieval', False):
            logger.info("\n[Step 2/3] Calling MCP Tool Server for retrieval...")
            search_query = decision.get('search_query', user_query)
            
            try:
                mcp_response = self.call_mcp_tool(
                    tool_name="document_retriever",
                    parameters={"query": search_query}
                )
                
                
                results = mcp_response.get('results', [])
                retrieved_context = format_retrieval_results(results)
                
                logger.info(f"Retrieved {len(results)} document chunks")
                
            except Exception as e:
                logger.error(f"Retrieval failed: {str(e)}")
                retrieved_context = None
        else:
            logger.info("\n[Step 2/3] Skipping retrieval (not needed)")
        
        # Step 3: Specialist synthesizes answer
        logger.info("\n[Step 3/3] Specialist Agent synthesizing answer...")
        
        specialist_prompt = self.manager.build_specialist_prompt(
            user_query=user_query,
            retrieved_context=retrieved_context
        )
        
        final_answer = self.specialist.synthesize_answer(specialist_prompt)
        
        logger.info("\n" + "=" * 60)
        logger.info("Query processing complete")
        logger.info("=" * 60)
        
        log_event("QUERY_COMPLETE", {
            "query": user_query,
            "retrieval_used": decision.get('needs_retrieval', False)
        })
        
        return final_answer
    
    def interactive_mode(self):
        """Run in interactive CLI mode."""
        print("\n" + "=" * 60)
        print("Multi-Agent Document Analysis System")
        print("=" * 60)
        print("Type your questions below. Type 'exit' or 'quit' to stop.\n")
        
        while True:
            try:
                user_input = input("\n🔍 Your question: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye! 👋")
                    break
                
                if not user_input:
                    continue
                
                # Process query
                answer = self.process_query(user_input)
                
                # Display answer
                print("\n" + "=" * 60)
                print("📝 Answer:")
                print("=" * 60)
                print(answer)
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye! 👋")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {str(e)}", exc_info=True)
                print(f"\n❌ Error: {str(e)}")


def main():
    """Main entry point."""
    logger.info("Starting Multi-Agent Orchestration")
    
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Check if query provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        answer = orchestrator.process_query(query)
        print("\n" + "=" * 60)
        print("Answer:")
        print("=" * 60)
        print(answer)
        print("=" * 60)
    else:
        # Interactive mode
        orchestrator.interactive_mode()


if __name__ == "__main__":
    main()
