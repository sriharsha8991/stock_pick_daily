"""
Open Interest analysis and trend alignment checks.
"""

import pandas as pd


def analyse_oi_signal(price_change: float, oi_change_pct: float) -> tuple[str, float]:
    """
    Classify Open Interest activity.
    Returns (signal_label, score).
    """
    threshold = 5  # % OI change to be significant

    if price_change > 0 and oi_change_pct > threshold:
        return "LONG_BUILDUP", 1.0
    elif price_change < 0 and oi_change_pct > threshold:
        return "SHORT_BUILDUP", 1.0
    elif price_change > 0 and oi_change_pct < -threshold:
        return "SHORT_COVERING", 0.5
    elif price_change < 0 and oi_change_pct < -threshold:
        return "LONG_UNWINDING", 0.5
    else:
        return "NEUTRAL", 0.25


def check_trend_alignment(row: pd.Series, bias: str = "long") -> tuple[bool, float]:
    """
    Check if price, EMAs and RSI are aligned for the given bias.
    Returns (is_aligned, trend_score 0-1).
    """
    price = row.get("close", 0)
    ema20 = row.get("ema20", 0)
    ema50 = row.get("ema50", 0)
    rsi = row.get("rsi", 50)

    if bias == "long":
        checks = [
            price > ema20,
            ema20 > ema50,
            55 <= rsi <= 80,
        ]
    else:
        checks = [
            price < ema20,
            ema20 < ema50,
            20 <= rsi <= 45,
        ]

    passed = sum(checks)
    is_aligned = passed >= 2  # at least 2 of 3
    score = passed / 3.0
    return is_aligned, round(score, 2)
