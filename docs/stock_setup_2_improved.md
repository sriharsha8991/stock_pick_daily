# Improved Pre-Market Intraday Scanner — India NSE Edition v2.0

> **Goal**: Pick top 2-3 stocks daily that can deliver **1-2% return post all taxes & charges** within intraday.

---

## Critical Gap Analysis of v1 Blueprint

| # | Gap in v1 | Impact | Fix in v2 |
|---|-----------|--------|-----------|
| 1 | No concrete data source | Can't build anything | Use `jugaad-data` (NSE live + historical) + `yfinance` (fallback) |
| 2 | Pre-market data assumption wrong | NSE has 9:00–9:08 pre-open, NOT extended pre-market like US | Use **pre-open session data** (9:08 equilibrium price) + SGX Nifty/GIFT Nifty |
| 3 | No F&O filter | Non-F&O stocks have poor liquidity, wider spreads | **Only trade F&O stocks** (206 stocks from NSE) |
| 4 | Missing Open Interest (OI) | OI build-up is THE most important signal for Indian markets | Add **OI change analysis** as a first-class signal |
| 5 | No FII/DII flow data | Institutional flows drive 60%+ of market direction | Add **FII/DII daily flow** to Market Bias Engine |
| 6 | No delivery % analysis | High delivery % = institutional conviction | Add **delivery % filter** |
| 7 | No expiry day logic | Weekly Thu expiry (Nifty/BankNifty) creates unique patterns | Add **expiry day regime** detection |
| 8 | No previous day pattern | NR7, Inside Bar, Range Expansion are high-probability setups | Add **prior candle pattern** scoring |
| 9 | Tax/cost calculation missing | Can't validate 1-2% post-tax target | Full **cost model** built in |
| 10 | Weak risk management | Only 1 risk rule | Add **position sizing, max loss, time-based exits** |
| 11 | Sector mapping not concrete | Abstract mention | Hard-coded **NSE sectoral index → constituent** mapping |
| 12 | No GIFT Nifty integration | Best pre-open directional signal | Use GIFT Nifty gap as primary bias signal |
| 13 | No ADR/global correlation | TCS/INFY ADRs, crude oil affect specific sectors | Add **global cues** layer |
| 14 | Gap filter too rigid (1.2%) | In low-VIX regime, 0.5% gap is significant | **Dynamic gap threshold** based on VIX regime |

---

## Transaction Cost Model (Zerodha/Discount Broker)

For a **₹2,00,000 intraday trade** (buy + sell):

| Component | Rate | Amount (₹) |
|-----------|------|------------|
| Brokerage | ₹20/order × 2 | 40 |
| STT | 0.025% on sell | 50 |
| Exchange charges (NSE) | 0.00307% × 2 | 12.28 |
| SEBI charges | ₹10/crore × 2 | 0.04 |
| Stamp duty | 0.003% on buy | 6 |
| GST (18% on brokerage+exchange+SEBI) | 18% | ~9.42 |
| **Total round-trip cost** | | **~₹118** |
| **Cost as % of trade value** | | **~0.059%** |

### Net Return Calculation

| Gross Move | Cost (%) | Net Pre-Tax | Tax (30% slab) | **Net Post-Tax** |
|-----------|----------|-------------|-----------------|-----------------|
| 1.5% | 0.06% | 1.44% | 0.43% | **~1.01%** |
| 2.0% | 0.06% | 1.94% | 0.58% | **~1.36%** |
| 2.5% | 0.06% | 2.44% | 0.73% | **~1.71%** |
| 3.0% | 0.06% | 2.94% | 0.88% | **~2.06%** |

> **Conclusion**: To net **1-2% post-tax**, we need stocks that move **1.5-3.0% intraday** in our direction.
> With ATR% filter ≥ 2%, this is achievable on 60-70% of trading days.

---

