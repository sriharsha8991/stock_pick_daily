"""
Backtesting Engine
Validates the scanner strategy on historical data.

Usage:
    python -m backtest_pkg.engine --days 360 --capital 20000
"""

import argparse
import logging
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from config import (
    CAPITAL_PER_TRADE,
    STOP_LOSS_ATR_MULTIPLE,
    TARGET_1_ATR_MULTIPLE,
    TARGET_2_ATR_MULTIPLE,
)
from data.fetcher import DataFetcher
from indicators_pkg.technical import add_all_indicators
from indicators_pkg.oi_analysis import check_trend_alignment
from utils.helpers import normalize

console = Console()
logger = logging.getLogger(__name__)


def backtest(days: int = 90, capital: float = 200_000, top_n: int = 2):
    """
    Simple backtest: for each historical trading day, simulate scanner logic
    on the previous day's close data, then check next-day intraday range
    to see if T1 / T2 / SL would have been hit.
    """
    console.print(f"\n[bold]Running backtest over last {days} days...[/bold]\n")

    fetcher = DataFetcher()

    # Pick a subset of liquid F&O stocks for backtesting
    test_symbols = [
        "HDFCBANK", "ICICIBANK", "SBIN", "RELIANCE", "TCS", "INFY",
        "BAJFINANCE", "AXISBANK", "TATASTEEL", "SUNPHARMA", "HINDUNILVR",
        "KOTAKBANK", "ITC", "LT", "M&M", "MARUTI", "WIPRO",
        "TECHM", "DRREDDY", "CIPLA", "JSWSTEEL", "HINDALCO",
        "BHARTIARTL", "NTPC", "POWERGRID", "TATAMOTORS",
    ]

    console.print(f"Fetching data for {len(test_symbols)} stocks...")
    all_data = fetcher.get_bulk_historical(test_symbols, days=days + 120)
    console.print(f"  → Got data for {len(all_data)} stocks\n")

    trade_log: list[dict] = []

    for symbol, df in all_data.items():
        if len(df) < 70:
            continue

        df = add_all_indicators(df)

        # Simulate day-by-day from lookback onwards
        for i in range(60, len(df) - 1):
            hist = df.iloc[: i + 1]
            next_day = df.iloc[i + 1]

            last = hist.iloc[-1]

            # Quick filter checks
            avg_vol = last.get("vol_avg_20", 0)
            if avg_vol < 1_000_000:
                continue

            gap_pct = last.get("gap_pct", 0)
            if abs(gap_pct) < 0.5:
                continue

            atr_pct = last.get("atr_pct", 0)
            if atr_pct < 1.5:
                continue

            vol_ratio = last.get("volume_ratio", 0)

            # Bias
            bias = "long" if gap_pct > 0 else "short"
            is_aligned, trend_score = check_trend_alignment(last, bias)

            if not is_aligned:
                continue

            # Simple score
            gap_score = normalize(abs(gap_pct), 0, 3.0)
            vol_score = normalize(vol_ratio, 1.0, 5.0)
            atr_score = normalize(atr_pct, 1.0, 5.0)
            score = 0.2 * gap_score + 0.2 * vol_score + 0.15 * atr_score + 0.2 * trend_score

            if score < 0.35:
                continue

            # Simulate trade on NEXT day
            entry = next_day["open"]
            atr = last["atr"]
            sl_points = atr * STOP_LOSS_ATR_MULTIPLE
            t1_points = atr * TARGET_1_ATR_MULTIPLE
            t2_points = atr * TARGET_2_ATR_MULTIPLE

            if bias == "long":
                sl = entry - sl_points
                t1 = entry + t1_points
                t2 = entry + t2_points
                if next_day["low"] <= sl:
                    result = "SL_HIT"
                    pnl_pct = -(sl_points / entry) * 100
                elif next_day["high"] >= t2:
                    result = "T2_HIT"
                    pnl_pct = (t2_points / entry) * 100
                elif next_day["high"] >= t1:
                    result = "T1_HIT"
                    pnl_pct = (t1_points / entry) * 100
                else:
                    pnl_pct = ((next_day["close"] - entry) / entry) * 100
                    result = "CLOSE_EXIT"
            else:
                sl = entry + sl_points
                t1 = entry - t1_points
                t2 = entry - t2_points
                if next_day["high"] >= sl:
                    result = "SL_HIT"
                    pnl_pct = -(sl_points / entry) * 100
                elif next_day["low"] <= t2:
                    result = "T2_HIT"
                    pnl_pct = (t2_points / entry) * 100
                elif next_day["low"] <= t1:
                    result = "T1_HIT"
                    pnl_pct = (t1_points / entry) * 100
                else:
                    pnl_pct = ((entry - next_day["close"]) / entry) * 100
                    result = "CLOSE_EXIT"

            trade_log.append({
                "date": next_day.get("date", ""),
                "symbol": symbol,
                "bias": bias.upper(),
                "entry": round(entry, 2),
                "sl": round(sl, 2),
                "t1": round(t1, 2),
                "t2": round(t2, 2),
                "result": result,
                "pnl_pct": round(pnl_pct, 2),
                "score": round(score, 3),
                "gap_pct": round(gap_pct, 2),
                "atr_pct": round(atr_pct, 2),
            })

    if not trade_log:
        console.print("[yellow]No trades generated in backtest period.[/yellow]")
        return

    trades_df = pd.DataFrame(trade_log)

    # ── Summary Stats ──
    total = len(trades_df)
    wins = len(trades_df[trades_df["pnl_pct"] > 0])
    losses = len(trades_df[trades_df["pnl_pct"] <= 0])
    win_rate = (wins / total) * 100 if total > 0 else 0
    avg_win = trades_df[trades_df["pnl_pct"] > 0]["pnl_pct"].mean() if wins > 0 else 0
    avg_loss = trades_df[trades_df["pnl_pct"] <= 0]["pnl_pct"].mean() if losses > 0 else 0
    total_pnl = trades_df["pnl_pct"].sum()
    avg_pnl = trades_df["pnl_pct"].mean()
    max_win = trades_df["pnl_pct"].max()
    max_loss = trades_df["pnl_pct"].min()

    t1_hits = len(trades_df[trades_df["result"] == "T1_HIT"])
    t2_hits = len(trades_df[trades_df["result"] == "T2_HIT"])
    sl_hits = len(trades_df[trades_df["result"] == "SL_HIT"])
    close_exits = len(trades_df[trades_df["result"] == "CLOSE_EXIT"])

    console.print(f"\n[bold]═══ BACKTEST RESULTS ({days} days) ═══[/bold]\n")

    stats_table = Table(show_header=False, box=None, padding=(0, 3))
    stats_table.add_row("Total Trades", str(total), "Win Rate", f"{win_rate:.1f}%")
    stats_table.add_row("Wins", str(wins), "Avg Win", f"{avg_win:+.2f}%")
    stats_table.add_row("Losses", str(losses), "Avg Loss", f"{avg_loss:+.2f}%")
    stats_table.add_row("T1 Hits", str(t1_hits), "T2 Hits", str(t2_hits))
    stats_table.add_row("SL Hits", str(sl_hits), "Close Exits", str(close_exits))
    stats_table.add_row("", "", "", "")
    stats_table.add_row("Total PnL", f"{total_pnl:+.1f}%", "Avg PnL/Trade", f"{avg_pnl:+.2f}%")
    stats_table.add_row("Max Win", f"{max_win:+.2f}%", "Max Loss", f"{max_loss:+.2f}%")

    if avg_loss != 0:
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        profit_factor = abs(avg_win * wins) / abs(avg_loss * losses) if losses > 0 else float("inf")
        stats_table.add_row("Expectancy", f"{expectancy:+.2f}%", "Profit Factor", f"{profit_factor:.2f}")

    console.print(stats_table)

    # ── Per-stock breakdown ──
    console.print(f"\n[bold]Per-Stock Performance (Top 10):[/bold]")
    stock_perf = trades_df.groupby("symbol").agg(
        trades=("pnl_pct", "count"),
        total_pnl=("pnl_pct", "sum"),
        avg_pnl=("pnl_pct", "mean"),
        win_rate=("pnl_pct", lambda x: (x > 0).mean() * 100),
    ).sort_values("total_pnl", ascending=False)

    perf_table = Table(show_lines=True)
    perf_table.add_column("Symbol", style="bold")
    perf_table.add_column("Trades", justify="right")
    perf_table.add_column("Total PnL%", justify="right")
    perf_table.add_column("Avg PnL%", justify="right")
    perf_table.add_column("Win Rate", justify="right")

    for sym, row in stock_perf.head(10).iterrows():
        color = "green" if row["total_pnl"] > 0 else "red"
        perf_table.add_row(
            sym,
            str(int(row["trades"])),
            f"[{color}]{row['total_pnl']:+.1f}%[/{color}]",
            f"{row['avg_pnl']:+.2f}%",
            f"{row['win_rate']:.0f}%",
        )
    console.print(perf_table)

    return trades_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest the Intraday Scanner")
    parser.add_argument("--days", type=int, default=90, help="Backtest lookback days")
    parser.add_argument("--capital", type=float, default=200_000, help="Capital per trade")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    backtest(days=args.days, capital=args.capital)
