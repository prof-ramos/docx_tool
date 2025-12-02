#!/bin/bash
# run_ingestion.sh - Ingest processed documents to Supabase

set -euo pipefail

# Default directory
DIRECTORY="${1:-Output}"
PATTERN="${2:-*.md}"

echo "📥 Starting document ingestion..."
echo "Directory: $DIRECTORY"
echo "Pattern: $PATTERN"

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check directory exists
if [ ! -d "$DIRECTORY" ]; then
    echo "❌ Error: Directory not found: $DIRECTORY"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    exit 1
fi

# Run ingestion
uv run python -m src.bot.core.ingestion "$DIRECTORY" --pattern "$PATTERN"
