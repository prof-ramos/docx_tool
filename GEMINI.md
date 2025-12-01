# Directory Overview

This directory contains a collection of Python scripts designed for processing and managing document files, primarily Microsoft Word (`.docx`) documents. The main purpose is to automate tasks like converting documents to Markdown, cleaning up formatting, and standardizing file names.

The `Administrativo` folder contains a large corpus of Brazilian legal and administrative documents in both `.docx` and `.md` formats.

# Key Files & Scripts

*   `convert_docx.py`: This script converts `.docx` files into Markdown (`.md`). It utilizes the `docling` library. By default, it looks for files in the `Input/` directory and places the converted files in the `Output/` directory.

*   `remove_colors.py`: This script removes color and highlight formatting from the text within a `.docx` file, saving a "clean" version. It uses the `python-docx` library.

*   `rename_files.py`: This utility script renames all files within the `Administrativo` directory to a standardized `snake_case` format.

*   `Administrativo/`: A directory containing numerous legal documents. It appears to be the primary target for the file processing scripts.

*   `Input/` & `Output/`: Default directories for the `convert_docx.py` script to read source files from and write converted files to.

# Usage & Development

This project uses a Python virtual environment located in `.venv/`.

## Prerequisites

*   Python 3
*   A configured virtual environment.

## Setting up the environment

To activate the virtual environment, run:
```bash
source .venv/bin/activate
```

## Running the Scripts

The scripts are intended to be run directly from the command line.

*   **Convert DOCX to Markdown:**
    ```bash
    # Process all .docx files in the Input/ directory
    python convert_docx.py

    # Specify input and output directories
    python convert_docx.py path/to/your/docs path/to/output
    ```

*   **Remove Colors from a DOCX file:**
    The `remove_colors.py` script is currently hardcoded to process a specific file. To use it for other files, you will need to modify the script.
    ```bash
    python remove_colors.py
    ```

*   **Rename Files:**
    This script is hardcoded to run on the `Administrativo` directory.
    ```bash
    python rename_files.py
    ```
