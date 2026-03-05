"""
Backward-compatibility shim.
The real implementation lives in ``backtest_pkg/engine.py``.

Usage:
    python -m backtest_pkg.engine --days 90 --capital 200000
"""

import argparse
import logging

from backtest_pkg.engine import backtest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest the Intraday Scanner")
    parser.add_argument("--days", type=int, default=90, help="Backtest lookback days")
    parser.add_argument("--capital", type=float, default=200_000, help="Capital per trade")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    backtest(days=args.days, capital=args.capital)
