"""Tests for core modules."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from docx_cli.core.cleaner import Cleaner
from docx_cli.core.normalizer import to_snake_case
from docx_cli.core.organizer import generate_id, get_subject_from_path, build_output_path

# --- Normalizer Tests ---
def test_to_snake_case():
    assert to_snake_case("Hello World") == "hello_world"
    assert to_snake_case("My File.docx") == "my_file_docx"
    assert to_snake_case("  TEST  ") == "test"
    assert to_snake_case("Café") == "cafe"

# --- Organizer Tests ---
def test_generate_id():
    fid = generate_id()
    assert len(fid) == 8
    assert fid.isalnum()

def test_get_subject_from_path():
    base = Path("/root")
    file = Path("/root/Admin/doc.docx")
    assert get_subject_from_path(file, base) == "Admin"

    file_root = Path("/root/doc.docx")
    assert get_subject_from_path(file_root, base) == "Geral"

def test_build_output_path():
    base = Path("/out")
    path = build_output_path(base, "Admin", "doc", "123", "md")
    assert str(path) == "/out/Admin/123_doc.md"

# --- Cleaner Tests ---
@pytest.fixture
def mock_doc():
    doc = MagicMock()

    # Mock paragraph
    p = MagicMock()
    p.runs = []
    doc.paragraphs = [p]

    # Mock table
    t = MagicMock()
    t.rows = []
    doc.tables = [t]

    return doc

@patch("docx.Document")
def test_cleaner_remove_colors(mock_document_cls, mock_doc, tmp_path):
    mock_document_cls.return_value = mock_doc

    cleaner = Cleaner()
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    # Create dummy input file
    input_path.touch()

    cleaner.remove_colors(input_path, output_path)

    mock_document_cls.assert_called_once_with(input_path)
    mock_doc.save.assert_called_once_with(output_path)

def test_cleaner_clean_run():
    cleaner = Cleaner()
    run = MagicMock()
    run.font.color.rgb = "RED"
    run.font.highlight_color = "YELLOW"

    # Mock XML element
    element = MagicMock()
    element.get_or_add_rPr.return_value.xpath.return_value = []
    run._element = element

    cleaner._clean_run(run)

    assert run.font.color.rgb is None
    assert run.font.highlight_color is None

def test_cleaner_clean_table():
    cleaner = Cleaner()
    table = MagicMock()
    row = MagicMock()
    cell = MagicMock()
    paragraph = MagicMock()
    run = MagicMock()

    table.rows = [row]
    row.cells = [cell]
    cell.paragraphs = [paragraph]
    paragraph.runs = [run]

    # Mock XML for cell shading
    cell._element.xpath.return_value = [MagicMock()]

    cleaner._clean_table(table)

    # Verify shading removal was attempted
    cell._element.xpath.assert_called()

def test_cleaner_clear_shading():
    cleaner = Cleaner()
    element = MagicMock()
    shd = MagicMock()
    element._element.xpath.return_value = [shd]

    cleaner._clear_shading(element)

    shd.getparent.return_value.remove.assert_called_once_with(shd)
