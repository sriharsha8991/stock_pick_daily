Perfect. I’ll give you a **professional-grade scanner blueprint** that you can directly convert into Python.

This is designed for:

* Pre-market stock selection (before trade day starts)
* Intraday continuation probability
* Indian markets (NSE), but adaptable

Since you’re technical, I’ll structure this like a system design doc.

---

# 🎯 Objective

Build a **Pre-Market Intraday Scanner** that outputs:

```
Rank | Symbol | Sector | Gap% | RelStrength | VolumeSpike | ATR% | Bias
```

Return only top 5 high-probability stocks.

---

# 🧠 Scanner Architecture

### Pipeline Flow

```
Data Source
    ↓
Market Bias Engine
    ↓
Sector Strength Engine
    ↓
Stock Filter Engine
    ↓
Technical Validation Layer
    ↓
Scoring & Ranking Model
    ↓
Final Shortlist
```

---

# 1️⃣ Data Inputs Required

You need:

### Daily Data (Last 3–6 months)

* OHLC
* Volume

### Intraday Data (5m or 15m)

* Pre-market price
* VWAP
* Volume

### Market Data

* Nifty index
* Bank Nifty
* India VIX

---

# 2️⃣ Market Bias Engine

### Logic

```python
if Nifty_gap > 0.5% and US_markets_green:
    bias = "Bullish"
elif Nifty_gap < -0.5%:
    bias = "Bearish"
else:
    bias = "Neutral"
```

Optional:

* If VIX > 18 → expect volatile day
* If VIX < 13 → range-bound likely

Output:

```
bias = LongOnly / ShortOnly / Both
```

---

# 3️⃣ Sector Strength Engine

### Step 1: Compute Relative Strength

Formula:

```
RS = (Sector_Return_5D) - (Nifty_Return_5D)
```

If RS > 0 → Outperforming
If RS < 0 → Underperforming

### Step 2: Pre-market Confirmation

```
If sector_gap > 0.7% AND RS positive → strong
```

Output:

```
Top 2 strong sectors
Top 1 weak sector
```

---

# 4️⃣ Stock Filter Engine

Filter stocks inside strong sector.

## A) Liquidity Filter

```python
if avg_daily_volume > 1_000_000:
    keep
```

## B) Gap Filter

```python
gap_pct = (today_open - yesterday_close) / yesterday_close * 100

if abs(gap_pct) > 1.2:
    keep
```

## C) Volume Spike

```python
volume_ratio = premarket_volume / avg_volume_10D

if volume_ratio > 1.5:
    keep
```

## D) Volatility Filter (ATR)

```python
atr_pct = ATR_14 / current_price * 100

if atr_pct > 2:
    keep
```

You want stocks that MOVE.

---

# 5️⃣ Technical Validation Layer

Now apply structure filters.

### For Long Bias:

```python
price > EMA20
EMA20 > EMA50
RSI > 55
price > VWAP
```

### For Short Bias:

```python
price < EMA20
EMA20 < EMA50
RSI < 45
price < VWAP
```

---

# 6️⃣ Scoring Model (Important)

Assign weighted scores:

```python
score = 0

score += gap_weight * normalized_gap
score += rs_weight * relative_strength
score += volume_weight * volume_ratio
score += atr_weight * atr_pct
score += structure_weight (if trend aligned)
```

Example weights:

```
gap: 20%
relative strength: 25%
volume spike: 20%
ATR: 15%
trend structure: 20%
```

Normalize everything 0–1 scale.

---

# 7️⃣ Ranking Logic

```python
stocks.sort(by="score", descending=True)
top5 = stocks.head(5)
```

Return:

```
Symbol
Sector
Gap%
RS score
Volume ratio
ATR%
Trend Direction
Final Score
```

---

# 🏗️ Python Skeleton Code Blueprint

Here is the structural code outline:

```python
import pandas as pd
import numpy as np

class IntradayScanner:

    def __init__(self, stock_data, sector_data, index_data):
        self.stock_data = stock_data
        self.sector_data = sector_data
        self.index_data = index_data

    def calculate_gap(self, df):
        df["gap_pct"] = (
            (df["open"] - df["prev_close"]) / df["prev_close"]
        ) * 100
        return df

    def calculate_relative_strength(self, stock_return, index_return):
        return stock_return - index_return

    def calculate_volume_ratio(self, premarket_vol, avg_vol):
        return premarket_vol / avg_vol

    def calculate_atr_pct(self, atr, price):
        return (atr / price) * 100

    def apply_technical_filters(self, df, bias="long"):
        if bias == "long":
            return df[
                (df["price"] > df["ema20"]) &
                (df["ema20"] > df["ema50"]) &
                (df["rsi"] > 55) &
                (df["price"] > df["vwap"])
            ]
        else:
            return df[
                (df["price"] < df["ema20"]) &
                (df["ema20"] < df["ema50"]) &
                (df["rsi"] < 45) &
                (df["price"] < df["vwap"])
            ]

    def score_stock(self, row):
        score = (
            0.2 * row["gap_score"] +
            0.25 * row["rs_score"] +
            0.2 * row["volume_score"] +
            0.15 * row["atr_score"] +
            0.2 * row["trend_score"]
        )
        return score

    def rank_stocks(self, df):
        df["final_score"] = df.apply(self.score_stock, axis=1)
        return df.sort_values("final_score", ascending=False)

```

---

# ⚡ Advanced Enhancements (Your Edge)

Since you're an AI engineer:

### Add ML Ranking Model

Train XGBoost classifier:

Target:

```
1 if stock moved > 1.5% intraday
0 otherwise
```

Features:

* Gap%
* RS
* Volume ratio
* ATR%
* EMA slope
* Previous day range expansion

Let model rank probability of breakout continuation.

---

# 🛑 Risk Layer

Also build:

```python
if first_15min_range < ATR_14 * 0.3:
    avoid_trade  # Low volatility trap
```

---

# 📈 Final Output Example

```
1. ICICIBANK  | Banking | Gap 1.8% | RS 0.9 | Vol 2.3x | Score 0.84
2. TCS        | IT      | Gap 1.5% | RS 0.7 | Vol 1.9x | Score 0.78
3. RELIANCE   | Energy  | Gap 2.1% | RS 0.6 | Vol 2.1x | Score 0.74
```

Trade only top 1–2.
