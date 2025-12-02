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

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latência: {latency}ms")

async def setup(bot):
    """Load the cog."""
    await bot.add_cog(AdminCommands(bot))
