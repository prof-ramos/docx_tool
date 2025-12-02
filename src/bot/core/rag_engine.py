"""RAG Engine for document retrieval and generation."""
import os
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
from rich.console import Console

console = Console()

class RAGEngine:
    """Retrieval-Augmented Generation engine using Supabase + OpenAI."""

    def __init__(self):
        self.supabase: Optional[Client] = None
        self.openai_client = None
        self.collection_name = "legal_documents"

    async def initialize(self):
        """Initialize connections to Supabase and OpenAI."""
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

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = await self.openai_client.Embedding.acreate(
                model="text-embedding-3-small",
                input=text
            )
            return response['data'][0]['embedding']
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

    async def query(self, question: str) -> Dict:
        """
        Main RAG query method.

        Args:
            question: User's question

        Returns:
            Dict with response and sources
        """
        # 1. Search relevant documents
        docs = await self.search_documents(question, top_k=5)

        if not docs:
            return {
                "answer": "Desculpe, não encontrei documentos relevantes para responder sua pergunta.",
                "sources": [],
                "confidence": 0.0
            }

        # 2. Generate response
        answer = await self.generate_response(question, docs)

        # 3. Extract sources
        sources = [
            {
                "title": doc.get('metadata', {}).get('title', 'Documento'),
                "similarity": doc.get('similarity', 0.0),
                "excerpt": doc.get('content', '')[:200] + "..."
            }
            for doc in docs
        ]

        return {
            "answer": answer,
            "sources": sources,
            "confidence": docs[0].get('similarity', 0.0) if docs else 0.0
        }
