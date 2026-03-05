"""
Core technical indicator computations (EMA, RSI, ATR, VWAP)
and the composite ``add_all_indicators`` helper.
"""

import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume-Weighted Average Price.
    Expects columns: high, low, close, volume.
    """
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cum_tp_vol = (typical_price * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to a daily OHLCV DataFrame.
    Returns the same DataFrame with new columns appended.
    """
    df = df.copy()

    # Moving Averages
    df["ema20"] = compute_ema(df["close"], 20)
    df["ema50"] = compute_ema(df["close"], 50)

    # RSI
    df["rsi"] = compute_rsi(df["close"], 14)

    # ATR
    df["atr"] = compute_atr(df, 14)
    df["atr_pct"] = (df["atr"] / df["close"]) * 100

    # Daily Range
    df["range"] = df["high"] - df["low"]
    df["range_pct"] = (df["range"] / df["close"]) * 100

    # Volume averages
    df["vol_avg_10"] = df["volume"].rolling(10).mean()
    df["vol_avg_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["vol_avg_20"].replace(0, np.nan)

    # Previous close (if not already present)
    if "prev_close" not in df.columns:
        df["prev_close"] = df["close"].shift(1)

    # Gap %
    df["gap_pct"] = ((df["open"] - df["prev_close"]) / df["prev_close"]) * 100

    # EMA slope (rate of change of EMA20 over 5 bars)
    df["ema20_slope"] = df["ema20"].pct_change(5) * 100

    return df
