"""Document conversion logic."""
from pathlib import Path
from docling.document_converter import DocumentConverter

class Converter:
    """Handles document conversion."""

    def __init__(self):
        self.converter = DocumentConverter()

    def convert_to_md(self, file_path: Path) -> str:
        """
        Converts a document to Markdown.

        Args:
            file_path: Path to the input file.

        Returns:
            The markdown content as a string.
        """
        result = self.converter.convert(file_path)
        return result.document.export_to_markdown()

    def convert_to_json(self, file_path: Path) -> dict:
        """
        Converts a document to JSON.

        Args:
            file_path: Path to the input file.

        Returns:
            The JSON content as a dict.
        """
        result = self.converter.convert(file_path)
        return result.document.export_to_dict()
