from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

try:
    from .agent import WeatherAgent, WeatherAgentError
except ImportError:
    from agent import WeatherAgent, WeatherAgentError


console = Console()


# This function prints the top heading of the CLI app.
def render_header() -> None:
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="right")
    table.add_row("[bold cyan]Weather Agent[/bold cyan]", "[dim]type exit to quit[/dim]")
    console.print(Panel(table, border_style="cyan", padding=(0, 1)))


# This function starts the CLI and keeps asking the user for questions.
def main() -> None:
    render_header()

    try:
        agent = WeatherAgent()
    except WeatherAgentError as exc:
        console.print(Panel(str(exc), title="Setup needed", border_style="red"))
        return

    while True:
        user_query = Prompt.ask("\n[bold green]You[/bold green]").strip()

        if user_query.lower() in {"exit", "quit", "q"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        # This spinner shows while the AI is thinking and calling the weather API.
        with console.status("[cyan]Thinking and checking live weather...[/cyan]", spinner="dots"):
            try:
                answer = agent.ask(user_query)
            except Exception as exc:
                answer = f"Sorry, I could not complete that request: {exc}"

        console.print(Panel(answer, title="Agent", border_style="green", padding=(1, 2)))


if __name__ == "__main__":
    main()
