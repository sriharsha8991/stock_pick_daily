"""
Display Module
Rich terminal output for scanner results.
"""

import sys
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Ensure UTF-8 output on Windows so box-drawing characters work
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

console = Console(force_terminal=True)


def display_results(results: dict) -> None:
    """Pretty-print scanner results to the terminal."""

    regime = results.get("regime", {})
    sector_analysis = results.get("sector_analysis", {})
    trade_plans = results.get("trade_plans", [])
    candidates = results.get("candidates", [])

    # ── Header ──
    bias = regime.get("bias", "NEUTRAL")
    bias_color = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}.get(bias, "white")

    header = Text()
    header.append(f"  INTRADAY SCANNER — {date.today().strftime('%d %b %Y')}", style="bold white")
    header.append(f"  |  Market: ", style="white")
    header.append(f"{bias}", style=f"bold {bias_color}")
    header.append(f"  |  VIX: {regime.get('vix', 0):.1f}", style="cyan")
    header.append(f" ({regime.get('vix_regime', 'normal')})", style="dim")

    console.print()
    console.print(Panel(header, border_style="bright_blue", expand=True))

    # ── Kill switch ──
    if not regime.get("tradeable", True):
        console.print(Panel(
            f"[bold red]⚠ KILL SWITCH ACTIVE[/bold red]\n"
            + "\n".join(f"  • {r}" for r in regime.get("kill_reasons", [])),
            border_style="red",
            title="NO TRADE TODAY",
        ))
        return

    # ── Market Context ──
    ctx_table = Table(show_header=False, box=None, padding=(0, 2))
    ctx_table.add_row("FII Net", f"₹{regime.get('fii_net', 0):+,.0f} Cr",
                       "DII Net", f"₹{regime.get('dii_net', 0):+,.0f} Cr")
    ctx_table.add_row("S&P 500", f"{regime.get('us_sp500_change', 0):+.2f}%",
                       "NASDAQ", f"{regime.get('us_nasdaq_change', 0):+.2f}%")
    ctx_table.add_row("Nifty Gap", f"{regime.get('nifty_gap_est', 0):+.2f}%",
                       "Expiry Day", "YES" if regime.get("is_expiry") else "No")
    console.print(Panel(ctx_table, title="Market Context", border_style="blue"))

    # ── Sector Rotation ──
    strong = sector_analysis.get("strong_sectors", [])
    weak = sector_analysis.get("weak_sectors", [])
    sector_scores = sector_analysis.get("sector_scores", {})

    sec_table = Table(title="Sector Relative Strength", show_lines=True)
    sec_table.add_column("Sector", style="bold")
    sec_table.add_column("RS (5D)", justify="right")
    sec_table.add_column("RS (20D)", justify="right")
    sec_table.add_column("Weighted RS", justify="right")
    sec_table.add_column("Signal", justify="center")

    for sector, scores in sorted(sector_scores.items(), key=lambda x: x[1]["weighted_rs"], reverse=True):
        signal = ""
        if sector in strong:
            signal = "[bold green]▲ STRONG[/bold green]"
        elif sector in weak:
            signal = "[bold red]▼ WEAK[/bold red]"

        rs_5d = scores["rs_5d"]
        rs_color = "green" if rs_5d > 0 else "red"
        sec_table.add_row(
            sector,
            f"[{rs_color}]{rs_5d:+.2f}%[/{rs_color}]",
            f"{scores['rs_20d']:+.2f}%",
            f"{scores['weighted_rs']:+.2f}",
            signal,
        )
    console.print(sec_table)

    # ── Candidates Table ──
    if candidates:
        cand_table = Table(title=f"Filtered Candidates ({len(candidates)} stocks)", show_lines=True)
        cand_table.add_column("#", justify="right", style="dim")
        cand_table.add_column("Symbol", style="bold cyan")
        cand_table.add_column("Sector")
        cand_table.add_column("Bias", justify="center")
        cand_table.add_column("Gap%", justify="right")
        cand_table.add_column("RS", justify="right")
        cand_table.add_column("Vol", justify="right")
        cand_table.add_column("ATR%", justify="right")
        cand_table.add_column("RSI", justify="right")
        cand_table.add_column("OI Signal")
        cand_table.add_column("Score", justify="right", style="bold")

        for i, c in enumerate(candidates[:10], 1):  # Show top 10
            bias_str = f"[green]LONG[/green]" if c["bias"] == "LONG" else f"[red]SHORT[/red]"
            cand_table.add_row(
                str(i),
                c["symbol"],
                c["sector"],
                bias_str,
                f"{c['gap_pct']:+.1f}%",
                f"{c['sector_rs']:+.2f}",
                f"{c['volume_ratio']:.1f}x",
                f"{c['atr_pct']:.1f}%",
                f"{c['rsi']:.0f}",
                c["oi_signal"],
                f"{c['final_score']:.3f}",
            )
        console.print(cand_table)

    # ── Trade Plans ──
    if trade_plans:
        console.print()
        console.print("[bold yellow]═══ TRADE PLANS ═══[/bold yellow]")
        console.print()

        for plan in trade_plans:
            bias_icon = "▲" if plan["bias"] == "LONG" else "▼"
            bias_color = "green" if plan["bias"] == "LONG" else "red"

            # Setup description
            setup_parts = []
            if plan.get("is_nr7"):
                setup_parts.append("NR7 Breakout")
            if plan.get("is_inside_bar"):
                setup_parts.append("Inside Bar")
            if plan.get("pattern_score", 0) > 0 and not setup_parts:
                setup_parts.append("Range Expansion")
            setup_str = " + ".join(setup_parts) if setup_parts else "Momentum"

            trend_icon = "▲" if plan["trend_aligned"] else "─"

            plan_text = (
                f"  [bold {bias_color}]#{plan['rank']} {plan['symbol']}[/bold {bias_color}]"
                f"  |  {plan['sector']}"
                f"  |  Score: [bold]{plan['score']:.3f}[/bold]/1.000\n"
                f"     Gap: {plan['gap_pct']:+.1f}%"
                f"  |  RS: {plan['sector_rs']:+.2f}"
                f"  |  Vol: {plan['volume_ratio']:.1f}x"
                f"  |  ATR%: {plan['atr_pct']:.1f}%\n"
                f"     OI: {plan['oi_signal']}"
                f"  |  Delivery: {plan['delivery_pct']:.0f}%"
                f"  |  RSI: {plan['rsi']:.0f}\n"
                f"     Setup: {setup_str}"
                f"  |  Trend: {trend_icon} {'Aligned' if plan['trend_aligned'] else 'Partial'}\n"
                f"     ─────────────────────────────────────────\n"
                f"     [bold]Entry:[/bold]  ₹{plan['entry']:,.2f}  (above 15-min {'high' if plan['bias'] == 'LONG' else 'low'})\n"
                f"     [bold red]Stop:[/bold red]   ₹{plan['stop_loss']:,.2f}"
                f"  |  Risk: ₹{plan['entry'] - plan['stop_loss']:+,.2f} ({plan['risk_pct']:.2f}%)\n"
                f"     [bold green]T1:[/bold green]     ₹{plan['target_1']:,.2f}"
                f"  |  Reward: {plan['reward_t1_pct']:.2f}%\n"
                f"     [bold green]T2:[/bold green]     ₹{plan['target_2']:,.2f}"
                f"  |  Reward: {plan['reward_t2_pct']:.2f}%\n"
                f"     R:R = 1:{plan['rr_ratio']:.1f}\n"
                f"     Size:  {plan['quantity']} shares"
                f"  |  Capital: ₹{plan['position_value']:,.0f}\n"
                f"     Cost:  ₹{plan['total_cost']:.0f} ({plan['cost_pct']:.3f}%)"
                f"  |  Exit by: {plan['exit_time']}"
            )

            console.print(Panel(plan_text, border_style=bias_color, expand=True))

    else:
        console.print(Panel(
            "[yellow]No stocks passed all filters today. Consider sitting out.[/yellow]",
            border_style="yellow",
        ))

    # ── Footer ──
    console.print()
    console.print(Panel(
        "  [dim]Risk: Max ₹4000/trade  |  Exit by 3:10 PM  |  Trail after T1  |  Max 2 trades/day[/dim]",
        border_style="dim",
    ))
