"""
Data Fetcher Module
Handles all data retrieval from NSE, Yahoo Finance, and other sources.

Key design decisions:
  - jugaad-data is tried first for NSE-specific data (delivery qty, trades)
  - yfinance is the fallback and is also used for batch downloads
  - All network calls have explicit timeouts (default 15 s per stock)
  - ``get_bulk_historical`` uses ``yf.download()`` for a single batch request
    instead of looping one-by-one (30 stocks in ~5 s vs ~120 min)
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)

# Maximum seconds to wait for a single jugaad-data call
_JUGAAD_TIMEOUT = 15
# Maximum seconds to wait for yfinance batch download
_YF_BATCH_TIMEOUT = 60

# ---------------------------------------------------------------------------
# Attempt to import jugaad-data; fall back gracefully
# ---------------------------------------------------------------------------
try:
    from jugaad_data.nse import NSELive, stock_df
    JUGAAD_AVAILABLE = True
except ImportError:
    JUGAAD_AVAILABLE = False
    logger.warning("jugaad-data not installed. Using yfinance as fallback for NSE data.")


# Shared pool for timeout-wrapped calls.  Using a persistent pool avoids the
# problem where ThreadPoolExecutor.__exit__ blocks until threads finish —
# which defeats the purpose of a timeout.
_TIMEOUT_POOL = ThreadPoolExecutor(max_workers=8)


def _run_with_timeout(fn, timeout: int, *args, **kwargs):
    """Run *fn* in a background thread; raise *FuturesTimeout* after *timeout* seconds."""
    future = _TIMEOUT_POOL.submit(fn, *args, **kwargs)
    return future.result(timeout=timeout)  # raises concurrent.futures.TimeoutError


class DataFetcher:
    """Centralised data-fetcher for the intraday scanner."""

    def __init__(self):
        if JUGAAD_AVAILABLE:
            try:
                self._nse_live = NSELive()
            except Exception:
                self._nse_live = None
        else:
            self._nse_live = None

        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    # ── Historical OHLCV (daily) — single stock ─────────────
    def get_historical_data(
        self,
        symbol: str,
        days: int = 180,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Return daily OHLCV DataFrame for *symbol* (NSE equity)."""
        end = end_date or date.today()
        start = end - timedelta(days=days)

        # --- Try jugaad-data with timeout ---
        if JUGAAD_AVAILABLE:
            try:
                df = _run_with_timeout(
                    stock_df, _JUGAAD_TIMEOUT,
                    symbol=symbol, from_date=start, to_date=end, series="EQ",
                )
                df = df.rename(columns={
                    "DATE": "date", "OPEN": "open", "HIGH": "high",
                    "LOW": "low", "CLOSE": "close", "VOLUME": "volume",
                    "PREV. CLOSE": "prev_close",
                    "NO OF TRADES": "trades",
                })
                if "DELIV_QTY" in df.columns:
                    df = df.rename(columns={"DELIV_QTY": "delivery_qty"})
                elif "DELIV. QTY" in df.columns:
                    df = df.rename(columns={"DELIV. QTY": "delivery_qty"})
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)
                if not df.empty:
                    return df
            except FuturesTimeout:
                logger.warning("jugaad-data timed out for %s after %ds", symbol, _JUGAAD_TIMEOUT)
            except Exception as exc:
                logger.warning("jugaad-data failed for %s: %s – falling back to yfinance", symbol, exc)

        # --- yfinance fallback (append .NS for NSE) ---
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(start=start, end=end, timeout=15)
            if df is not None and not df.empty:
                df = df.reset_index().rename(columns={
                    "Date": "date", "Open": "open", "High": "high",
                    "Low": "low", "Close": "close", "Volume": "volume",
                })
                df["prev_close"] = df["close"].shift(1)
                return df
        except Exception as exc:
            logger.warning("yfinance failed for %s: %s", symbol, exc)

        return pd.DataFrame()

    # ── Index historical data ────────────────────────────────
    def get_index_data(self, index_symbol: str = "^NSEI", days: int = 30) -> pd.DataFrame:
        """Fetch Nifty 50 (or any index) daily data via yfinance."""
        end = date.today()
        start = end - timedelta(days=days)
        try:
            ticker = yf.Ticker(index_symbol)
            df = ticker.history(start=start, end=end, timeout=15)
            if df is None or df.empty:
                logger.warning("No index data returned for %s", index_symbol)
                return pd.DataFrame()
            df = df.reset_index().rename(columns={
                "Date": "date", "Open": "open", "High": "high",
                "Low": "low", "Close": "close", "Volume": "volume",
            })
            return df
        except Exception as exc:
            logger.warning("Index data fetch failed for %s: %s", index_symbol, exc)
            return pd.DataFrame()

    # ── Live stock quote ─────────────────────────────────────
    def get_live_quote(self, symbol: str) -> dict:
        """Get real-time quote from NSE for *symbol*."""
        if self._nse_live is not None:
            try:
                q = _run_with_timeout(self._nse_live.stock_quote, _JUGAAD_TIMEOUT, symbol)
                price_info = q.get("priceInfo", {})
                return {
                    "symbol": symbol,
                    "last_price": price_info.get("lastPrice", 0),
                    "open": price_info.get("open", 0),
                    "prev_close": price_info.get("previousClose", 0),
                    "vwap": price_info.get("vwap", 0),
                    "high": price_info.get("intraDayHighLow", {}).get("max", 0),
                    "low": price_info.get("intraDayHighLow", {}).get("min", 0),
                    "volume": q.get("securityWiseDP", {}).get("quantityTraded", 0),
                    "delivery_qty": q.get("securityWiseDP", {}).get("deliveryQuantity", 0),
                    "delivery_pct": q.get("securityWiseDP", {}).get("deliveryToTradedQuantity", 0),
                }
            except Exception as exc:
                logger.warning("NSELive quote failed for %s: %s", symbol, exc)

        # yfinance live fallback
        try:
            t = yf.Ticker(f"{symbol}.NS")
            info = t.info
            return {
                "symbol": symbol,
                "last_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "open": info.get("open", info.get("regularMarketOpen", 0)),
                "prev_close": info.get("previousClose", info.get("regularMarketPreviousClose", 0)),
                "vwap": 0,
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "volume": info.get("volume", 0),
                "delivery_qty": 0,
                "delivery_pct": 0,
            }
        except Exception as exc:
            logger.warning("yfinance quote failed for %s: %s", symbol, exc)
            return {
                "symbol": symbol, "last_price": 0, "open": 0, "prev_close": 0,
                "vwap": 0, "high": 0, "low": 0, "volume": 0,
                "delivery_qty": 0, "delivery_pct": 0,
            }

    # ── Pre-open market data ─────────────────────────────────
    def get_preopen_data(self) -> pd.DataFrame:
        """Fetch NSE pre-open session data (Nifty 50 constituents)."""
        if self._nse_live is not None:
            try:
                data = _run_with_timeout(
                    self._nse_live.pre_open_market, _JUGAAD_TIMEOUT, "NIFTY",
                )
                rows = []
                for item in data.get("data", []):
                    meta = item.get("metadata", {})
                    rows.append({
                        "symbol": meta.get("symbol"),
                        "open": meta.get("lastPrice", 0),
                        "prev_close": meta.get("previousClose", 0),
                        "change_pct": meta.get("pChange", 0),
                        "final_quantity": meta.get("finalQuantity", 0),
                    })
                return pd.DataFrame(rows)
            except Exception as exc:
                logger.warning("Pre-open data fetch failed: %s", exc)

        return pd.DataFrame()

    # ── India VIX ────────────────────────────────────────────
    def get_india_vix(self) -> float:
        """Return most recent India VIX closing value."""
        try:
            vix = yf.Ticker("^INDIAVIX")
            hist = vix.history(period="5d", timeout=10)
            if hist is not None and not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception as exc:
            logger.warning("India VIX fetch failed: %s", exc)

        # Try NSE direct
        if self._nse_live is not None:
            try:
                data = _run_with_timeout(
                    self._nse_live.live_index, _JUGAAD_TIMEOUT, "INDIA VIX",
                )
                return float(data.get("last", 15))
            except Exception:
                pass
        return 15.0  # safe default

    # ── FII/DII data ─────────────────────────────────────────
    def get_fii_dii_data(self) -> dict:
        """
        Fetch FII / DII activity data from NSE.
        Returns dict with fii_net and dii_net in crores.
        """
        try:
            url = "https://www.nseindia.com/api/fiidiiTradeReact"
            self._session.get("https://www.nseindia.com", timeout=10)
            resp = self._session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                fii_buy = fii_sell = dii_buy = dii_sell = 0
                for entry in data:
                    cat = entry.get("category", "")
                    if "FII" in cat or "FPI" in cat:
                        fii_buy = float(entry.get("buyValue", 0))
                        fii_sell = float(entry.get("sellValue", 0))
                    elif "DII" in cat:
                        dii_buy = float(entry.get("buyValue", 0))
                        dii_sell = float(entry.get("sellValue", 0))
                return {
                    "fii_net": round((fii_buy - fii_sell) / 100, 2),
                    "dii_net": round((dii_buy - dii_sell) / 100, 2),
                    "fii_buy": round(fii_buy / 100, 2),
                    "fii_sell": round(fii_sell / 100, 2),
                }
        except Exception as exc:
            logger.warning("FII/DII data fetch failed: %s", exc)

        return {"fii_net": 0, "dii_net": 0, "fii_buy": 0, "fii_sell": 0}

    # ── GIFT Nifty / Nifty Futures ───────────────────────────
    def get_gift_nifty(self) -> float:
        """Get the latest GIFT Nifty Futures price for pre-market bias."""
        try:
            for ticker_sym in ["^NSEI", "NQ=F"]:
                try:
                    t = yf.Ticker(ticker_sym)
                    hist = t.history(period="1d", timeout=10)
                    if hist is not None and not hist.empty:
                        return float(hist["Close"].iloc[-1])
                except Exception:
                    continue
        except Exception as exc:
            logger.warning("GIFT Nifty fetch failed: %s", exc)
        return 0.0

    # ── US Market Close ──────────────────────────────────────
    def get_us_market_data(self) -> dict:
        """Fetch previous day's S&P 500 and NASDAQ change."""
        result = {"sp500_change_pct": 0.0, "nasdaq_change_pct": 0.0}
        for sym, key in [("^GSPC", "sp500_change_pct"), ("^IXIC", "nasdaq_change_pct")]:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="5d", timeout=10)
                if hist is not None and len(hist) >= 2:
                    prev = hist["Close"].iloc[-2]
                    last = hist["Close"].iloc[-1]
                    result[key] = round(((last - prev) / prev) * 100, 2)
            except Exception:
                pass
        return result

    # ── Sector Index Data (BATCH) ────────────────────────────
    def get_sector_returns(self, sector_map: dict, period_days: int = 5) -> dict:
        """
        Compute sector returns over *period_days*.
        Uses a single ``yf.download()`` batch call for all sector tickers.
        """
        tickers = {sector: info["yf_ticker"] for sector, info in sector_map.items()}
        ticker_list = list(tickers.values())
        results = {sector: 0.0 for sector in sector_map}

        try:
            raw = yf.download(
                ticker_list,
                period=f"{period_days + 10}d",
                group_by="ticker",
                progress=False,
                timeout=20,
                threads=True,
            )
            if raw is None or raw.empty:
                logger.warning("Batch sector download returned no data")
                return results

            for sector, yf_ticker in tickers.items():
                try:
                    if len(ticker_list) == 1:
                        close = raw["Close"]
                    else:
                        close = (
                            raw[yf_ticker]["Close"]
                            if yf_ticker in raw.columns.get_level_values(0)
                            else None
                        )

                    if close is not None and len(close.dropna()) >= period_days:
                        close = close.dropna()
                        recent = close.iloc[-1]
                        past = close.iloc[-period_days]
                        results[sector] = round(((recent - past) / past) * 100, 2)
                except Exception:
                    pass
        except Exception as exc:
            logger.warning("Batch sector download failed: %s – falling back to sequential", exc)
            for sector, info in sector_map.items():
                try:
                    t = yf.Ticker(info["yf_ticker"])
                    hist = t.history(period=f"{period_days + 5}d", timeout=10)
                    if hist is not None and len(hist) >= period_days:
                        recent = hist["Close"].iloc[-1]
                        past = hist["Close"].iloc[-period_days]
                        results[sector] = round(((recent - past) / past) * 100, 2)
                except Exception:
                    pass
        return results

    # ── Bulk stock data (BATCH download) ─────────────────────
    def get_bulk_historical(
        self, symbols: list[str], days: int = 180,
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols.

        Strategy:
          1. Try ``yf.download()`` batch (single HTTP request for ALL symbols).
          2. Fall back to one-by-one ``get_historical_data`` for any missing.

        Returns dict mapping symbol → OHLCV DataFrame.
        """
        end = date.today()
        start = end - timedelta(days=days)
        yf_symbols = [f"{s}.NS" for s in symbols]
        result: dict[str, pd.DataFrame] = {}

        # --- Batch download via yfinance ---
        logger.info("Batch-downloading %d stocks via yfinance …", len(symbols))
        try:
            raw = yf.download(
                yf_symbols,
                start=start,
                end=end,
                group_by="ticker",
                progress=False,
                timeout=_YF_BATCH_TIMEOUT,
                threads=True,
            )
            if raw is not None and not raw.empty:
                for sym, yf_sym in zip(symbols, yf_symbols):
                    try:
                        if len(yf_symbols) == 1:
                            df = raw.copy()
                        else:
                            if yf_sym not in raw.columns.get_level_values(0):
                                continue
                            df = raw[yf_sym].copy()

                        df = df.dropna(subset=["Close"])
                        if df.empty or len(df) < 10:
                            continue

                        df = df.reset_index().rename(columns={
                            "Date": "date", "Open": "open", "High": "high",
                            "Low": "low", "Close": "close", "Volume": "volume",
                        })
                        df["prev_close"] = df["close"].shift(1)
                        result[sym] = df
                    except Exception as exc:
                        logger.debug("Batch parse failed for %s: %s", sym, exc)
        except Exception as exc:
            logger.warning("Batch download failed: %s – falling back to one-by-one", exc)

        # --- Fill any missing symbols one-by-one ---
        missing = [s for s in symbols if s not in result]
        if missing:
            logger.info("Fetching %d missing stocks individually …", len(missing))
            for sym in missing:
                try:
                    df = self.get_historical_data(sym, days=days)
                    if df is not None and not df.empty:
                        result[sym] = df
                except Exception as exc:
                    logger.warning("Failed to fetch %s: %s", sym, exc)

        logger.info("Got data for %d / %d stocks", len(result), len(symbols))
        return result
