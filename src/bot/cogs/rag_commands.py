"""RAG query commands for Discord."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class RAGCommands(commands.Cog):
    """Commands for querying legal documents."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perguntar", description="Faça uma pergunta sobre legislação brasileira")
    @app_commands.describe(pergunta="Sua pergunta sobre leis e regulamentos")
    async def ask(self, interaction: discord.Interaction, pergunta: str):
        """
        Ask a question about Brazilian legislation.

        Usage: /perguntar <sua pergunta>
        """
        await interaction.response.defer(thinking=True)

        try:
            # Query RAG engine
            result = await self.bot.rag_engine.query(pergunta)

            # Build response embed
            embed = discord.Embed(
                title="📚 Resposta Legal",
                description=result["answer"],
                color=discord.Color.blue()
            )

            # Add confidence
            confidence_emoji = "🟢" if result["confidence"] > 0.8 else "🟡" if result["confidence"] > 0.6 else "🔴"
            embed.add_field(
                name="Confiança",
                value=f"{confidence_emoji} {result['confidence']:.1%}",
                inline=True
            )

            # Add sources
            if result["sources"]:
                sources_text = "\n".join([
                    f"• **{src['title']}** ({src['similarity']:.1%})"
                    for src in result["sources"][:3]
                ])
                embed.add_field(
                    name="📄 Fontes",
                    value=sources_text,
                    inline=False
                )

            embed.set_footer(text="⚠️ Sempre consulte um advogado para casos específicos")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro",
                description=f"Ocorreu um erro ao processar sua pergunta:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="buscar", description="Busca documentos legais por palavras-chave")
    @app_commands.describe(
        palavras_chave="Palavras-chave para buscar",
        limite="Número de resultados (máx 10)"
    )
    async def search(
        self,
        interaction: discord.Interaction,
        palavras_chave: str,
        limite: Optional[int] = 5
    ):
        """
        Search legal documents by keywords.

        Usage: /buscar <palavras-chave> [limite]
        """
        await interaction.response.defer(thinking=True)

        try:
            # Limit results
            limite = min(limite, 10)

            # Search documents
            docs = await self.bot.rag_engine.search_documents(
                palavras_chave,
                top_k=limite,
                threshold=0.5
            )

            if not docs:
                embed = discord.Embed(
                    title="🔍 Busca",
                    description="Nenhum documento encontrado com essas palavras-chave.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return

            # Build results embed
            embed = discord.Embed(
                title=f"🔍 Resultados para: {palavras_chave}",
                description=f"Encontrados {len(docs)} documentos relevantes:",
                color=discord.Color.green()
            )

            for i, doc in enumerate(docs, 1):
                title = doc.get('metadata', {}).get('title', 'Documento sem título')
                similarity = doc.get('similarity', 0.0)
                content = doc.get('content', '')[:150]

                embed.add_field(
                    name=f"{i}. {title} ({similarity:.1%})",
                    value=f"```{content}...```",
                    inline=False
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro na busca:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @commands.command(name="ajuda_legal")
    async def help_legal(self, ctx):
        """Show help for legal commands."""
        embed = discord.Embed(
            title="📚 Comandos de Consulta Legal",
            description="Use estes comandos para consultar a legislação brasileira:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="/perguntar <pergunta>",
            value="Faça uma pergunta sobre legislação e receba uma resposta com fontes",
            inline=False
        )

        embed.add_field(
            name="/buscar <palavras-chave> [limite]",
            value="Busca documentos legais por palavras-chave",
            inline=False
        )

        embed.add_field(
            name="Exemplos",
            value=(
                "• `/perguntar O que é desapropriação por utilidade pública?`\n"
                "• `/buscar licitações 3`\n"
                "• `/perguntar Quais são os tipos de licitação?`"
            ),
            inline=False
        )

        embed.set_footer(text="⚠️ Este bot fornece informações gerais, não substitui consulta jurídica")

        await ctx.send(embed=embed)

async def setup(bot):
    """Load the cog."""
    await bot.add_cog(RAGCommands(bot))
