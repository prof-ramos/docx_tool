"""Admin commands for bot management."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import psutil
import platform

class AdminCommands(commands.Cog):
    """Administrative commands for bot management."""

    def __init__(self, bot):
        self.bot = bot

    def is_admin():
        """Check if user has admin permissions."""
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    @app_commands.command(name="status", description="Mostra status do bot e sistema")
    async def status(self, interaction: discord.Interaction):
        """Show bot and system status."""
        # System info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        embed = discord.Embed(
            title="🤖 Status do Bot",
            color=discord.Color.green()
        )

        # Bot info
        embed.add_field(
            name="🌐 Servidores",
            value=str(len(self.bot.guilds)),
            inline=True
        )

        embed.add_field(
            name="👥 Usuários",
            value=str(len(self.bot.users)),
            inline=True
        )

        embed.add_field(
            name="📶 Latência",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )

        # System info
        embed.add_field(
            name="🖥️ CPU",
            value=f"{cpu_percent}%",
            inline=True
        )

        embed.add_field(
            name="💾 Memória",
            value=f"{memory.percent}%",
            inline=True
        )

        embed.add_field(
            name="🐍 Python",
            value=platform.python_version(),
            inline=True
        )

        # RAG Engine status
        rag_status = "✅ Online" if self.bot.rag_engine else "❌ Offline"
        embed.add_field(
            name="🧠 RAG Engine",
            value=rag_status,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="[ADMIN] Sincroniza comandos slash")
    @is_admin()
    async def sync(self, interaction: discord.Interaction):
        """Sync slash commands (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            synced = await self.bot.tree.sync()
            embed = discord.Embed(
                title="✅ Comandos Sincronizados",
                description=f"Sincronizados {len(synced)} comandos slash.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro ao sincronizar:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="reload_rag", description="[ADMIN] Recarrega o RAG engine")
    @is_admin()
    async def reload_rag(self, interaction: discord.Interaction):
        """Reload RAG engine (admin only)."""
        await interaction.response.defer(ephemeral=True)

        try:
            await self.bot.rag_engine.initialize()
            embed = discord.Embed(
                title="✅ RAG Recarregado",
                description="RAG Engine reinicializado com sucesso.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro ao recarregar:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="[ADMIN] Estatísticas de uso")
    @is_admin()
    async def stats(self, interaction: discord.Interaction):
        """Show usage statistics (admin only)."""
        # TODO: Implement stats tracking
        embed = discord.Embed(
            title="📊 Estatísticas",
            description="Estatísticas ainda não implementadas.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cache_stats", description="[ADMIN] Estatísticas do cache")
    @is_admin()
    async def cache_stats(self, interaction: discord.Interaction):
        """Show cache statistics (admin only)."""
        if not self.bot.rag_engine or not self.bot.rag_engine.cache_enabled:
            embed = discord.Embed(
                title="⚠️ Cache Desabilitado",
                description="O cache está desabilitado no RAG engine.",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cache_stats = self.bot.rag_engine.get_cache_stats()

        embed = discord.Embed(
            title="📊 Estatísticas do Cache",
            color=discord.Color.blue()
        )

        # Embedding cache stats
        emb_stats = cache_stats['embeddings']
        embed.add_field(
            name="🔤 Cache de Embeddings",
            value=(
                f"**Hits:** {emb_stats['hits']}\n"
                f"**Misses:** {emb_stats['misses']}\n"
                f"**Hit Rate:** {emb_stats['hit_rate']:.1%}\n"
                f"**Tamanho:** {emb_stats['size']} entradas\n"
                f"**Evictions:** {emb_stats['evictions']}"
            ),
            inline=False
        )

        # Response cache stats
        resp_stats = cache_stats['responses']
        embed.add_field(
            name="💬 Cache de Respostas",
            value=(
                f"**Hits:** {resp_stats['hits']}\n"
                f"**Misses:** {resp_stats['misses']}\n"
                f"**Hit Rate:** {resp_stats['hit_rate']:.1%}\n"
                f"**Tamanho:** {resp_stats['size']} entradas\n"
                f"**Evictions:** {resp_stats['evictions']}"
            ),
            inline=False
        )

        # Total size
        total_size_mb = cache_stats['total_size_bytes'] / (1024 * 1024)
        embed.add_field(
            name="💾 Tamanho Total Estimado",
            value=f"{total_size_mb:.2f} MB",
            inline=False
        )

        # Calculate savings
        total_api_calls_saved = emb_stats['hits'] + (resp_stats['hits'] * 6)  # Assume 1 query = 1 embed + 1 LLM call
        embed.add_field(
            name="💰 Economia Estimada",
            value=f"~{total_api_calls_saved} chamadas de API economizadas",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear_cache", description="[ADMIN] Limpa o cache")
    @app_commands.describe(
        cache_type="Tipo de cache a limpar (embeddings, responses, all)"
    )
    @app_commands.choices(cache_type=[
        app_commands.Choice(name="Embeddings", value="embeddings"),
        app_commands.Choice(name="Respostas", value="responses"),
        app_commands.Choice(name="Tudo", value="all")
    ])
    @is_admin()
    async def clear_cache(
        self,
        interaction: discord.Interaction,
        cache_type: app_commands.Choice[str]
    ):
        """Clear cache (admin only)."""
        if not self.bot.rag_engine or not self.bot.rag_engine.cache_enabled:
            embed = discord.Embed(
                title="⚠️ Cache Desabilitado",
                description="O cache está desabilitado no RAG engine.",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get stats before clearing
            before_stats = self.bot.rag_engine.get_cache_stats()

            # Clear cache
            self.bot.rag_engine.clear_cache(cache_type.value)

            # Build response
            cache_type_name = cache_type.name
            embed = discord.Embed(
                title="✅ Cache Limpo",
                description=f"Cache de **{cache_type_name}** foi limpo com sucesso.",
                color=discord.Color.green()
            )

            # Show what was cleared
            if cache_type.value in ["embeddings", "all"]:
                emb_cleared = before_stats['embeddings']['size']
                embed.add_field(
                    name="🔤 Embeddings Removidos",
                    value=f"{emb_cleared} entradas",
                    inline=True
                )

            if cache_type.value in ["responses", "all"]:
                resp_cleared = before_stats['responses']['size']
                embed.add_field(
                    name="💬 Respostas Removidas",
                    value=f"{resp_cleared} entradas",
                    inline=True
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro",
                description=f"Erro ao limpar cache:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latência: {latency}ms")

async def setup(bot):
    """Load the cog."""
    await bot.add_cog(AdminCommands(bot))
