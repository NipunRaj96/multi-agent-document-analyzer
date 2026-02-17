
import pytest
from mcp_server.models import ToolDefinition, ToolParameter, RetrievalResult
from pydantic import ValidationError

def test_tool_definition_creation():
    """Test creating a valid tool definition."""
    tool = ToolDefinition(
        name="test_tool",
        description="Test description",
        parameters={
            "query": ToolParameter(type="string", description="Search query")
        }
    )
    assert tool.name == "test_tool"
    assert tool.description == "Test description"
    assert "query" in tool.parameters
    assert tool.parameters["query"].type == "string"

def test_retrieval_result_creation():
    """Test creating a valid retrieval result."""
    result = RetrievalResult(
        text="Test text",
        source="test_doc.md",
        chunk_id=1,
        score=0.95
    )
    assert result.text == "Test text"
    assert result.source == "test_doc.md"
    assert result.score == 0.95

def test_tool_parameter_validation():
    """Test validation of tool parameters."""
    with pytest.raises(ValidationError):
        ToolParameter(type="string", description="Missing required field", required="not_bool")
