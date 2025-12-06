"""RAG Engine for document retrieval and generation."""
import os
import hashlib
import asyncio
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
from rich.console import Console
from .cache_manager import CacheManager

console = Console()

class RAGEngine:
    """Retrieval-Augmented Generation engine using Supabase + OpenAI."""

    def __init__(self, enable_cache: bool = True):
        self.supabase: Optional[Client] = None
        self.openai_client = None
        self.collection_name = "legal_documents"
        self._cache_save_task = None

        # Initialize cache manager
        self.cache_enabled = enable_cache
        if enable_cache:
            self.cache = CacheManager(
                embedding_ttl=86400 * 7,  # 7 days for embeddings
                response_ttl=3600,  # 1 hour for responses
                enable_persistence=True
            )
            console.print("[green]✓ Cache enabled[/green]")
        else:
            self.cache = None
            console.print("[yellow]⚠ Cache disabled[/yellow]")

    async def initialize(self):
        """Initialize connections to Supabase and OpenAI."""
        # Load cache asynchronously
        if self.cache_enabled:
            console.print("[blue]ℹ Loading cache...[/blue]")
            await self.cache.load_async()

        # Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            console.print("[red]✗ Supabase credentials missing![/red]")
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

        self.supabase = create_client(supabase_url, supabase_key)
        console.print("[green]✓ Connected to Supabase[/green]")

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            console.print("[red]✗ OpenAI API key missing![/red]")
            raise ValueError("Missing OPENAI_API_KEY")

        openai.api_key = openai_key
        self.openai_client = openai
        console.print("[green]✓ Connected to OpenAI[/green]")

        # Start periodic cache saving (every 5 minutes)
        if self.cache_enabled and self.cache.enable_persistence:
            self._start_periodic_save()

    def _start_periodic_save(self):
        """Start background task for periodic cache saving."""
        async def save_loop():
            while True:
                await asyncio.sleep(300)  # 5 minutes
                if self.cache:
                    await self.cache.save_async()

        self._cache_save_task = asyncio.create_task(save_loop())

    async def shutdown(self):
        """Gracefully shutdown the engine."""
        if self._cache_save_task:
            self._cache_save_task.cancel()
            try:
                await self._cache_save_task
            except asyncio.CancelledError:
                pass

        if self.cache_enabled:
            console.print("[blue]ℹ Saving cache before shutdown...[/blue]")
            await self.cache.save_async()

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Uses cache to avoid redundant API calls.

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

    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for relevant documents using vector similarity.

        Args:
            query: User query text
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of matching documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)

            # Search in Supabase using pgvector
            result = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': top_k
                }
            ).execute()

            return result.data if result.data else []

        except Exception as e:
            console.print(f"[red]✗ Search error: {e}[/red]")
            return []

    async def generate_response(
        self,
        query: str,
        context_docs: List[Dict],
        model: str = "gpt-4o-mini"
    ) -> str:
        """
        Generate response using retrieved context.

        Args:
            query: User's question
            context_docs: Retrieved documents
            model: OpenAI model to use

        Returns:
            Generated response
        """
        # Build context from documents
        context_parts = []
        for doc in context_docs:
            title = doc.get('metadata', {}).get('title', 'Documento')
            content = doc.get('content', '')
            context_parts.append(f"**{title}**:\n{content}")

        context = "\n\n---\n\n".join(context_parts)

        # System prompt
        system_prompt = """Você é um assistente especializado em legislação brasileira.
Responda perguntas com base APENAS nos documentos fornecidos.
Seja preciso, cite artigos e leis quando relevante.
Se a informação não estiver nos documentos, diga claramente."""

        # User prompt
        user_prompt = f"""Contexto dos documentos legais:

{context}

---

Pergunta do usuário: {query}

Responda de forma clara e objetiva, citando os documentos quando necessário."""

        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            console.print(f"[red]✗ Generation error: {e}[/red]")
            return f"Erro ao gerar resposta: {str(e)}"

    def _hash_context(self, docs: List[Dict]) -> str:
        """
        Create hash of document context for caching.

        Args:
            docs: List of retrieved documents

        Returns:
            Hash of document IDs and similarity scores
        """
        # Create deterministic representation of context
        context_repr = "|".join([
            f"{doc.get('id', '')}:{doc.get('similarity', 0.0):.4f}"
            for doc in docs
        ])
        return hashlib.sha256(context_repr.encode('utf-8')).hexdigest()

    async def query(self, question: str) -> Dict:
        """
        Main RAG query method.

        Uses cache for both embeddings and complete responses.

        Args:
            question: User's question

        Returns:
            Dict with response and sources
        """
        # 1. Search relevant documents (uses embedding cache internally)
        docs = await self.search_documents(question, top_k=5)

        if not docs:
            return {
                "answer": "Desculpe, não encontrei documentos relevantes para responder sua pergunta.",
                "sources": [],
                "confidence": 0.0
            }

        # 2. Check response cache
        context_hash = self._hash_context(docs)
        if self.cache_enabled:
            cached_response = self.cache.get_response(question, context_hash)
            if cached_response is not None:
                return cached_response

        # 3. Generate response
        answer = await self.generate_response(question, docs)

        # 4. Extract sources
        sources = [
            {
                "title": doc.get('metadata', {}).get('title', 'Documento'),
                "similarity": doc.get('similarity', 0.0),
                "excerpt": doc.get('content', '')[:200] + "..."
            }
            for doc in docs
        ]

        # 5. Build result
        result = {
            "answer": answer,
            "sources": sources,
            "confidence": docs[0].get('similarity', 0.0) if docs else 0.0
        }

        # 6. Cache the response
        if self.cache_enabled:
            self.cache.set_response(question, result, context_hash)

        return result

    def get_cache_stats(self) -> Optional[Dict]:
        """
        Get cache statistics.

        Returns:
            Cache stats dict or None if cache disabled
        """
        if self.cache_enabled:
            return self.cache.get_stats()
        return None

    def clear_cache(self, cache_type: str = "all"):
        """
        Clear cache.

        Args:
            cache_type: "embeddings", "responses", or "all"
        """
        if not self.cache_enabled:
            console.print("[yellow]⚠ Cache is disabled[/yellow]")
            return

        if cache_type == "embeddings":
            self.cache.clear_embeddings()
        elif cache_type == "responses":
            self.cache.clear_responses()
        elif cache_type == "all":
            self.cache.clear_all()
        else:
            console.print(f"[red]✗ Invalid cache type: {cache_type}[/red]")
