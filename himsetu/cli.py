"""Interactive Command-Line Interface (CLI) & Server Runner for HIMSETU.

Provides a rich terminal REPL interacting directly with HimSetuEngine,
as well as a command runner for the FastAPI REST server.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional
from colorama import Fore, Style, init as colorama_init
from rich.console import Console
from rich.panel import Panel

from himsetu.engine import HimSetuEngine, EngineState
from himsetu.config import load_config

colorama_init(autoreset=True)
console = Console()


def print_banner(engine: HimSetuEngine) -> None:
    """Render startup banner and welcome header."""
    st = engine.status()
    banner_text = (
        f"[bold cyan]HIMSETU Core Engine[/bold cyan] [yellow]v{st['version']}[/yellow]\n"
        f"[dim]Environment: {st['environment']} | Status: {st['state']} | Permission Tier: {st['default_permission_level']}[/dim]\n"
        f"[dim]Type [bold white]/help[/bold white] for commands or [bold white]/exit[/bold white] to quit.[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", title="[bold white]HIMSETU CLI[/bold white]"))


def run_api_server(host: str = "127.0.0.1", port: int = 8000) -> int:
    """Start the FastAPI Uvicorn REST API server."""
    console.print(
        f"[bold cyan]Starting HIMSETU REST API Server on[/bold cyan] "
        f"[bold green]http://{host}:{port}[/bold green] (Docs: [link=http://{host}:{port}/docs]http://{host}:{port}/docs[/link])"
    )
    try:
        import uvicorn
        uvicorn.run("himsetu.api.app:create_app", host=host, port=port, factory=True, log_level="info")
        return 0
    except Exception as exc:
        console.print(f"[bold red]Failed to start API server:[/bold red] {exc}")
        return 1


def main(config_path: Optional[str] = None) -> int:
    """CLI application entry point loop and subcommands dispatcher."""
    # Handle direct command-line arguments (e.g. `main.py serve --port 8000`)
    if len(sys.argv) > 1 and sys.argv[1] in ("serve", "--serve"):
        parser = argparse.ArgumentParser(description="Run HIMSETU FastAPI REST Server")
        parser.add_argument("cmd", nargs="?", default="serve")
        parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind to")
        parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
        args = parser.parse_args(sys.argv[1:])
        return run_api_server(host=args.host, port=args.port)

    try:
        cfg = load_config(config_path=config_path) if config_path else load_config()
        engine = HimSetuEngine(config=cfg)
        engine.initialize()
    except Exception as exc:
        console.print(f"[bold red]Failed to initialize HIMSETU Engine:[/bold red] {exc}")
        return 1

    print_banner(engine)

    try:
        while engine.state == EngineState.READY:
            try:
                user_input = input(f"\n{Fore.CYAN}himsetu>{Style.RESET_ALL} ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Keyboard interrupt received. Shutting down...[/yellow]")
                break

            if not user_input:
                continue

            # Process input string
            result = engine.process(user_input)

            if result.intent == "exit":
                console.print(f"[bold yellow]{result.message}[/bold yellow]")
                break

            if result.success:
                console.print(f"[bold green][+] [{result.intent.upper()}][/bold green]")
                console.print(result.message)
            else:
                console.print(f"[bold red][-] [{result.error or 'ERROR'}][/bold red] {result.message}")

    finally:
        engine.shutdown()
        console.print("[dim]HIMSETU session closed.[/dim]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
