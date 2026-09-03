import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from chat import ask_pdf, get_chat_model, get_vector_store

console = Console()


def display_banner() -> None:
    """Render welcome header banner."""
    console.print(
        Panel.fit(
            "[bold cyan]PDF Knowledge Desk[/bold cyan]\n"
            "[dim]Grounded answers powered by Gemini & Qdrant[/dim]",
            border_style="cyan",
        )
    )
    console.print("[dim]Type 'exit', 'quit', or ':q' to leave.[/dim]\n")


def display_sources(sources: list) -> None:
    """Render table of retrieved passages and metadata."""
    if not sources:
        return

    table = Table(title="Retrieved Passages", show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", width=4)
    table.add_column("Page", justify="center", width=8)
    table.add_column("Score", justify="right", width=10)

    for src in sources:
        table.add_row(
            str(src["index"]),
            str(src["page"]),
            f"{src['score']:.4f}",
        )

    console.print(table)


def run_interactive_cli() -> None:
    """Main interactive terminal loop."""
    display_banner()

    with console.status("[bold yellow]Connecting to Qdrant & Gemini...", spinner="dots"):
        try:
            vector_store = get_vector_store()
            llm = get_chat_model()
        except Exception as err:
            console.print(f"[bold red]Initialization failed:[/bold red] {err}")
            console.print("[dim]Ensure Qdrant is running on port 6333 and GOOGLE_API_KEY is valid.[/dim]")
            return

    console.print("[bold green]Ready for questions![/bold green]\n")

    while True:
        try:
            question = console.input("[bold cyan]You[/bold cyan] [dim]>[/dim] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not question:
            continue

        if question.lower() in {"exit", "quit", ":q", "q"}:
            console.print("[dim]Goodbye![/dim]")
            break

        try:
            with console.status("[bold green]Searching context & generating answer...", spinner="dots"):
                result = ask_pdf(question, vector_store=vector_store, llm=llm)

            console.print(
                Panel(
                    Markdown(result["answer"]),
                    title="[bold green]Answer[/bold green]",
                    border_style="green",
                )
            )

            if result["sources"]:
                display_sources(result["sources"])
            console.print()

        except Exception as err:
            console.print(f"[bold red]Query failed:[/bold red] {err}\n")


def main() -> None:
    run_interactive_cli()


if __name__ == "__main__":
    main()
