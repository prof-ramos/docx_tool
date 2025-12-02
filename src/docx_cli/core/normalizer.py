"""Filename normalization logic."""
import unicodedata
import re

def to_snake_case(name: str) -> str:
    """
    Converts a string to snake_case.

    Args:
        name: The string to convert.

    Returns:
        The converted snake_case string.
    """
    # Normalize unicode characters
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')

    # Convert to lowercase
    name = name.lower()

    # Replace non-alphanumeric characters with underscores
    name = re.sub(r'[^a-z0-9]', '_', name)

    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)

    # Strip leading/trailing underscores
    return name.strip('_')