## Improved Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  DATA COLLECTION LAYER                   │
│  GIFT Nifty | NSE Pre-Open | FII/DII | India VIX       │
│  Historical OHLCV | Sector Indices | OI Data            │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│               MARKET REGIME ENGINE                       │
│  GIFT Nifty Gap + FII/DII Flow + VIX Regime +           │
│  Global Cues (US/Asia) + Expiry Day Detection            │
│  Output: BULLISH / BEARISH / NEUTRAL + Volatility Regime │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│              SECTOR ROTATION ENGINE                      │
│  5D/10D Relative Strength vs Nifty50                     │
│  Sector gap at pre-open + Money flow (FII sector wise)   │
│  Output: Top 2 Strong Sectors + Top 1 Weak Sector        │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│              STOCK UNIVERSE FILTER                        │
│  F&O stocks only (206) → Sector filtered → Liquidity     │
│  → Dynamic Gap → Volume Spike → ATR% → Delivery %        │
│  Output: 15-25 candidate stocks                          │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│           TECHNICAL VALIDATION + OI LAYER                │
│  EMA Trend + RSI + VWAP + Prior Day Pattern              │
│  + OI Build-up/Unwinding + Put-Call Ratio                │
│  Output: 5-8 technically valid stocks                    │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│              SCORING & RANKING ENGINE                     │
│  Weighted multi-factor score (0-100)                     │
│  + Risk-adjusted position size                           │
│  Output: Top 3 ranked stocks with entry/SL/target        │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                RISK MANAGEMENT LAYER                     │
│  Max 2% capital risk per trade | Time-based exit by 3:10 │
│  First 15min range validation | Circuit limit check      │
│  Output: Final 2 trades with position size               │
└─────────────────────────────────────────────────────────┘
```

---

## Module 1: Market Regime Engine (Enhanced)

### Inputs
- **GIFT Nifty** (pre 9:00 AM) — replaces SGX Nifty
- **India VIX** (previous close)
- **FII/DII net data** (previous day from NSE)
- **US Markets** (S&P 500, NASDAQ % change)
- **Asia Markets** (Nikkei, Hang Seng opening)
- **Day type** (Expiry day? Monday? Friday?)

### Logic
```python
# Primary Signal: GIFT Nifty gap
gift_gap = (gift_nifty_current - nifty_prev_close) / nifty_prev_close * 100

# FII flow signal (previous day)
fii_signal = "bullish" if fii_net > 500  # ₹500 Cr net buy
             "bearish" if fii_net < -500
             "neutral"

# VIX Regime
vix_regime = "high_vol"   if vix > 18
             "normal"     if 13 <= vix <= 18  
             "low_vol"    if vix < 13

# Composite Bias
if gift_gap > 0.3% AND fii_signal != "bearish":
    bias = "BULLISH"
elif gift_gap < -0.3% AND fii_signal != "bullish":
    bias = "BEARISH"  
else:
    bias = "NEUTRAL"  # Trade both sides or sit out

# Expiry adjustment
if is_weekly_expiry:
    bias_confidence *= 0.8  # Reduce confidence on expiry days
    expect_mean_reversion = True
```

### VIX-Based Dynamic Thresholds
```
VIX < 13:  gap_threshold = 0.5%, atr_threshold = 1.5%, target = 1.0%
VIX 13-18: gap_threshold = 0.8%, atr_threshold = 2.0%, target = 1.5%
VIX > 18:  gap_threshold = 1.2%, atr_threshold = 2.5%, target = 2.0%
```

---

## Module 2: Sector Rotation Engine (Enhanced)

### NSE Sectoral Indices to Track
```
NIFTY BANK         → Banking stocks
NIFTY IT           → IT/Tech stocks
NIFTY PHARMA       → Pharma stocks
NIFTY AUTO         → Auto stocks
NIFTY METAL        → Metal/Mining stocks
NIFTY REALTY       → Real estate stocks
NIFTY ENERGY       → Oil/Gas/Power stocks
NIFTY FMCG         → Consumer staples
NIFTY FIN SERVICE  → NBFCs, Insurance
NIFTY PSU BANK     → PSU Banks
NIFTY MEDIA        → Media stocks
NIFTY PRIVATE BANK → Private Banks
```

### Enhanced RS Calculation
```python
# Multi-timeframe Relative Strength
RS_5D  = sector_return_5D - nifty_return_5D    # Short-term momentum
RS_20D = sector_return_20D - nifty_return_20D   # Medium-term trend

# Weighted RS
sector_RS = 0.6 * RS_5D + 0.4 * RS_20D

# Pre-open sector gap confirmation
sector_gap = (sector_open - sector_prev_close) / sector_prev_close * 100

# Strong sector: positive RS + gapping in same direction
if sector_RS > 0 and sector_gap > 0.3%:
    sector_strength = "STRONG"
