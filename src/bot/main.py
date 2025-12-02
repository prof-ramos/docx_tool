"""Main Discord bot entry point."""
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from rich.console import Console

from .cogs.rag_commands import RAGCommands
from .cogs.admin_commands import AdminCommands
from .core.rag_engine import RAGEngine

load_dotenv()

console = Console()

class LegalBot(commands.Bot):
    """Discord bot for legal document RAG queries."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )

        self.rag_engine = None

    async def setup_hook(self):
        """Initialize bot components."""
        console.print("[cyan]Initializing RAG Engine...[/cyan]")
        self.rag_engine = RAGEngine()
        await self.rag_engine.initialize()

        # Load cogs
        await self.add_cog(RAGCommands(self))
        await self.add_cog(AdminCommands(self))

        console.print("[green]✓ Bot ready![/green]")

    async def on_ready(self):
        """Called when bot is ready."""
        console.print(f"[green]✓ Logged in as {self.user}[/green]")
        console.print(f"[cyan]Servers: {len(self.guilds)}[/cyan]")

        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="documentos legais 📚"
            )
        )

def run_bot():
    """Start the Discord bot."""
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        console.print("[red]✗ DISCORD_TOKEN not found in .env[/red]")
        return

    bot = LegalBot()
    bot.run(token)

if __name__ == "__main__":
    run_bot()
