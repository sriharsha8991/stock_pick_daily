"""
Backward-compatibility shim.
The real implementation lives in ``indicators_pkg/``.
"""

from indicators_pkg.technical import (  # noqa: F401
    add_all_indicators,
    compute_atr,
    compute_ema,
    compute_rsi,
    compute_vwap,
)
from indicators_pkg.patterns import detect_prior_day_patterns  # noqa: F401
from indicators_pkg.oi_analysis import (  # noqa: F401
    analyse_oi_signal,
    check_trend_alignment,
)
