from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .agent import CodingAgent, CodingAgentError
from .config import Settings, SettingsError


console = Console()
DEFAULT_WORKSPACE = Path(__file__).resolve().parents[2]


# Shows the app title and the workspace being used.
def render_header(workspace: Path) -> None:
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row("[bold cyan]Claude Code Agent[/bold cyan]", f"[dim]{workspace}[/dim]")
    console.print(Panel(table, border_style="cyan", padding=(0, 1)))


# Reads CLI arguments, creates the agent, and starts one-shot or interactive mode.
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="claude-code-agent",
        description="Run an AI coding agent over a local workspace.",
    )
    parser.add_argument("task", nargs="*", help="Natural-language coding task.")
    parser.add_argument(
        "-w",
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help="Project directory the agent is allowed to work in.",
    )
    parser.add_argument("--max-steps", type=int, default=12, help="Maximum AI/tool iterations.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show tool details.")
    args = parser.parse_args(argv)

    task = " ".join(args.task).strip() or None
    workspace = args.workspace.resolve()
    render_header(workspace)

    try:
        settings = Settings.load()
        agent = CodingAgent(
            settings=settings,
            workspace=workspace,
            console=console,
            verbose=args.verbose,
        )
    except (SettingsError, CodingAgentError) as exc:
        console.print(Panel(str(exc), title="Setup needed", border_style="red"))
        raise SystemExit(1) from exc

    if task:
        _run_one(agent, task, args.max_steps)
        return

    console.print("[dim]Type a task, or 'exit' to quit.[/dim]")
    while True:
        user_task = Prompt.ask("\n[bold green]Task[/bold green]").strip()
        if user_task.lower() in {"exit", "quit", "q"}:
            console.print("[dim]Goodbye.[/dim]")
            return
        if user_task:
            _run_one(agent, user_task, args.max_steps)


# Runs a single user task and prints the final result panel.
def _run_one(agent: CodingAgent, task: str, max_steps: int) -> None:
    try:
        result = agent.run(task=task, max_steps=max_steps)
    except Exception as exc:
        console.print(Panel(str(exc), title="Failed", border_style="red"))
        raise SystemExit(1) from exc

    border = "green" if result.ok else "red"
    title = "Completed" if result.ok else "Stopped"
    console.print(Panel(_terminal_safe(result.summary), title=title, border_style=border, padding=(1, 2)))


# Cleans model text so older Windows terminals can print it safely.
def _terminal_safe(text: str) -> str:
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
        "\u00a0": " ",
        "\u202f": " ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("ascii", errors="replace").decode("ascii")


if __name__ == "__main__":
    main()
