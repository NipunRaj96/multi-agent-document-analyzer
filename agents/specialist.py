"""
Specialist Agent implementation using Google Gemini API.
Synthesizes final answers grounded in retrieved context.
"""

from typing import Optional
import google.generativeai as genai

from agents.prompts import get_specialist_prompt
from config.settings import settings
from utils.logger import get_logger
from utils.monitoring import PerformanceMonitor, log_event

logger = get_logger(__name__)


class SpecialistAgent:
    """Specialist Agent for synthesizing grounded answers."""
    
    def __init__(self):
        """Initialize Specialist Agent with Gemini client."""
        genai.configure(api_key=settings.gemini_api_key)
        
        self.model_name = settings.specialist_model
        self.system_prompt = get_specialist_prompt()
        
        # Configure generation parameters
        self.generation_config = {
            "temperature": settings.get('agents.specialist.temperature', 0.3),
            "max_output_tokens": settings.get('agents.specialist.max_tokens', 2000),
        }
        
        # Initialize model (system prompt will be prepended to user messages)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
        
        logger.info(f"SpecialistAgent initialized with model: {self.model_name}")
    
    @PerformanceMonitor.track_latency("specialist_agent_synthesis")
    def synthesize_answer(self, prompt: str) -> str:
        """
        Synthesize final answer based on prompt and context.
        
        Args:
            prompt: Prompt from Manager Agent (includes context and question)
            
        Returns:
            Synthesized answer with citations
        """
        logger.info("Specialist synthesizing answer")
        log_event("SPECIALIST_SYNTHESIS_START", {"prompt_length": len(prompt)})
        
        try:
            # Prepend system prompt to user message
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            answer = response.text
            
            logger.info(f"Specialist generated answer ({len(answer)} chars)")
            log_event("SPECIALIST_SYNTHESIS_SUCCESS", {
                "answer_length": len(answer)
            })
            
            return answer
            
        except Exception as e:
            logger.error(f"Specialist agent error: {str(e)}", exc_info=True)
            log_event("SPECIALIST_ERROR", {"error": str(e)})
            
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    def synthesize_with_context(
        self,
        user_query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Convenience method to synthesize answer with context.
        
        Args:
            user_query: User's question
            context: Retrieved context (optional)
            
        Returns:
            Synthesized answer
        """
        if context:
            prompt = f"""Context from Knowledge Base:
{context}

User Question: {user_query}

Please provide a comprehensive answer based on the context above. Include citations."""
        else:
            prompt = f"""User Question: {user_query}

Note: No relevant documents were found in the knowledge base. Please provide a general response or indicate that you don't have specific information."""
        
        return self.synthesize_answer(prompt)
