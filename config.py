"""
Backward-compatibility shim — all constants now live under ``config/``.

Importing ``from config import X`` still works because the ``config/``
package's ``__init__.py`` re-exports everything.

This file can be safely deleted once all imports use the package directly.
"""

# This file is intentionally left as a placeholder.
# Python will resolve ``import config`` to the ``config/`` package
# (which has __init__.py) instead of this file when both exist.
# To be safe, we keep this file empty so nothing breaks if
# the project root is at the front of sys.path.


# ──────────────────────────────────────────────
# SECTOR → STOCK MAPPING (F&O Stocks Only)
# ──────────────────────────────────────────────
SECTOR_STOCKS = {
    "BANKING": [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN",
        "INDUSINDBK", "BANKBARODA", "PNB", "CANBK", "FEDERALBNK",
        "IDFCFIRSTB", "BANDHANBNK", "AUBANK", "RBLBANK", "INDIANB",
        "BANKINDIA", "UNIONBANK", "YESBANK",
    ],
    "IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTM",
        "MPHASIS", "COFORGE", "PERSISTENT", "KPITTECH", "TATAELXSI",
        "OFSS",
    ],
    "PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN",
        "AUROPHARMA", "BIOCON", "TORNTPHARM", "GLENMARK", "MANKIND",
        "ZYDUSLIFE", "LAURUSLABS", "SYNGENE", "PPLPHARMA",
    ],
    "AUTO": [
        "MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "HEROMOTOCO",
        "EICHERMOT", "ASHOKLEY", "TVSMOTOR", "BHARATFORG", "MOTHERSON",
        "SONACOMS", "UNOMINDA", "EXIDEIND",
    ],
    "METAL": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL",
        "SAIL", "NMDC", "NATIONALUM", "HINDZINC",
    ],
    "ENERGY": [
        "RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "HINDPETRO",
        "OIL", "PETRONET", "NTPC", "POWERGRID", "TATAPOWER",
        "NHPC", "PFC", "RECLTD", "COALINDIA", "ADANIENT",
        "ADANIGREEN", "ADANIPORTS", "ADANIENSOL",
    ],
    "FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR",
        "MARICO", "COLPAL", "GODREJCP", "TATACONSUM", "VBL",
        "UNITDSPR", "PATANJALI",
    ],
    "FINANCIAL": [
        "BAJFINANCE", "BAJAJFINSV", "HDFCLIFE", "SBILIFE", "ICICIPRULI",
        "ICICIGI", "HDFCAMC", "CHOLAFIN", "SHRIRAMFIN", "MUTHOOTFIN",
        "MANAPPURAM", "LICHSGFIN", "LTF", "SBICARD", "ABCAPITAL",
        "MFSL", "JIOFIN", "SAMMAANCAP", "PNBHOUSING", "ANGELONE",
        "NUVAMA", "KFINTECH", "CAMS", "CDSL", "360ONE",
    ],
    "REALTY": [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD",
        "LODHA",
    ],
}

# ──────────────────────────────────────────────
# ALL F&O STOCKS (flat list for quick lookup)
# ──────────────────────────────────────────────
ALL_FNO_STOCKS = sorted(set(
    stock for stocks in SECTOR_STOCKS.values() for stock in stocks
))

# ──────────────────────────────────────────────
# VIX REGIME THRESHOLDS
# ──────────────────────────────────────────────
VIX_REGIMES = {
    "low_vol":  {"vix_max": 13, "gap_threshold": 0.5, "atr_threshold": 1.5},
    "normal":   {"vix_max": 18, "gap_threshold": 0.8, "atr_threshold": 2.0},
    "high_vol": {"vix_max": 99, "gap_threshold": 1.2, "atr_threshold": 2.5},
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
MIN_AVG_VOLUME = 2_000_000        # 20 lakh shares/day
MIN_PREOPEN_VOL_RATIO = 1.3       # Pre-open volume spike
MIN_FIRST_CANDLE_VOL_RATIO = 1.5  # First 5-min candle spike
MIN_DELIVERY_PCT = 40             # Delivery % for conviction
MIN_SCORE_THRESHOLD = 0.60        # Minimum score to trade

# ──────────────────────────────────────────────
# RISK MANAGEMENT
# ──────────────────────────────────────────────
CAPITAL_PER_TRADE = 200_000       # ₹2 Lakhs per trade
MAX_RISK_PCT = 0.02               # 2% risk per trade = ₹4000
MAX_TRADES_PER_DAY = 2            # Maximum concurrent trades
STOP_LOSS_ATR_MULTIPLE = 0.5      # SL = 0.5 × ATR
TARGET_1_ATR_MULTIPLE = 0.8       # T1 = 0.8 × ATR
TARGET_2_ATR_MULTIPLE = 1.5       # T2 = 1.5 × ATR
EXIT_TIME = "15:10"               # Hard exit time

# ──────────────────────────────────────────────
# KILL SWITCHES
# ──────────────────────────────────────────────
MAX_VIX_TO_TRADE = 25             # Don't trade above VIX 25
MAX_MARKET_GAP = 2.0              # Don't trade if Nifty gaps > 2%
WEEKLY_MAX_LOSS_PCT = 0.04        # Stop trading if down 4% for week

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
# TRANSACTION COSTS (per side, Zerodha-like)
# ──────────────────────────────────────────────
BROKERAGE_PER_ORDER = 20          # ₹20 flat
STT_SELL_RATE = 0.00025           # 0.025% on sell
EXCHANGE_CHARGE_RATE = 0.0000307  # NSE transaction charge
GST_RATE = 0.18                   # 18% GST
STAMP_DUTY_RATE = 0.00003         # 0.003% on buy
TAX_SLAB = 0.30                   # 30% tax bracket (worst case)

# ──────────────────────────────────────────────
# NSE MARKET TIMING
# ──────────────────────────────────────────────
PRE_OPEN_START = "09:00"
PRE_OPEN_END = "09:08"
MARKET_OPEN = "09:15"
FIRST_15MIN_END = "09:30"
MARKET_CLOSE = "15:30"
SQUARE_OFF_TIME = "15:10"

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
