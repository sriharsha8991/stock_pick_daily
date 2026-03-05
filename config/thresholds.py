"""
VIX regimes, scoring weights, and filter thresholds.
"""

# ──────────────────────────────────────────────
# VIX REGIME THRESHOLDS
# ──────────────────────────────────────────────
VIX_REGIMES = {
    "low_vol":  {"vix_max": 13, "gap_threshold": 0.3, "atr_threshold": 1.0},
    "normal":   {"vix_max": 18, "gap_threshold": 0.5, "atr_threshold": 1.5},
    "high_vol": {"vix_max": 99, "gap_threshold": 0.7, "atr_threshold": 1.8},
}

# ──────────────────────────────────────────────
# SCORING WEIGHTS
# ──────────────────────────────────────────────
SCORING_WEIGHTS = {
    "gap_score":            0.12,
    "relative_strength":    0.15,
    "volume_spike":         0.12,
    "atr_pct":              0.10,
    "trend_structure":      0.15,
    "oi_signal":            0.18,
    "prior_day_pattern":    0.08,
    "delivery_pct":         0.05,
    "fii_sector_alignment": 0.05,
}

# ──────────────────────────────────────────────
# FILTER THRESHOLDS
# ──────────────────────────────────────────────
MIN_AVG_VOLUME = 500_000          # 5 lakh shares/day (F&O stocks easily clear this)
MIN_PREOPEN_VOL_RATIO = 1.3       # Pre-open volume spike
MIN_FIRST_CANDLE_VOL_RATIO = 1.5  # First 5-min candle spike
MIN_DELIVERY_PCT = 40             # Delivery % for conviction
MIN_SCORE_THRESHOLD = 0.40        # Minimum score to trade (relaxed; real OI data will tighten)

# ──────────────────────────────────────────────
# FII/DII SIGNAL THRESHOLDS (in Crores)
# ──────────────────────────────────────────────
FII_BULLISH_THRESHOLD = 500       # ₹500 Cr net buy = bullish
FII_BEARISH_THRESHOLD = -500      # ₹500 Cr net sell = bearish

# ──────────────────────────────────────────────
# OI ANALYSIS THRESHOLDS
# ──────────────────────────────────────────────
OI_CHANGE_SIGNIFICANT = 5         # 5% OI change is significant

# ──────────────────────────────────────────────
# KILL SWITCHES
# ──────────────────────────────────────────────
MAX_VIX_TO_TRADE = 25             # Don't trade above VIX 25
MAX_MARKET_GAP = 2.0              # Don't trade if Nifty gaps > 2%
WEEKLY_MAX_LOSS_PCT = 0.04        # Stop trading if down 4% for week

# ──────────────────────────────────────────────
# HISTORICAL DATA LOOKBACK
# ──────────────────────────────────────────────
LOOKBACK_DAYS = 180               # 6 months of daily data
RS_SHORT_PERIOD = 5               # 5-day RS
RS_MEDIUM_PERIOD = 20             # 20-day RS
EMA_SHORT = 20
EMA_LONG = 50
RSI_PERIOD = 14
ATR_PERIOD = 14
VOLUME_AVG_PERIOD = 20
