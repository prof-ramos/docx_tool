"""Process command."""
import asyncio
import json
import shutil
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Tuple, Optional

import typer
from typing_extensions import Annotated
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from ..console import console
from ..config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
from ..core.normalizer import to_snake_case
from ..core.organizer import generate_id, get_subject_from_path, build_output_path
from ..core.converter import Converter
from ..core.cleaner import Cleaner

app = typer.Typer(help="Batch process DOCX files.")

# Standalone function for pickling support in ProcessPoolExecutor
def process_single_file(
    file_path: Path,
    input_dir: Path,
    output_dir: Path,
    output_format: str,
    clean: bool,
    dry_run: bool
) -> Tuple[bool, str]:
    """
    Processes a single file: Normalize -> Clean -> Convert.
    Returns (success, message).
    """
    try:
        # 1. Analyze
        filename = file_path.name
        subject = get_subject_from_path(file_path, input_dir)
        file_id = generate_id()

        # 2. Normalize
        name_stem = file_path.stem
        normalized_name = to_snake_case(name_stem)

        # 3. Determine Output Path
        ext = output_format
        final_path = build_output_path(output_dir, subject, normalized_name, file_id, ext)

        if dry_run:
            return True, f"[dim]Would process: {filename} -> {final_path}[/dim]"

        # Create directory
        final_path.parent.mkdir(parents=True, exist_ok=True)

        # Work on a temporary copy or the original?
        # If cleaning, we need a temp file.
        working_path = file_path
        temp_clean_path = None

        if clean:
            # Create a temp file for the cleaned version
            # We use the final directory but with a temp suffix to avoid collisions
            temp_clean_path = final_path.parent / f"{normalized_name}_{file_id}_clean.docx"
            cleaner = Cleaner()
            cleaner.remove_colors(file_path, temp_clean_path)
            working_path = temp_clean_path

        # 4. Convert
        converter = Converter()
        if output_format == "md":
            content = converter.convert_to_md(working_path)
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            content = converter.convert_to_json(working_path)
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

        # Cleanup temp file
        if temp_clean_path and temp_clean_path.exists():
            os.remove(temp_clean_path)

        return True, f"Processed {filename}"

    except Exception as e:
        return False, f"Error processing {file_path.name}: {str(e)}"

async def run_parallel(
    files: list[Path],
    input_dir: Path,
    output_dir: Path,
    output_format: str,
    clean: bool,
    dry_run: bool
):
    """Runs processing in parallel using ProcessPoolExecutor."""

    loop = asyncio.get_running_loop()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[cyan]Processing...", total=len(files))

        success_count = 0
        error_count = 0

        # Create executor
        # Limit workers to avoid OOM with heavy ML models in docling
        max_workers = min(os.cpu_count() or 1, 4)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for file_path in files:
                # Submit task
                future = loop.run_in_executor(
                    executor,
                    process_single_file,
                    file_path,
                    input_dir,
                    output_dir,
                    output_format,
                    clean,
                    dry_run
                )
                futures.append(future)

            # Wait for results
            for future in asyncio.as_completed(futures):
                success, msg = await future
                if success:
                    success_count += 1
                    if dry_run:
                        console.print(msg)
                else:
                    error_count += 1
                    console.print(f"❌ {msg}", style="error")

                progress.advance(task_id)

    # Summary
    console.print("---")
    if error_count == 0:
        console.print(f"✅ Completed successfully! Processed {success_count} files.", style="success")
    else:
        console.print(f"⚠️ Completed with errors. Success: {success_count}, Errors: {error_count}", style="warning")


@app.command()
def run(
    input_dir: Annotated[
        Path,
        typer.Argument(
            help="Directory containing DOCX files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        )
    ] = DEFAULT_INPUT_DIR,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Directory to save processed files",
            file_okay=False,
            dir_okay=True,
            writable=True,
        )
    ] = DEFAULT_OUTPUT_DIR,
    output_format: Annotated[
        str,
        typer.Option(
            "--format", "-f",
            help="Output format (md or json)",
            case_sensitive=False,
        )
    ] = "md",
    clean: Annotated[
        bool,
        typer.Option(
            "--clean",
            help="Remove colors and highlights before processing",
        )
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simulate processing without writing files",
        )
    ] = False,
):
    """
    Batch process DOCX files: Normalize, Organize, and Convert.
    """
    # Validate format
    if output_format not in ["md", "json"]:
        console.print(f"❌ Invalid format: {output_format}. Use 'md' or 'json'.", style="error")
        raise typer.Exit(code=1)

    # Find files
    console.print(f"🔎 Scanning [bold]{input_dir}[/bold]...", style="info")
    files = list(input_dir.rglob("*.docx"))

    if not files:
        console.print("⚠️ No .docx files found.", style="warning")
        raise typer.Exit()

    console.print(f"📄 Found [bold]{len(files)}[/bold] files.", style="info")

    # Run async loop
    asyncio.run(run_parallel(files, input_dir, output_dir, output_format, clean, dry_run))
