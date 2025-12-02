#!/bin/bash
# run_dashboard.sh - Start Admin Dashboard

set -euo pipefail

echo "📊 Starting Admin Dashboard..."

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    exit 1
fi

# Run dashboard
uv run streamlit run src/dashboard/admin.py
