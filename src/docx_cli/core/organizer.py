"""File organization and ID generation logic."""
import uuid
from pathlib import Path
from datetime import datetime

def generate_id() -> str:
    """Generates a unique short ID."""
    # Using first 8 chars of UUID for brevity but reasonable uniqueness
    return str(uuid.uuid4())[:8]

def get_subject_from_path(file_path: Path, root_dir: Path) -> str:
    """
    Extracts the subject (materia) from the file path relative to root.

    Args:
        file_path: The full path to the file.
        root_dir: The root directory being scanned.

    Returns:
        The subject name (directory name).
    """
    try:
        # Get path relative to the input root
        rel_path = file_path.relative_to(root_dir)
        # The first part of the relative path is the subject folder
        # If the file is in root, use 'General' or similar
        if len(rel_path.parts) > 1:
            return rel_path.parts[0]
        return "Geral"
    except ValueError:
        return "Unknown"

def build_output_path(
    output_dir: Path,
    subject: str,
    normalized_name: str,
    file_id: str,
    extension: str
) -> Path:
    """
    Constructs the final output path.

    Format: output_dir / subject / {id}_{normalized_name}.{extension}
    """
    filename = f"{file_id}_{normalized_name}.{extension}"
    return output_dir / subject / filename