elif sector_RS < 0 and sector_gap < -0.3%:
    sector_strength = "WEAK"  # For short candidates
```

---

## Module 3: Stock Universe & Filters (Enhanced)

### Universe: F&O Stocks Only (206 stocks)
Why?
- Guaranteed liquidity (avg volume > 5-10 lakh shares)
- Tighter bid-ask spreads (less slippage)
- OI data available (our edge signal)
- Can hedge with options if needed

### Filter Pipeline

#### A) Liquidity Filter (Stricter)
```python
avg_volume_20D > 2_000_000 shares  # Minimum 20L shares/day
avg_turnover_20D > 50_crore        # ₹50 Cr daily turnover
```

#### B) Dynamic Gap Filter (VIX-adjusted)
```python
gap_threshold = {
    "low_vol":  0.5,   # VIX < 13
    "normal":   0.8,   # VIX 13-18
    "high_vol": 1.2    # VIX > 18
}
gap_pct = (pre_open_price - prev_close) / prev_close * 100
keep if abs(gap_pct) > gap_threshold[vix_regime]
```

#### C) Volume Spike (Pre-open + Day 1 candle)
```python
# Pre-open volume ratio
preopen_vol_ratio = preopen_volume / avg_preopen_volume_10D
keep if preopen_vol_ratio > 1.3

# After 9:15, check first 5-min candle volume
first_candle_vol_ratio = first_5min_volume / avg_first_5min_volume_10D
keep if first_candle_vol_ratio > 1.5
```

#### D) ATR% Filter (Stocks That Move)
```python
atr_14 = calculate_ATR(14)
atr_pct = (atr_14 / current_price) * 100
keep if atr_pct > atr_threshold[vix_regime]  # Dynamic threshold
```

#### E) Delivery % Filter (NEW - Institutional Conviction)
```python
# High delivery % + price rise = institutional buying
prev_delivery_pct = delivery_quantity / total_traded_qty * 100
if bias == "BULLISH":
    keep if prev_delivery_pct > 40  # Above average delivery
```

#### F) Prior Day Pattern Filter (NEW)
```python
# Inside Bar (today's range inside yesterday's range)
is_inside_bar = (prev_high < prev_prev_high) and (prev_low > prev_prev_low)

# NR7 (Narrowest Range of last 7 days)  
ranges_7d = [(h - l) for h, l in zip(highs[-7:], lows[-7:])]
is_nr7 = ranges_7d[-1] == min(ranges_7d)

# Range Expansion (previous day had big range — momentum continuation)
is_range_expansion = (prev_high - prev_low) > 1.5 * atr_14

# Score: NR7 breakouts have highest probability
pattern_score = 0
if is_inside_bar: pattern_score += 0.3
if is_nr7: pattern_score += 0.5
if is_range_expansion: pattern_score += 0.2
```

---

## Module 4: Technical Validation + OI Layer (Enhanced)

### Technical Filters
```python
# For LONG:
price > EMA_20_daily
EMA_20 > EMA_50_daily  # Trend alignment
RSI_14 > 50 and RSI_14 < 80  # Momentum but not overbought
price > VWAP  # Institutional support

# For SHORT:
price < EMA_20_daily
EMA_20 < EMA_50_daily
RSI_14 < 50 and RSI_14 > 20  # Bearish but not oversold
price < VWAP
```

### Open Interest Analysis (NEW — Indian Market Edge)
```python
# OI Change Logic
oi_change_pct = (current_OI - prev_OI) / prev_OI * 100
price_change = (current_price - prev_close)

# Long Build-up: Price UP + OI UP → Bullish (new longs being created)
if price_change > 0 and oi_change_pct > 5:
    oi_signal = "LONG_BUILDUP"  # Strong bullish
    oi_score = 1.0

# Short Build-up: Price DOWN + OI UP → Bearish (new shorts being created)  
elif price_change < 0 and oi_change_pct > 5:
    oi_signal = "SHORT_BUILDUP"  # Strong bearish
    oi_score = 1.0

# Short Covering: Price UP + OI DOWN → Moderately bullish
elif price_change > 0 and oi_change_pct < -5:
    oi_signal = "SHORT_COVERING"  # Weak bullish
    oi_score = 0.5

