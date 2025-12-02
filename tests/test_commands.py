"""Tests for CLI commands."""
import pytest
from typer.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from docx_cli.main import app

runner = CliRunner()

@pytest.fixture
def mock_process_pool():
    with patch("docx_cli.commands.process.ProcessPoolExecutor") as mock:
        yield mock

@pytest.fixture
def mock_asyncio_run():
    with patch("asyncio.run") as mock:
        yield mock

def test_process_command_help():
    result = runner.invoke(app, ["process", "run", "--help"])
    assert result.exit_code == 0
    assert "Batch process DOCX files" in result.stdout

def test_process_command_no_files(tmp_path):
    # Empty directory
    result = runner.invoke(app, ["process", "run", str(tmp_path)])
    assert result.exit_code == 0 # Should exit gracefully
    assert "No .docx files found" in result.stdout

@patch("docx_cli.commands.process.run_parallel")
def test_process_command_success(mock_run_parallel, tmp_path):
    # Create dummy file
    (tmp_path / "test.docx").touch()

    # We need to mock asyncio.run because typer runs sync
    with patch("asyncio.run") as mock_run:
        result = runner.invoke(app, ["process", "run", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    mock_run.assert_called_once()

def test_process_single_file_dry_run(tmp_path):
    from docx_cli.commands.process import process_single_file

    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    file_path = input_dir / "test.docx"

    success, msg = process_single_file(
        file_path, input_dir, output_dir, "md", False, True
    )

    assert success is True
    assert "Would process" in msg

@patch("docx_cli.commands.process.Cleaner")
@patch("docx_cli.commands.process.Converter")
def test_process_single_file_execution(mock_converter_cls, mock_cleaner_cls, tmp_path):
    from docx_cli.commands.process import process_single_file

    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    file_path = input_dir / "test.docx"
    file_path.touch()

    # Mock Converter
    mock_converter = mock_converter_cls.return_value
    mock_converter.convert_to_md.return_value = "# Test"

    success, msg = process_single_file(
        file_path, input_dir, output_dir, "md", True, False
    )

    assert success is True
    assert "Processed test.docx" in msg

    # Check if cleaner was called
    mock_cleaner_cls.return_value.remove_colors.assert_called_once()

    # Check if output file exists
    # Note: The actual file writing happens in the function, so we check if the mock returned content was written?
    # Wait, the function writes to file. We should check if file exists in output_dir
    # But since we mocked converter, we need to check if it wrote what converter returned.

    # The output path is dynamic (includes ID), so it's hard to predict exact path without mocking ID generation.
    # But we can check if ANY file exists in output_dir/Uncategorized
    assert len(list(output_dir.rglob("*.md"))) == 1
