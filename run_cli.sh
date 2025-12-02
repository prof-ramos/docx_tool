#!/bin/bash
# run_cli.sh - Entrypoint for the CLI

set -euo pipefail

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first."
    exit 1
fi

# Run the CLI using uv
uv run python -m docx_cli.main "$@"