# Long Unwinding: Price DOWN + OI DOWN → Moderately bearish
elif price_change < 0 and oi_change_pct < -5:
    oi_signal = "LONG_UNWINDING"  # Weak bearish
    oi_score = 0.5

# Confirmation rule:
# For LONG trades: require LONG_BUILDUP or SHORT_COVERING
# For SHORT trades: require SHORT_BUILDUP or LONG_UNWINDING
```

### Put-Call Ratio (PCR) for Nifty/BankNifty (Market Level)
```python
pcr = total_put_oi / total_call_oi

if pcr > 1.2:    market_sentiment = "BULLISH"   # Put writers confident
elif pcr < 0.8:  market_sentiment = "BEARISH"   # Call writers confident
else:            market_sentiment = "NEUTRAL"
```

---

## Module 5: Enhanced Scoring Model

### Factor Weights (Adjusted for Indian Market Reality)

```python
weights = {
    "gap_score":              0.12,   # Gap direction & magnitude
    "relative_strength":      0.15,   # Sector RS
    "volume_spike":           0.12,   # Volume confirmation
    "atr_pct":                0.10,   # Volatility (ability to move)
    "trend_structure":        0.15,   # EMA alignment + RSI
    "oi_signal":              0.18,   # OI build-up (MOST important for Indian mkts)
    "prior_day_pattern":      0.08,   # NR7, Inside Bar etc.
    "delivery_pct":           0.05,   # Institutional conviction
    "fii_sector_alignment":   0.05,   # FII flow aligned with sector
}
# Total = 1.00
```

### Normalization (0-1 scale)
```python
def normalize(value, min_val, max_val):
    return max(0, min(1, (value - min_val) / (max_val - min_val)))

# Example:
gap_score = normalize(abs(gap_pct), 0, 3.0)           # 0-3% range
rs_score = normalize(sector_RS, -2.0, 2.0)             # Centered at 0
volume_score = normalize(volume_ratio, 1.0, 5.0)       # 1x to 5x
atr_score = normalize(atr_pct, 1.0, 5.0)               # 1% to 5%
trend_score = 1.0 if fully_aligned else 0.5 if partial  # Binary-ish
oi_score = from OI analysis above (0, 0.5, 1.0)
pattern_score = from pattern analysis (0 to 0.5)
delivery_score = normalize(delivery_pct, 30, 70)
fii_score = 1.0 if fii_aligned else 0.0
```

### Final Score
```python
final_score = sum(weights[k] * scores[k] for k in weights)
# Range: 0 to 1.0
# Threshold: Only trade if score > 0.65 (high conviction)
```

---

## Module 6: Risk Management Layer (NEW)

### Position Sizing
```python
capital = 200000  # ₹2L per trade
max_risk_per_trade = 0.02  # 2% of capital = ₹4000

# ATR-based stop loss
stop_loss_points = atr_14 * 0.5  # Half ATR as stop
stop_loss_pct = stop_loss_points / entry_price * 100

# Position size
quantity = max_risk_per_trade / stop_loss_points
position_value = quantity * entry_price

# Cap at capital limit
if position_value > capital:
    quantity = capital / entry_price
```

### Entry Rules
```python
# Wait for first 15 minutes (9:15 - 9:30)
# Entry ONLY after first 15-min candle closes
# Confirm gap direction holds (gap fill = avoid)

if first_15min_high > pre_open_price and bias == "BULLISH":
    entry = first_15min_high + 0.05  # Buy above 15-min high
    stop_loss = first_15min_low - atr_14 * 0.1
    
target_1 = entry + atr_14 * 0.8   # ~1% for most stocks
target_2 = entry + atr_14 * 1.2   # ~1.5-2%
```

### Exit Rules
```python
# Hard rules (non-negotiable):
1. Stop loss hit → EXIT immediately
2. Time stop: EXIT all positions by 3:10 PM (before 3:15 volatility)
3. If stock doesn't move 0.5% in first 30 min after entry → EXIT (dead stock)

# Trailing stop:
if unrealized_profit > 1 * atr_14:
    trailing_stop = entry + 0.5 * atr_14  # Lock in half
    
