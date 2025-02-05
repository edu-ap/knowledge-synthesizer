import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def sample_pattern():
    """Return a sample Fabric pattern content."""
    return """You are an AI assistant tasked with extracting key insights.
Focus on the main themes and important takeaways.
Be concise and clear in your analysis."""

@pytest.fixture
def mock_github_patterns():
    """Mock GitHub API response for pattern listing."""
    return [
        {"name": "extract_wisdom", "type": "dir"},
        {"name": "create_summary", "type": "dir"},
        {"name": "analyze_patterns", "type": "dir"}
    ]

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test analysis result"))]
    return mock_response

@pytest.fixture
def sample_markdown_file(temp_dir):
    """Create a sample markdown file for testing."""
    content = """# Test Document
    
This is a test document with some content.
It has multiple lines and paragraphs.

## Section 1
- Point 1
- Point 2

## Section 2
Some more content here."""
    
    file_path = temp_dir / "test.md"
    file_path.write_text(content)
    return file_path

@pytest.fixture
def mock_env_file(temp_dir):
    """Create a mock .env file."""
    env_path = temp_dir / ".env"
    env_path.write_text("OPENAI_API_KEY=test-key-12345")
    return env_path 