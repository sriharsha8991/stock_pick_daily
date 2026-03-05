"""
Technical indicators package.

Re-exports the public API so existing ``from indicators import …`` style
imports continue to work (via the compatibility shim at project root).
"""

from indicators_pkg.technical import (
    add_all_indicators,
    compute_atr,
    compute_ema,
    compute_rsi,
    compute_vwap,
)
from indicators_pkg.patterns import detect_prior_day_patterns
from indicators_pkg.oi_analysis import analyse_oi_signal, check_trend_alignment

__all__ = [
    "add_all_indicators",
    "compute_atr",
    "compute_ema",
    "compute_rsi",
    "compute_vwap",
    "detect_prior_day_patterns",
    "analyse_oi_signal",
    "check_trend_alignment",
]