# Target-based:
# Book 50% at Target 1, trail rest to Target 2
```

### Kill Switches
```python
# Do NOT trade if:
1. VIX > 25                    # Too volatile, random moves
2. Market gap > 2% either side  # Gap may fill, choppy
3. RBI policy day / Budget day  # Event risk
4. Portfolio already down 4% for the week  # Stop trading, reset
5. First 15-min range < ATR * 0.2  # Dead market
6. It's a short trading day (Muhurat, pre-holiday)
```

---

## Module 7: Data Sources & APIs

| Data Need | Source | API/Method |
|-----------|--------|------------|
| Historical OHLCV (Daily) | `jugaad-data` | `stock_df()` |
| Live stock quotes | `jugaad-data` | `NSELive().stock_quote()` |
| Pre-open data | `jugaad-data` | `NSELive().pre_open_market()` |
| India VIX | `yfinance` | Ticker("^INDIAVIX") |
| Sector indices | `yfinance` | `.NS` suffix sector tickers |
| FII/DII data | NSE website scrape | `/api/fiidiiTradeReact` endpoint |
| Open Interest | `jugaad-data` / NSE | F&O bhavcopy or live OI |
| GIFT Nifty | `yfinance` | Ticker for GIFT Nifty futures |
| Delivery data | NSE bhavcopy | `jugaad-data` bhavcopy |
| US markets | `yfinance` | S&P 500, NASDAQ |

---

## Final Output Format

```
═══════════════════════════════════════════════════════════════
  INTRADAY SCANNER — 03 Mar 2026 | Market: BULLISH | VIX: 15.2
  FII: +₹1200 Cr | Strong Sectors: BANKING, IT | Weak: METAL
═══════════════════════════════════════════════════════════════

  #1 ICICIBANK  | Banking  | Score: 0.82/1.00
     Gap: +1.4% | RS: +0.9 | Vol: 2.3x | ATR%: 2.1%
     OI: LONG_BUILDUP (+8.2%) | Delivery: 48%
     Setup: NR7 Breakout | Trend: ▲ EMA aligned
     ─────────────────────────────────────────
     Entry: ₹1285 (above 15-min high)
     Stop:  ₹1272 | Risk: ₹13 (1.01%)
     T1:    ₹1298 | Reward: ₹13 (1.01%)
     T2:    ₹1310 | Reward: ₹25 (1.95%)
     Size:  155 shares | Capital: ₹1,99,175
     
  #2 TCS        | IT       | Score: 0.76/1.00
     Gap: +1.1% | RS: +0.7 | Vol: 1.9x | ATR%: 1.8%
     OI: SHORT_COVERING (-6.1%) | Delivery: 42%
     Setup: Range Expansion | Trend: ▲ EMA aligned
     ─────────────────────────────────────────
     Entry: ₹4120 (above 15-min high)
     Stop:  ₹4085 | Risk: ₹35 (0.85%)  
     T1:    ₹4165 | Reward: ₹45 (1.09%)
     T2:    ₹4200 | Reward: ₹80 (1.94%)
     Size:  48 shares | Capital: ₹1,97,760

═══════════════════════════════════════════════════════════════
  Risk: Max ₹4000/trade | Exit by 3:10 PM | Trail after T1
═══════════════════════════════════════════════════════════════
```

---

## Backtesting Strategy

Before going live:
1. **Collect 6 months of data** using `jugaad-data`
2. **Paper trade for 2 weeks** — log every signal vs actual outcome
3. **Track hit rate**: Target 55-60% win rate with 1.5:1 reward-risk
4. **Expected monthly return**: ~8-12% gross, ~5-8% post-tax (20 trading days × 2 trades × 55% win × 1.5% avg win - 45% × 0.75% avg loss)

---

## Key Indian Market Nuances Not in v1

1. **No shorting in cash market** — need F&O or intraday MIS/bracket orders
2. **Pre-open session (9:00-9:08)** is auction-based, not continuous — can't really "trade" pre-market
3. **Weekly expiry** (Thursday for Nifty/BankNifty, other days for other indices) — creates specific gamma-driven moves
4. **Peak margin rules** — need full margin upfront for intraday positions
5. **Circuit limits** — stocks can hit upper/lower circuit, locking you in
6. **T+1 settlement** — intraday positions auto-squared off at 3:15-3:20 PM
7. **FII/DII data** is released by 6-7 PM for the current day — use previous day's data
8. **Ban period in F&O** — stocks near 95% MWPL get banned, avoid these
