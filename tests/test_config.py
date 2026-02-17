
import pytest
from config.settings import settings
import os

def test_settings_singleton():
    """Test that settings is a singleton."""
    s1 = settings
    s2 = settings
    assert s1 is s2

def test_config_keys_exist():
    """Test that essential configuration keys exist."""
    # These should come from config.json or environment variables
    # We just check they are accessible via properties
    # Note: Values might be None if not set in env/config, but properties should exist
    assert hasattr(settings, 'gemini_api_key')
    assert hasattr(settings, 'groq_api_key')
    assert hasattr(settings, 'embedding_model')
    assert hasattr(settings, 'mcp_host')
    assert hasattr(settings, 'mcp_port')

def test_default_values():
    """Test default values for optional settings."""
    assert settings.chunk_size == 500
    assert settings.chunk_overlap == 50
    assert settings.top_k == 5
