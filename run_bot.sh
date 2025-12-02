#!/bin/bash
# run_bot.sh - Start Discord bot

set -euo pipefail

echo "🤖 Starting Legal Bot..."

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run bot
uv run python -m src.bot.main
