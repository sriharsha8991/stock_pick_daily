"""
Risk management and transaction cost parameters.
"""

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
# TRANSACTION COSTS (per side, Zerodha-like)
# ──────────────────────────────────────────────
BROKERAGE_PER_ORDER = 20          # ₹20 flat
STT_SELL_RATE = 0.00025           # 0.025% on sell
EXCHANGE_CHARGE_RATE = 0.0000307  # NSE transaction charge
GST_RATE = 0.18                   # 18% GST
STAMP_DUTY_RATE = 0.00003         # 0.003% on buy
TAX_SLAB = 0.30                   # 30% tax bracket (worst case)
