"""
Manager Agent implementation using Groq API.
Decides when to use retrieval and orchestrates the workflow.
"""

import json
from typing import Dict, Any, Optional
from groq import Groq
from pydantic import BaseModel, ValidationError

from agents.prompts import get_manager_prompt
from config.settings import settings
from utils.logger import get_logger
from utils.monitoring import PerformanceMonitor, log_event

logger = get_logger(__name__)


class ManagerDecision(BaseModel):
    """Validated structure for Manager Agent decisions."""
    needs_retrieval: bool
    reasoning: str
    search_query: Optional[str] = None
    specialist_prompt: Optional[str] = None


class ManagerAgent:
    """Manager Agent for orchestrating document retrieval and analysis."""
    
    def __init__(self):
        """Initialize Manager Agent with Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.manager_model
        self.system_prompt = get_manager_prompt()
        logger.info(f"ManagerAgent initialized with model: {self.model}")
    
    @PerformanceMonitor.track_latency("manager_agent_decision")
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query and decide on retrieval strategy.
        
        Args:
            user_query: User's question
            
        Returns:
            Dictionary with decision, reasoning, search_query, and specialist_prompt
        """
        logger.info(f"Manager analyzing query: '{user_query[:100]}...'")
        
        log_event("MANAGER_ANALYSIS_START", {"query": user_query[:100]})
        
        # Construct prompt
        user_message = f"""Analyze this user query and decide if document retrieval is needed:

User Query: "{user_query}"

Respond in JSON format as specified in your instructions."""
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=settings.get('agents.manager.temperature', 0.1),
                max_tokens=settings.get('agents.manager.max_tokens', 1000),
                response_format={"type": "json_object"}
            )
            
            # Parse and validate response
            decision_json = response.choices[0].message.content
            decision_dict = json.loads(decision_json)
            
            # Validate with Pydantic
            decision = ManagerDecision(**decision_dict)
            
            logger.info(f"Manager decision: needs_retrieval={decision.needs_retrieval}")
            logger.info(f"Reasoning: {decision.reasoning}")
            
            log_event("MANAGER_DECISION", {
                "needs_retrieval": decision.needs_retrieval,
                "reasoning": decision.reasoning,
                "search_query": decision.search_query or 'N/A'
            })
            
            return decision.model_dump()
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid Manager response format: {str(e)}", exc_info=True)
            log_event("MANAGER_VALIDATION_ERROR", {"error": str(e)})
            
            # Fallback to safe default
            return {
                "needs_retrieval": True,
                "reasoning": "Defaulting to retrieval due to response parsing error",
                "search_query": user_query
            }
        except Exception as e:
            logger.error(f"Manager agent error: {str(e)}", exc_info=True)
            log_event("MANAGER_ERROR", {"error": str(e)})
            
            # Fallback decision
            return {
                "needs_retrieval": True,
                "reasoning": "Error in decision making, defaulting to retrieval",
                "search_query": user_query,
                "specialist_prompt": f"Answer this question: {user_query}"
            }
    
    def build_specialist_prompt(
        self,
        user_query: str,
        retrieved_context: Optional[str] = None
    ) -> str:
        """
        Build prompt for Specialist Agent.
        
        Args:
            user_query: Original user query
            retrieved_context: Retrieved document context (if any)
            
        Returns:
            Formatted prompt for Specialist
        """
        if retrieved_context:
            prompt = f"""Context from Knowledge Base:
{retrieved_context}

User Question: {user_query}

Please provide a comprehensive answer based on the context above. Include citations."""
        else:
            prompt = f"""User Question: {user_query}

Note: No relevant documents were found in the knowledge base. Please provide a general response or indicate that you don't have specific information."""
        
        return prompt
