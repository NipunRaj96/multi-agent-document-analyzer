"""
Configuration loader for the Multi-Agent Document Analysis System.
Loads settings from config.json and provides easy access throughout the application.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class Settings:
    """Singleton configuration loader."""
    
    _instance = None
    _config: Dict[str, Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.json."""
        config_path = Path(__file__).parent.parent / "config.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = json.load(f)
        
        # Override with environment variables (for security)
        if os.getenv('GEMINI_API_KEY'):
            self._config['api_keys']['gemini_api_key'] = os.getenv('GEMINI_API_KEY')
        if os.getenv('GROQ_API_KEY'):
            self._config['api_keys']['groq_api_key'] = os.getenv('GROQ_API_KEY')
        
        # Create logs directory if it doesn't exist
        log_file = self._config.get('logging', {}).get('file', 'logs/system.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'api_keys.gemini_api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def gemini_api_key(self) -> str:
        """Get Gemini API key."""
        return self.get('api_keys.gemini_api_key')
    
    @property
    def groq_api_key(self) -> str:
        """Get Groq API key."""
        return self.get('api_keys.groq_api_key')
    
    @property
    def mcp_host(self) -> str:
        """Get MCP server host."""
        return self.get('mcp_server.host', '0.0.0.0')
    
    @property
    def mcp_port(self) -> int:
        """Get MCP server port."""
        return self.get('mcp_server.port', 8000)
    
    @property
    def embedding_model(self) -> str:
        """Get embedding model name."""
        return self.get('retrieval.embedding_model')
    
    @property
    def chunk_size(self) -> int:
        """Get chunk size for document splitting."""
        return self.get('retrieval.chunk_size', 500)
    
    @property
    def chunk_overlap(self) -> int:
        """Get chunk overlap size."""
        return self.get('retrieval.chunk_overlap', 50)
    
    @property
    def top_k(self) -> int:
        """Get number of top results to retrieve."""
        return self.get('retrieval.top_k', 5)
    
    @property
    def manager_model(self) -> str:
        """Get Manager Agent model name."""
        return self.get('agents.manager.model')
    
    @property
    def specialist_model(self) -> str:
        """Get Specialist Agent model name."""
        return self.get('agents.specialist.model')


# Global settings instance
settings = Settings()
