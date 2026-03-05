"""
NSE Intraday Stock Scanner Configuration.

Re-exports all configuration constants from sub-modules for backward
compatibility.  Import from ``config`` exactly as before::

    from config import ALL_FNO_STOCKS, CAPITAL_PER_TRADE, VIX_REGIMES
"""

# Sector & stock universe
from config.sectors import (
    ALL_FNO_STOCKS,
    SECTOR_INDEX_MAP,
    SECTOR_STOCKS,
)

# VIX, scoring, filters, kill-switches
from config.thresholds import (
    ATR_PERIOD,
    EMA_LONG,
    EMA_SHORT,
    FII_BEARISH_THRESHOLD,
    FII_BULLISH_THRESHOLD,
    LOOKBACK_DAYS,
    MAX_MARKET_GAP,
    MAX_VIX_TO_TRADE,
    MIN_AVG_VOLUME,
    MIN_DELIVERY_PCT,
    MIN_FIRST_CANDLE_VOL_RATIO,
    MIN_PREOPEN_VOL_RATIO,
    MIN_SCORE_THRESHOLD,
    OI_CHANGE_SIGNIFICANT,
    RS_MEDIUM_PERIOD,
    RS_SHORT_PERIOD,
    RSI_PERIOD,
    SCORING_WEIGHTS,
    VIX_REGIMES,
    VOLUME_AVG_PERIOD,
    WEEKLY_MAX_LOSS_PCT,
)

# Risk management & costs
from config.risk import (
    BROKERAGE_PER_ORDER,
    CAPITAL_PER_TRADE,
    EXCHANGE_CHARGE_RATE,
    EXIT_TIME,
    GST_RATE,
    MAX_RISK_PCT,
    MAX_TRADES_PER_DAY,
    STAMP_DUTY_RATE,
    STOP_LOSS_ATR_MULTIPLE,
    STT_SELL_RATE,
    TARGET_1_ATR_MULTIPLE,
    TARGET_2_ATR_MULTIPLE,
    TAX_SLAB,
)

# Market timing
from config.timing import (
    FIRST_15MIN_END,
    MARKET_CLOSE,
    MARKET_OPEN,
    PRE_OPEN_END,
    PRE_OPEN_START,
    SQUARE_OFF_TIME,
)
