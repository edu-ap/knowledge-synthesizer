"""Test suite for CLI module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from knowledge_synthesizer.cli import main

class TestCLI:
    """Test suite for CLI functionality."""
    
    def test_main_help(self, capsys):
        """Test main function with help flag."""
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "Knowledge Synthesizer" in captured.out
        
    def test_main_version(self, capsys):
        """Test main function with version flag."""
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "Knowledge Synthesizer" in captured.out
        
    def test_main_process_file(self, tmp_path):
        """Test processing a single file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")
        
        with patch('knowledge_synthesizer.cli.KnowledgeSynthesizer') as mock_synth:
            mock_instance = MagicMock()
            mock_synth.return_value = mock_instance
            
            main([str(test_file)])
            
            mock_instance.process_file.assert_called_once()
            mock_instance.save_synthesis.assert_called_once()
            
    def test_main_process_directory(self, tmp_path):
        """Test processing a directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "test.md").write_text("Test content")
        
        with patch('knowledge_synthesizer.cli.KnowledgeSynthesizer') as mock_synth:
            mock_instance = MagicMock()
            mock_synth.return_value = mock_instance
            
            main([str(test_dir), "--recursive"])
            
            mock_instance.process_directory.assert_called_once()
            
    def test_main_dry_run(self, tmp_path):
        """Test dry run mode."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")
        
        with patch('knowledge_synthesizer.cli.KnowledgeSynthesizer') as mock_synth:
            mock_instance = MagicMock()
            mock_synth.return_value = mock_instance
            
            main([str(test_file), "--dry-run"])
            
            mock_synth.assert_called_with(
                api_key=None,
                dry_run=True,
                force_refresh=False,
                separate_files=False
            )
            
    def test_main_force_refresh(self, tmp_path):
        """Test force refresh mode."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")
        
        with patch('knowledge_synthesizer.cli.KnowledgeSynthesizer') as mock_synth:
            mock_instance = MagicMock()
            mock_synth.return_value = mock_instance
            
            main([str(test_file), "--force"])
            
            mock_synth.assert_called_with(
                api_key=None,
                dry_run=False,
                force_refresh=True,
                separate_files=False
            )
            
    def test_main_separate_files(self, tmp_path):
        """Test separate files mode."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")
        
        with patch('knowledge_synthesizer.cli.KnowledgeSynthesizer') as mock_synth:
            mock_instance = MagicMock()
            mock_synth.return_value = mock_instance
            
            main([str(test_file), "--separate"])
            
            mock_synth.assert_called_with(
                api_key=None,
                dry_run=False,
                force_refresh=False,
                separate_files=True
            )
            
    def test_main_invalid_path(self):
        """Test with invalid input path."""
        with pytest.raises(SystemExit) as exc:
            main(["nonexistent.md"])
        assert exc.value.code == 1 