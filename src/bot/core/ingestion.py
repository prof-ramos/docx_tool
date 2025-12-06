"""Document ingestion pipeline for RAG."""
import os
import asyncio
from pathlib import Path
from typing import List, Dict
import openai
from supabase import create_client, Client
from rich.console import Console
from rich.progress import track
import hashlib
from .cache_manager import CacheManager

console = Console()

class DocumentIngestionPipeline:
    """Pipeline to ingest processed documents into Supabase vector store."""

    def __init__(self, enable_cache: bool = True):
        self.supabase: Client = None
        self.openai_client = None
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200

        # Initialize cache manager
        self.cache_enabled = enable_cache
        if enable_cache:
            self.cache = CacheManager(
                embedding_ttl=0,  # No expiration for document embeddings
                response_ttl=0,  # Not used in ingestion
                enable_persistence=True
            )
        else:
            self.cache = None

    async def initialize(self):
        """Initialize connections."""
        # Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials")

        self.supabase = create_client(supabase_url, supabase_key)
        console.print("[green]✓ Connected to Supabase[/green]")

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("Missing OPENAI_API_KEY")

        openai.api_key = openai_key
        self.openai_client = openai
        console.print("[green]✓ Connected to OpenAI[/green]")

    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full document text
            metadata: Document metadata

        Returns:
            List of chunks with metadata
        """
        chunks = []
        text_length = len(text)

        start = 0
        chunk_index = 0

        while start < text_length:
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence end
                sentence_end = text.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index": chunk_index,
                        "start_char": start,
                        "end_char": end
                    }
                })

            chunk_index += 1
            start = end - self.chunk_overlap

        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Uses cache to avoid redundant API calls for duplicate content.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache first
        if self.cache_enabled:
            cached_embedding = self.cache.get_embedding(text)
            if cached_embedding is not None:
                return cached_embedding

        # Generate new embedding
        try:
            response = await self.openai_client.Embedding.acreate(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response['data'][0]['embedding']

            # Cache the result
            if self.cache_enabled:
                self.cache.set_embedding(text, embedding)

            return embedding

        except Exception as e:
            console.print(f"[red]✗ Embedding error: {e}[/red]")
            raise

    def generate_document_id(self, file_path: Path, chunk_index: int = 0) -> str:
        """Generate unique ID for document chunk."""
        content = f"{file_path.stem}_{chunk_index}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def ingest_document(self, file_path: Path) -> int:
        """
        Ingest a single Markdown document.

        Args:
            file_path: Path to .md file

        Returns:
            Number of chunks inserted
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                console.print(f"[yellow]⚠ Skipping empty file: {file_path.name}[/yellow]")
                return 0

            # Extract metadata from file path
            metadata = {
                "title": file_path.stem.replace('_', ' ').title(),
                "file_name": file_path.name,
                "file_path": str(file_path),
                "source": "Administrativo"
            }

            # Chunk document
            chunks = self.chunk_text(content, metadata)

            if not chunks:
                return 0

            # Process each chunk
            inserted_count = 0
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = await self.generate_embedding(chunk["content"])

                    # Generate unique ID
                    doc_id = self.generate_document_id(file_path, chunk["metadata"]["chunk_index"])

                    # Insert into Supabase
                    data = {
                        "id": doc_id,
                        "content": chunk["content"],
                        "metadata": chunk["metadata"],
                        "embedding": embedding
                    }

                    self.supabase.table("documents").upsert(data).execute()
                    inserted_count += 1

                except Exception as e:
                    console.print(f"[red]✗ Error processing chunk: {e}[/red]")
                    continue

            console.print(f"[green]✓ Ingested {file_path.name}: {inserted_count} chunks[/green]")
            return inserted_count

        except Exception as e:
            console.print(f"[red]✗ Error ingesting {file_path.name}: {e}[/red]")
            return 0

    async def ingest_directory(self, directory: Path, pattern: str = "*.md") -> Dict:
        """
        Ingest all documents in a directory.

        Args:
            directory: Directory containing documents
            pattern: File pattern to match

        Returns:
            Statistics about ingestion
        """
        files = list(directory.rglob(pattern))

        if not files:
            console.print(f"[yellow]⚠ No files found matching {pattern} in {directory}[/yellow]")
            return {"total_files": 0, "total_chunks": 0, "errors": 0}

        console.print(f"[cyan]📄 Found {len(files)} files to ingest[/cyan]")

        total_chunks = 0
        errors = 0

        for file_path in track(files, description="Ingesting documents..."):
            try:
                chunks = await self.ingest_document(file_path)
                total_chunks += chunks
            except Exception as e:
                console.print(f"[red]✗ Error with {file_path.name}: {e}[/red]")
                errors += 1

        # Summary
        stats = {
            "total_files": len(files),
            "total_chunks": total_chunks,
            "errors": errors,
            "success_rate": (len(files) - errors) / len(files) if files else 0
        }

        console.print("\n[bold cyan]═══ Ingestion Complete ═══[/bold cyan]")
        console.print(f"[green]✓ Files processed: {stats['total_files']}[/green]")
        console.print(f"[green]✓ Chunks created: {stats['total_chunks']}[/green]")
        console.print(f"[yellow]⚠ Errors: {stats['errors']}[/yellow]")
        console.print(f"[blue]Success rate: {stats['success_rate']:.1%}[/blue]")

        # Show cache statistics
        if self.cache_enabled:
            cache_stats = self.cache.get_stats()
            emb_stats = cache_stats['embeddings']
            console.print(f"\n[bold cyan]Cache Performance:[/bold cyan]")
            console.print(f"[green]✓ Cache hits: {emb_stats['hits']}[/green]")
            console.print(f"[yellow]○ Cache misses: {emb_stats['misses']}[/yellow]")
            console.print(f"[blue]Hit rate: {emb_stats['hit_rate']:.1%}[/blue]")
            console.print(f"[cyan]Cached embeddings: {emb_stats['size']}[/cyan]")

            # Calculate API call savings
            if emb_stats['hits'] > 0:
                api_calls_saved = emb_stats['hits']
                cost_saved = api_calls_saved * 0.00002  # Approximate cost per embedding
                console.print(f"[green]💰 Estimated API calls saved: {api_calls_saved}[/green]")
                console.print(f"[green]💰 Estimated cost saved: ${cost_saved:.4f}[/green]")

        return stats


async def main():
    """CLI entrypoint for document ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing processed Markdown files"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.md",
        help="File pattern to match (default: *.md)"
    )

    args = parser.parse_args()

    if not args.directory.exists():
        console.print(f"[red]✗ Directory not found: {args.directory}[/red]")
        return

    # Initialize pipeline
    pipeline = DocumentIngestionPipeline()
    await pipeline.initialize()

    # Ingest documents
    await pipeline.ingest_directory(args.directory, args.pattern)


if __name__ == "__main__":
    asyncio.run(main())
