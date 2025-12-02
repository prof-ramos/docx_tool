# CLAUDE.md

This file provides guidance to Claude Code when working with this Discord Bot + RAG project.

## Project Overview

This is a **Discord Bot with RAG (Retrieval-Augmented Generation)** for querying Brazilian legal documents.

### Architecture
```
User Question (Discord)
         ↓
  Discord Bot (discord.py)
         ↓
   RAG Engine (OpenAI + Supabase)
         ↓
  Vector Search (pgvector)
         ↓
   LLM Response (GPT-4)
         ↓
    Discord Embed
```

### Components
1. **Document Processing CLI** (`src/docx_cli/`) - Converts DOCX → Markdown
2. **Discord Bot** (`src/bot/`) - Handles user queries and admin commands
3. **RAG Engine** (`src/bot/core/`) - Vector search + LLM generation
4. **Admin Dashboard** (`src/dashboard/`) - Streamlit web interface for monitoring
5. **Supabase Vector Store** - PostgreSQL with pgvector extension

## Technology Stack

### Core Technologies
- **Python 3.14** (requires 3.11+)
- **UV** - Modern package manager
- **discord.py** - Discord bot framework
- **OpenAI API** - Embeddings (text-embedding-3-small) + Generation (GPT-4o-mini)
- **Supabase** - Vector database (PostgreSQL + pgvector)
- **Typer** - CLI framework
- **Streamlit** - Admin dashboard
- **Docling** - Document conversion (DOCX → Markdown)

### Key Dependencies
```toml
discord.py = ">=2.3.0"
openai = ">=1.0.0"
supabase = ">=2.0.0"
typer[all] = ">=0.9.0"
streamlit = ">=1.28.0"
docling = ">=1.0.0"
python-docx = ">=1.0.0"
pydantic = ">=2.0.0"
rich = ">=13.0.0"
psutil = ">=5.9.0"
```

## Project Structure

```
legal-bot/
├── src/
│   ├── bot/                      # Discord bot
│   │   ├── main.py              # Bot entry point
│   │   ├── cogs/                # Command handlers
│   │   │   ├── rag_commands.py  # /perguntar, /buscar
│   │   │   └── admin_commands.py # /status, /sync, /reload_rag
│   │   └── core/                # Core logic
│   │       ├── rag_engine.py    # RAG implementation
│   │       └── ingestion.py     # Document → Vector DB pipeline
│   ├── docx_cli/                # Document processing
│   │   ├── main.py              # CLI entry point
│   │   ├── commands/
│   │   │   └── process.py       # Batch processing
│   │   └── core/
│   │       ├── converter.py     # DOCX → Markdown
│   │       ├── normalizer.py    # Text normalization
│   │       └── cleaner.py       # Remove formatting
│   └── dashboard/               # Admin interface
│       └── admin.py             # Streamlit dashboard
├── supabase/
│   └── migrations/
│       └── 001_create_documents_table.sql
├── Administrativo/              # Input: Legal DOCX files
├── Output/                      # Processed Markdown files
├── pyproject.toml               # Project config
├── .env                         # Environment variables
└── run_*.sh                     # Launcher scripts
```

## Development Workflow

### 1. Setup Environment
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Database Setup
```bash
# Run Supabase migration
# (Use Supabase dashboard or CLI)
psql $DATABASE_URL < supabase/migrations/001_create_documents_table.sql
```

### 3. Process Documents
```bash
# Convert DOCX to Markdown
uv run python -m docx_cli.main process Administrativo --output-dir Output --format md

# Or use shortcut
./run_cli.sh process
```

### 4. Ingest Documents to Vector DB
```bash
# Ingest processed Markdown files
uv run python -m src.bot.core.ingestion Output

# This will:
# 1. Chunk documents (1000 chars with 200 overlap)
# 2. Generate embeddings (OpenAI text-embedding-3-small)
# 3. Store in Supabase with metadata
```

### 5. Run Discord Bot
```bash
# Start bot
uv run python -m src.bot.main

# Or use shortcut
./run_bot.sh
```

### 6. Run Admin Dashboard
```bash
# Start Streamlit dashboard
uv run streamlit run src/dashboard/admin.py

# Or use shortcut
./run_dashboard.sh
```

## Discord Bot Commands

### User Commands (Slash Commands)
- `/perguntar <pergunta>` - Ask a question about Brazilian legislation
- `/buscar <palavras-chave> [limite]` - Search documents by keywords
- `!ajuda_legal` - Show help

### Admin Commands (Requires admin permissions)
- `/status` - Show bot and system status
- `/sync` - Sync slash commands
- `/reload_rag` - Reload RAG engine
- `/stats` - Show usage statistics
- `!ping` - Check bot latency

### Examples
```
/perguntar O que é desapropriação por utilidade pública?
/buscar licitações 5
/perguntar Quais são os requisitos para processo administrativo?
```

## RAG Pipeline

### Document Ingestion
1. **Read Markdown** from Output/
2. **Chunk Text** (1000 chars, 200 overlap)
3. **Generate Embeddings** (OpenAI text-embedding-3-small, 1536 dims)
4. **Store in Supabase** with metadata

### Query Flow
1. User asks question via Discord
2. Generate query embedding
3. Vector similarity search (pgvector cosine similarity)
4. Retrieve top-k documents (default: 5, threshold: 0.7)
5. Build context from retrieved docs
6. Generate response using GPT-4o-mini
7. Return formatted embed with sources

### Configuration
```python
# RAG Engine settings
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions
GENERATION_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200
TOP_K = 5  # results per query
SIMILARITY_THRESHOLD = 0.7  # 0.0-1.0
```

