"""CLI interface for BullBearArena."""

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box

from bullbeararena import AGENT_DISPLAY, DEFAULT_AGENTS

app = typer.Typer(
    name="bullbeararena",
    help="🐃🐻 BullBearArena — AI-powered stock analysis through legendary investor perspectives",
)
console = Console()


@app.command()
def analyze(
    ticker: str = typer.Argument(..., help="Stock ticker symbol (e.g., AAPL, TSLA)"),
    agents: Optional[str] = typer.Option(None, "--agents", "-a", help="Comma-separated agent IDs (e.g., buffett,wood)"),
    llm_provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (openai, anthropic, ollama)"),
    llm_model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model name"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save report to file"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Analyze a stock through legendary investor perspectives."""
    asyncio.run(_analyze(ticker, agents, llm_provider, llm_model, output, json_output))


async def _analyze(ticker: str, agents_str: Optional[str], provider: Optional[str],
                    model: Optional[str], output: Optional[str], json_out: bool):
    from .config import Config
    from .data.sec_client import SECEdgarClient
    from .data.metrics import compute_financials
    from .agents.orchestrator import run_all_agents
    from .report.generator import generate_report
    from .report.formatter import format_report_markdown

    config = Config()
    if provider:
        config.llm_provider = provider
    if model:
        config.llm_model = model

    agent_ids = None
    if agents_str:
        agent_ids = [a.strip() for a in agents_str.split(",")]
        invalid = [a for a in agent_ids if a not in AGENT_DISPLAY]
        if invalid:
            console.print(f"[red]Unknown agents: {invalid}[/red]")
            console.print(f"[dim]Available: {list(AGENT_DISPLAY.keys())}[/dim]")
            raise typer.Exit(1)

    # Step 1: Fetch data
    console.print(f"\n[bold blue]📊 Fetching financial data for [cyan]{ticker.upper()}[/cyan]...[/bold blue]")
    try:
        client = SECEdgarClient(config)
        financials = await client.get_financials(ticker)
        console.print(f"[green]✓ Found: {financials['company_name']} (CIK: {financials['cik']})[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)

    # Step 2: Compute metrics
    console.print("[bold blue]🧮 Computing financial metrics...[/bold blue]")
    snapshot = compute_financials(
        facts_data=financials["facts"],
        company_name=financials["company_name"],
        ticker=financials["ticker"],
        latest_filings=financials["latest_filings"],
    )

    filing_str = ""
    if financials["latest_filings"]:
        f = financials["latest_filings"][0]
        filing_str = f"{f['form']} filed {f['date']}"

    # Step 3: Run agents
    console.print(f"[bold blue]🤖 Running investor agents (this takes 10-30s)...[/bold blue]")
    verdicts = await run_all_agents(
        financial_data=snapshot.to_dict(),
        agent_ids=agent_ids,
        config=config,
    )

    # Display agent results table
    table = Table(title=f"\n {snapshot.company_name} ({snapshot.ticker}) — Agent Verdicts",
                  box=box.ROUNDED, show_lines=True)
    table.add_column("Agent", style="bold")
    table.add_column("Rating", justify="center")
    table.add_column("Confidence", justify="center")
    table.add_column("One-liner", max_width=50)

    for v in verdicts:
        rating_style = {"Strong Buy": "bold green", "Buy": "green", "Hold": "yellow",
                        "Sell": "red", "Strong Sell": "bold red"}.get(v.rating, "white")
        table.add_row(
            f"{v.emoji} {v.agent_name}",
            f"[{rating_style}]{v.rating}[/{rating_style}]",
            f"{v.confidence:.0%}",
            v.summary[:60] + "..." if len(v.summary) > 60 else v.summary,
        )

    console.print(table)

    # Step 4: Generate report
    console.print("\n[bold blue]📝 Generating arena report...[/bold blue]")
    report = await generate_report(
        company_name=financials["company_name"],
        ticker=financials["ticker"],
        latest_filing=filing_str,
        verdicts=verdicts,
        config=config,
    )

    if json_out:
        result = report.to_dict()
        result["financial_snapshot"] = snapshot.to_dict()
        output_text = json.dumps(result, indent=2, ensure_ascii=False)
        if output:
            with open(output, "w") as f:
                f.write(output_text)
            console.print(f"[green]✓ Report saved to {output}[/green]")
        else:
            console.print(output_text)
    else:
        md = format_report_markdown(report, snapshot)
        if output:
            with open(output, "w") as f:
                f.write(md)
            console.print(f"[green]✓ Report saved to {output}[/green]")
        else:
            console.print(Panel(Markdown(md), title="🏟️ BullBearArena Report", border_style="blue"))

    # Disclaimer
    console.print("\n[dim]⚠️ This is for educational purposes only. Not financial advice. Do your own research.[/dim]\n")


@app.command()
def list_agents():
    """List all available investor agents."""
    table = Table(title="Available Investor Agents", box=box.ROUNDED)
    table.add_column("ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Style")

    for agent_id, info in AGENT_DISPLAY.items():
        table.add_row(agent_id, f"{info['emoji']} {info['name']}", info["style"])

    console.print(table)


@app.command()
def lookup(ticker: str):
    """Look up a ticker symbol in SEC EDGAR."""
    asyncio.run(_lookup(ticker))


async def _lookup(ticker: str):
    from .config import Config
    from .data.sec_client import SECEdgarClient

    config = Config()
    client = SECEdgarClient(config)
    try:
        cik = await client.resolve_cik(ticker)
        subs = await client.get_company_submissions(cik)
        console.print(f"[green]✓ {ticker.upper()} → {subs.get('name', 'N/A')} (CIK: {cik})[/green]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")


if __name__ == "__main__":
    app()
