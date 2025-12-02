"""Main entry point for the CLI application."""
import typer
from typing_extensions import Annotated
from .console import console
from .commands import process

app = typer.Typer(
    name="docx-cli",
    help="Professional CLI for processing DOCX files",
    add_completion=True,
    rich_markup_mode="rich",
)

app.add_typer(process.app, name="process")

@app.callback()
def callback(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show version")
    ] = False,
):
    """
    DOCX Processing Tool CLI.
    """
    if version:
        console.print("docx-cli v0.1.0", style="info")
        raise typer.Exit()

if __name__ == "__main__":
    app()
