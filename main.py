"""
NSE Intraday Stock Scanner — Main Entry Point

Usage:
    python main.py              # Run full scanner
    python main.py --dry-run    # Run with sample/cached data
    python main.py --debug      # Verbose logging
"""

import argparse
import logging
import sys
from datetime import date

# Ensure UTF-8 output on Windows terminals (fixes Rich box-drawing chars)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from rich.console import Console

from display_pkg import display_results
from scanner import IntradayScanner

console = Console(force_terminal=True)


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="NSE Intraday Stock Scanner v2.0")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Run with minimal output for testing")
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    console.print()
    console.print("[bold bright_blue]╔══════════════════════════════════════════════════╗[/bold bright_blue]")
    console.print("[bold bright_blue]║   NSE Intraday Scanner v2.0 — Pre-Market Run    ║[/bold bright_blue]")
    console.print(f"[bold bright_blue]║   {date.today().strftime('%A, %d %B %Y'):^46s}   ║[/bold bright_blue]")
    console.print("[bold bright_blue]╚══════════════════════════════════════════════════╝[/bold bright_blue]")
    console.print()

    try:
        scanner = IntradayScanner()

        with console.status("[bold cyan]Running scanner pipeline...[/bold cyan]"):
            results = scanner.run()

        display_results(results)

        # Summary stats
        trade_plans = results.get("trade_plans", [])
        if trade_plans:
            console.print()
            console.print(f"[bold green]✓ {len(trade_plans)} trade plan(s) generated.[/bold green]")
            console.print("[dim]Review the plans above. Enter trades only after first 15-min candle (9:30 AM).[/dim]")
        else:
            console.print()
            console.print("[bold yellow]⚠ No high-conviction trades found today.[/bold yellow]")
            console.print("[dim]Either market conditions are unfavourable or filters were too strict.[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Scanner interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[bold red]Error: {exc}[/bold red]")
        logging.exception("Scanner failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