## Environment Variables

Required in `.env`:
```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Optional: OpenRouter (alternative to OpenAI)
OPENROUTER_API_KEY=sk-or-v1-...
```

## Admin Dashboard Features

Streamlit dashboard at `src/dashboard/admin.py`:

- **Dashboard** - Real-time statistics, document counts, source breakdown
- **Documents** - Browse and search ingested documents
- **Search** - Test vector search functionality
- **Settings** - Check environment variables, test connections, trigger ingestion

## Coding Guidelines

### Discord Bot Patterns

**Slash Command (Cog):**
```python
from discord import app_commands
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mycommand", description="Description")
    @app_commands.describe(param="Parameter description")
    async def my_command(self, interaction: discord.Interaction, param: str):
        await interaction.response.defer(thinking=True)
        # Process...
        await interaction.followup.send("Response")
```

**Embed Response:**
```python
embed = discord.Embed(
    title="Title",
    description="Description",
    color=discord.Color.blue()
)
embed.add_field(name="Field", value="Value", inline=True)
await interaction.followup.send(embed=embed)
```

### RAG Engine Patterns

**Vector Search:**
```python
# In rag_engine.py
docs = await self.search_documents(query, top_k=5, threshold=0.7)
```

**Generate Response:**
```python
answer = await self.generate_response(question, context_docs)
```

**Full Query:**
```python
result = await self.bot.rag_engine.query(question)
# Returns: {"answer": str, "sources": list, "confidence": float}
```

### Ingestion Patterns

**Ingest Single File:**
```python
from src.bot.core.ingestion import DocumentIngestionPipeline

pipeline = DocumentIngestionPipeline()
await pipeline.initialize()
chunks_inserted = await pipeline.ingest_document(file_path)
```

**Ingest Directory:**
```python
stats = await pipeline.ingest_directory(directory, pattern="*.md")
```

## Testing

### Manual Testing
```bash
# Test document processing
./run_cli.sh process Administrativo --dry-run

# Test ingestion (dry run not available, use small dataset)
uv run python -m src.bot.core.ingestion Output --pattern "lei_9784*.md"

# Test bot locally
uv run python -m src.bot.main
# Then use Discord to test commands
```

### Unit Tests (TODO)
```bash
pytest tests/
pytest tests/test_rag_engine.py -v
pytest --cov=src --cov-report=html
```

## Common Tasks

### Add New Discord Command
1. Edit `src/bot/cogs/rag_commands.py` or `admin_commands.py`
2. Add `@app_commands.command()` method
3. Restart bot
4. Run `/sync` in Discord to register command

### Update RAG Model
1. Edit `src/bot/core/rag_engine.py`
2. Change `EMBEDDING_MODEL` or `GENERATION_MODEL`
3. Re-ingest documents if embedding model changed
4. Reload with `/reload_rag`

### Add Document Source
1. Place DOCX files in `Administrativo/` or new folder
2. Run `./run_cli.sh process <folder>`
3. Run ingestion: `uv run python -m src.bot.core.ingestion Output`

### Monitor Bot Performance
1. Open dashboard: `./run_dashboard.sh`
2. Check Discord: `/status`
3. View Supabase dashboard for query stats

## Troubleshooting

### Bot Not Responding
```bash
# Check bot is running
ps aux | grep "src.bot.main"

# Check Discord token
echo $DISCORD_TOKEN

# Check logs
uv run python -m src.bot.main
```

### RAG Not Finding Documents
```bash
# Check Supabase connection
uv run python -c "from supabase import create_client; import os; print(create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')).table('documents').select('count').execute())"

# Check if documents are ingested
# Use admin dashboard or:
psql $DATABASE_URL -c "SELECT COUNT(*) FROM documents;"
```

### Embeddings Failing
```bash
# Test OpenAI connection
uv run python -c "import openai; import os; openai.api_key = os.getenv('OPENAI_API_KEY'); print(openai.Model.list())"

# Check API key has embeddings access
```

### Dashboard Not Loading
```bash
# Check Supabase RLS policies
# Ensure anon key has SELECT access to documents table

# Test in Python:
from supabase import create_client
import os
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
print(supabase.table("documents").select("count").execute())
```

## Important Notes

### Document Processing
- Input: Brazilian legal documents (DOCX)
- Processing: Removes formatting, converts to Markdown, normalizes names
- Output: Clean Markdown files in Output/

### Vector Storage
- Uses Supabase pgvector extension
- Embeddings: OpenAI text-embedding-3-small (1536 dims)
- Similarity: Cosine similarity
- Indexing: IVFFlat with 100 lists

### Rate Limits
- OpenAI: 500 RPM (embeddings), 200 RPM (chat)
- Discord: 50 slash commands per second
- Supabase: Depends on plan

### Security
- Use SERVICE_ROLE_KEY for ingestion (bypasses RLS)
- Use ANON_KEY for dashboard (respects RLS)
- Never commit .env to git
- Discord token in .env only

## Resources

- **discord.py docs:** https://discordpy.readthedocs.io
- **OpenAI API:** https://platform.openai.com/docs
- **Supabase Vector:** https://supabase.com/docs/guides/ai
- **Docling:** https://github.com/DS4SD/docling
- **UV:** https://github.com/astral-sh/uv

## Quick Reference

```bash
# Process documents
./run_cli.sh process

# Ingest to vector DB
uv run python -m src.bot.core.ingestion Output

# Run bot
./run_bot.sh

# Run dashboard
./run_dashboard.sh

# Apply Supabase migration
psql $DATABASE_URL < supabase/migrations/001_create_documents_table.sql
```
