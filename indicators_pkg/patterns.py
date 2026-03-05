"""
Prior-day candlestick / range pattern detection.
"""

import numpy as np
import pandas as pd


def detect_prior_day_patterns(df: pd.DataFrame) -> dict:
    """
    Detect prior-day candle patterns on the last row of a daily DataFrame.
    Returns a dict of pattern flags and a composite score.
    """
    if len(df) < 8:
        return {
            "is_inside_bar": False,
            "is_nr7": False,
            "is_range_expansion": False,
            "pattern_score": 0.0,
        }

    highs = df["high"].values
    lows = df["low"].values
    ranges = highs - lows
    atr = df["atr"].iloc[-1] if "atr" in df.columns else ranges[-1]

    # Inside Bar: last bar's range inside previous bar's range
    is_inside_bar = (highs[-1] < highs[-2]) and (lows[-1] > lows[-2])

    # NR7: Narrowest range of last 7 bars
    last_7_ranges = ranges[-7:]
    is_nr7 = ranges[-1] == last_7_ranges.min()

    # Range Expansion: previous day had large range (> 1.5 × ATR)
    is_range_expansion = ranges[-1] > 1.5 * atr

    # Composite score
    score = 0.0
    if is_nr7:
        score += 0.5          # Highest probability — compression breakout
    if is_inside_bar:
        score += 0.3          # Good breakout setup
    if is_range_expansion:
        score += 0.2          # Momentum continuation

    return {
        "is_inside_bar": bool(is_inside_bar),
        "is_nr7": bool(is_nr7),
        "is_range_expansion": bool(is_range_expansion),
        "pattern_score": round(score, 2),
    }
