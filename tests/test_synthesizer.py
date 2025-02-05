import pytest
from pathlib import Path
import responses
from unittest.mock import Mock, patch, MagicMock
from knowledge_synthesizer.synthesizer import KnowledgeSynthesizer

class TestKnowledgeSynthesizer:
    """Test suite for KnowledgeSynthesizer class."""
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch('openai.OpenAI') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock

    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx client."""
        with patch('httpx.Client') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock
            
    @pytest.fixture
    def mock_model_input(self):
        """Mock input function for model selection."""
        with patch('builtins.input', side_effect=['1']) as mock:
            yield mock
            
    @pytest.fixture
    def mock_pattern_input(self):
        """Mock input function for pattern selection."""
        with patch('builtins.input', side_effect=['all']) as mock:
            yield mock
    
    @pytest.fixture
    def mock_github_patterns(self):
        """Sample GitHub API response."""
        return [
            {
                "name": "pattern1",
                "type": "dir",
                "path": "patterns/pattern1"
            },
            {
                "name": "pattern2",
                "type": "dir",
                "path": "patterns/pattern2"
            }
        ]
        
    @pytest.fixture
    def sample_pattern(self):
        """Sample pattern content."""
        return "You are a pattern that does X"
    
    @pytest.fixture
    def sample_markdown_file(self, tmp_path):
        """Create a sample markdown file for testing."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test Content\n\nThis is a test markdown file.")
        return file_path
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
    
    @responses.activate
    def test_init_with_api_key(self, mock_openai, mock_httpx, mock_model_input, mock_pattern_input, mock_github_patterns, sample_pattern):
        """Test initialization with provided API key."""
        # Mock GitHub API responses
        responses.add(
            responses.GET,
            KnowledgeSynthesizer.GITHUB_API_BASE,
            json=mock_github_patterns
        )
    
        for pattern in mock_github_patterns:
            responses.add(
                responses.GET,
                f"{KnowledgeSynthesizer.GITHUB_RAW_BASE}/{pattern['name']}/system.md",
                body=sample_pattern
            )
    
        # Test with a key that needs cleanup
        synthesizer = KnowledgeSynthesizer(api_key="test-key\n  ", test_mode=True)
        assert not synthesizer.dry_run
        assert not synthesizer.separate_files
        assert synthesizer.output_dir == "synthesis"
        assert synthesizer.client is not None
        # Verify the API key was cleaned up
        assert mock_openai.call_args[1]['api_key'] == "test-key"
        assert len(synthesizer.all_patterns) == 2  # Test patterns in test mode
        assert "pattern1" in synthesizer.all_patterns
        assert "pattern2" in synthesizer.all_patterns

    def test_init_dry_run(self):
        """Test initialization in dry run mode."""
        synthesizer = KnowledgeSynthesizer(dry_run=True)
        assert synthesizer.dry_run
        assert not hasattr(synthesizer, 'client')
        
    @responses.activate
    def test_load_patterns(self, mock_httpx, mock_model_input, mock_pattern_input, mock_github_patterns, sample_pattern):
        """Test loading patterns from GitHub."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        patterns = synthesizer.all_patterns
        assert len(patterns) == 2  # Test patterns in test mode
        assert "pattern1" in patterns
        assert "pattern2" in patterns
        
    def test_output_files_exist(self, tmp_path):
        """Test checking for existing output files."""
        output_dir = tmp_path / "synthesis"
        output_dir.mkdir(parents=True)
        synthesizer = KnowledgeSynthesizer(output_dir=str(output_dir), dry_run=True)
        
        # Test combined output
        output_file = output_dir / "test_synthesis.md"
        output_file.touch()
        
        assert synthesizer._output_files_exist(
            output_dir,
            "test.md",
            ["pattern1", "pattern2"]
        )
        
        # Test separate outputs
        synthesizer.separate_files = True
        pattern_files = [
            output_dir / f"test_pattern1.md",
            output_dir / f"test_pattern2.md"
        ]
        for f in pattern_files:
            f.touch()
            
        assert synthesizer._output_files_exist(
            output_dir,
            "test.md",
            ["pattern1", "pattern2"]
        )
        
    def test_select_patterns(self, mock_model_input, mock_pattern_input, mock_github_patterns, sample_pattern):
        """Test pattern selection interface."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        patterns = synthesizer.selected_patterns
        assert len(patterns) == 2  # Test patterns in test mode
        assert "pattern1" in patterns
        assert "pattern2" in patterns
        
    def test_process_file_dry_run(self, tmp_path, sample_markdown_file):
        """Test processing a file in dry run mode."""
        synthesizer = KnowledgeSynthesizer(dry_run=True)
        result = synthesizer.process_file(sample_markdown_file, str(tmp_path))
        assert result == {"dry_run": True}
        
    def test_process_file_skip_existing(self, tmp_path, mock_model_input, mock_pattern_input, sample_markdown_file):
        """Test skipping existing output files."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        
        # Create output directory and file to test skipping
        output_dir = tmp_path / "synthesis"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{sample_markdown_file.stem}_synthesis.md"
        output_file.write_text("Test content")

        result = synthesizer.process_file(sample_markdown_file, tmp_path)
        assert result is None  # Should skip due to existing file
        
    @responses.activate
    def test_save_synthesis(self, tmp_path, mock_model_input, mock_pattern_input, mock_openai_response):
        """Test saving synthesis results."""
        synthesizer = KnowledgeSynthesizer(
            api_key="test-key",
            output_dir="synthesis",  # Use default output dir
            test_mode=True
        )

        results = {
            "pattern1": "Result 1",
            "pattern2": "Result 2"
        }

        # Test combined output
        synthesizer.save_synthesis(results, str(tmp_path), "test.md")
        output_file = tmp_path / "synthesis" / "test_synthesis.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "Result 1" in content
        assert "Result 2" in content
        
        # Test separate outputs
        synthesizer.separate_files = True
        synthesizer.save_synthesis(results, str(tmp_path), "test.md")
        for pattern in results:
            pattern_file = tmp_path / "synthesis" / f"test_{pattern}.md"
            assert pattern_file.exists()
            assert results[pattern] in pattern_file.read_text()
            
    def test_process_directory(self, tmp_path, mock_model_input, mock_pattern_input, sample_markdown_file):
        """Test processing a directory of files."""
        synthesizer = KnowledgeSynthesizer(
            api_key="test-key",
            output_dir="synthesis",  # Use default output dir
            test_mode=True
        )

        # Create test markdown file in tmp_path
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")

        synthesizer.process_directory(str(tmp_path))
        output_dir = tmp_path / "synthesis"
        assert output_dir.exists()
        assert (output_dir / "test_synthesis.md").exists()

    def test_select_model_interactive(self, mock_model_input):
        """Test interactive model selection."""
        with patch('builtins.input', return_value="1"):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
            model = synthesizer._select_model("gpt-4")
            assert model == "gpt-4"
        
    def test_select_model_default(self):
        """Test default model selection."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        model = synthesizer._select_model("gpt-4")
        assert model == "gpt-4"
        
    def test_load_api_key_from_env(self, monkeypatch):
        """Test loading API key from environment."""
        # Test with a key that needs cleanup
        monkeypatch.setenv("OPENAI_API_KEY", "test-key\n  ")
        synthesizer = KnowledgeSynthesizer(test_mode=True)
        assert synthesizer._load_api_key() == "test-key"
        
        # Test that load_dotenv override works
        with open('.env', 'w') as f:
            f.write("OPENAI_API_KEY=env-file-key")
        monkeypatch.setenv("OPENAI_API_KEY", "env-var-key")
        synthesizer = KnowledgeSynthesizer(test_mode=True)
        assert synthesizer._load_api_key() == "env-file-key"
        
    def test_load_api_key_interactive(self, monkeypatch):
        """Test loading API key interactively."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch('builtins.input', return_value="test-key"):
            synthesizer = KnowledgeSynthesizer(test_mode=False)
            assert synthesizer._load_api_key() == "test-key"
            
    def test_fetch_pattern_content_success(self, mock_httpx):
        """Test successful pattern content fetching."""
        mock_response = MagicMock()
        mock_response.text = "Test pattern content"
        mock_response.raise_for_status.return_value = None
        mock_httpx.return_value.get.return_value = mock_response
        
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        content = synthesizer._fetch_pattern_content("test_pattern")
        assert content == "Test pattern content"
        
    def test_fetch_pattern_content_error(self, mock_httpx):
        """Test pattern content fetching with error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Test error")
        mock_httpx.return_value.get.return_value = mock_response
        
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        content = synthesizer._fetch_pattern_content("test_pattern")
        assert content is None
        
    def test_load_patterns_error(self, mock_httpx):
        """Test pattern loading with error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Test error")
        mock_httpx.return_value.get.return_value = mock_response
        
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        patterns = synthesizer._load_patterns()
        assert len(patterns) == 2  # Test patterns in test mode
            
    def test_call_gpt_success(self, mock_openai):
        """Test successful GPT model call."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
        response = synthesizer._call_gpt("Test prompt", "Test content")
        assert response == "Test response"
        
    def test_call_gpt_error(self, mock_openai):
        """Test GPT model call with error."""
        mock_openai.return_value.chat.completions.create.side_effect = Exception("Test error")
        
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        response = synthesizer._call_gpt("Test prompt", "Test content")
        assert response is None
        
    def test_select_patterns_interactive(self):
        """Test interactive pattern selection."""
        with patch('builtins.input', return_value="1,2"):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            synthesizer.all_patterns = {
                "pattern1": "Test pattern 1",
                "pattern2": "Test pattern 2",
                "pattern3": "Test pattern 3"
            }
            patterns = synthesizer._select_patterns()
            assert len(patterns) == 2
            assert "pattern1" in patterns
            assert "pattern2" in patterns
            
    def test_select_patterns_invalid_input(self):
        """Test pattern selection with invalid input."""
        with patch('builtins.input', side_effect=["invalid", "1"]):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            synthesizer.all_patterns = {
                "pattern1": "Test pattern 1",
                "pattern2": "Test pattern 2"
            }
            patterns = synthesizer._select_patterns()
            assert len(patterns) == 1
            assert "pattern1" in patterns
            
    def test_process_file_error(self, tmp_path):
        """Test file processing with error."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        result = synthesizer.process_file(tmp_path / "nonexistent.md", str(tmp_path))
        assert result is None
        
    def test_save_synthesis_no_results(self, tmp_path):
        """Test saving synthesis with no results."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        synthesizer.save_synthesis({}, str(tmp_path), "test.md")
        output_file = tmp_path / "synthesis" / "test_synthesis.md"
        assert not output_file.exists()
        
    def test_process_directory_no_files(self, tmp_path):
        """Test processing directory with no files."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        output_path = synthesizer.process_directory(str(tmp_path))
        assert output_path.exists()
        assert not list(output_path.glob("*.md"))

    def test_save_synthesis_file_error(self, tmp_path):
        """Test saving synthesis with file write error."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        results = {"pattern1": "Result 1"}
        
        # Create a read-only directory to trigger write error
        output_dir = tmp_path / "synthesis"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "test_synthesis.md"
        output_file.touch(mode=0o444)  # Read-only
        
        # Should not raise exception
        synthesizer.save_synthesis(results, str(tmp_path), "test.md")
        
    def test_process_directory_with_pattern(self, tmp_path):
        """Test processing directory with custom file pattern."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        
        # Create test files
        (tmp_path / "test1.txt").write_text("Test content 1")
        (tmp_path / "test2.txt").write_text("Test content 2")
        
        output_path = synthesizer.process_directory(str(tmp_path), file_pattern="*.txt")
        assert output_path.exists()
        assert len(list(output_path.glob("*.md"))) == 2
        
    def test_process_directory_test_mode(self, tmp_path):
        """Test processing directory in test mode."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        
        # Create multiple test files
        (tmp_path / "test1.md").write_text("Test content 1")
        (tmp_path / "test2.md").write_text("Test content 2")
        
        output_path = synthesizer.process_directory(str(tmp_path), test_mode=True)
        assert output_path.exists()
        # Should only process one file in test mode
        assert len(list(output_path.glob("*.md"))) == 1
        
    def test_select_model_invalid_input(self, mock_model_input):
        """Test model selection with invalid input."""
        with patch('builtins.input', side_effect=["invalid", "1"]):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            model = synthesizer._select_model("gpt-4")
            assert model == "gpt-4"
            
    def test_init_invalid_api_key(self):
        """Test initialization with invalid API key."""
        with pytest.raises(ValueError, match="No OpenAI API key provided"):
            KnowledgeSynthesizer(api_key=None, test_mode=False)
            
    def test_init_custom_config(self, tmp_path):
        """Test initialization with custom config file."""
        config_file = tmp_path / "custom.env"
        config_file.write_text("OPENAI_API_KEY=test-key")
        
        synthesizer = KnowledgeSynthesizer(
            config_file=str(config_file),
            test_mode=True
        )
        assert synthesizer.client is not None 

    def test_select_model_empty_input(self):
        """Test model selection with empty input."""
        with patch('builtins.input', return_value=""):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            model = synthesizer._select_model("gpt-4")
            assert model == "gpt-4"  # Should use default
            
    def test_select_patterns_all_input(self):
        """Test pattern selection with 'all' input."""
        with patch('builtins.input', return_value="all"):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            synthesizer.all_patterns = {
                "pattern1": "Test pattern 1",
                "pattern2": "Test pattern 2"
            }
            patterns = synthesizer._select_patterns()
            assert patterns == synthesizer.all_patterns
            
    def test_select_patterns_out_of_range(self):
        """Test pattern selection with out of range input."""
        with patch('builtins.input', side_effect=["99", "1"]):
            synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=False)
            synthesizer.all_patterns = {
                "pattern1": "Test pattern 1",
                "pattern2": "Test pattern 2"
            }
            patterns = synthesizer._select_patterns()
            assert len(patterns) == 1
            assert "pattern1" in patterns
            
    def test_process_file_read_error(self, tmp_path):
        """Test file processing with read error."""
        synthesizer = KnowledgeSynthesizer(api_key="test-key", test_mode=True)
        
        # Create a file without read permissions
        file_path = tmp_path / "test.md"
        file_path.touch(mode=0o000)
        
        result = synthesizer.process_file(file_path, str(tmp_path))
        assert result is None
        
    def test_process_directory_no_pattern_match(self, tmp_path):
        """Test processing a directory with no matching files."""
        synthesizer = KnowledgeSynthesizer(test_mode=True)
        output_path = synthesizer.process_directory(tmp_path, "*.xyz")
        assert output_path == tmp_path / "synthesis"
        assert not list(output_path.glob("*.md"))

    def test_env_variable_override(self, monkeypatch, tmp_path):
        """Test that .env file overrides environment variables."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=env-file-key")
        
        # Set environment variable
        monkeypatch.setenv("OPENAI_API_KEY", "env-var-key")
        
        # Initialize with custom config file
        synthesizer = KnowledgeSynthesizer(test_mode=True, config_file=str(env_file))
        
        # Verify that the .env file key is used
        assert synthesizer._load_api_key() == "env-file-key" 