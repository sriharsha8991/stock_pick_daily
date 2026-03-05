"""
Stock Filter Pipeline
Applies liquidity, gap, volume, ATR, delivery, pattern, and trend filters.
"""

import logging

import pandas as pd

from config import (
    ALL_FNO_STOCKS,
    FII_BEARISH_THRESHOLD,
    FII_BULLISH_THRESHOLD,
    MIN_AVG_VOLUME,
    SECTOR_STOCKS,
    VIX_REGIMES,
)
from data.fetcher import DataFetcher
from indicators_pkg.technical import add_all_indicators
from indicators_pkg.patterns import detect_prior_day_patterns
from indicators_pkg.oi_analysis import analyse_oi_signal, check_trend_alignment

logger = logging.getLogger(__name__)


class StockFilter:
    """Filter candidate stocks through the multi-step pipeline."""

    def __init__(
        self,
        fetcher: DataFetcher,
        *,
        market_bias: str = "NEUTRAL",
        vix_regime: str = "normal",
        fii_dii: dict | None = None,
        sector_rs: dict | None = None,
        strong_sectors: list[str] | None = None,
        weak_sectors: list[str] | None = None,
    ):
        self.fetcher = fetcher
        self.market_bias = market_bias
        self.vix_regime = vix_regime
        self.fii_dii = fii_dii or {}
        self.sector_rs = sector_rs or {}
        self.strong_sectors = strong_sectors or []
        self.weak_sectors = weak_sectors or []

    def run(self) -> pd.DataFrame:
        """
        Execute the full filtering pipeline.
        Returns a DataFrame of candidate stocks with indicators attached.
        """
        # Determine which stocks to scan based on bias & sectors.
        # Always include strong + weak sectors so we have a wide enough
        # universe.  The bias just decides the *direction* for each stock,
        # not whether to exclude whole sectors.
        if self.market_bias == "BULLISH":
            # Primary: strong sectors, secondary: all others
            primary_sectors = self.strong_sectors
        elif self.market_bias == "BEARISH":
            # Primary: weak sectors (shorts), but also include strong
            # sectors for potential contra-trend longs
            primary_sectors = self.weak_sectors + self.strong_sectors
        else:
            primary_sectors = self.strong_sectors + self.weak_sectors

        # Build candidate list: primary sectors first, then fill from
        # ALL F&O stocks so we never scan fewer than 30 symbols.
        candidate_symbols: list[str] = []
        for sector in primary_sectors:
            candidate_symbols.extend(SECTOR_STOCKS.get(sector, []))

        # If that's still thin, add remaining sectors
        if len(candidate_symbols) < 30:
            for sector, stocks in SECTOR_STOCKS.items():
                if sector not in primary_sectors:
                    candidate_symbols.extend(stocks)

        # De-dup while preserving order
        seen: set[str] = set()
        candidate_symbols = [s for s in candidate_symbols if not (s in seen or seen.add(s))]

        if not candidate_symbols:
            candidate_symbols = ALL_FNO_STOCKS[:50]

        logger.info(
            "Scanning %d candidate stocks (primary sectors: %s)",
            len(candidate_symbols),
            primary_sectors,
        )

        # Fetch historical data (the heavy I/O step)
        stock_data = self.fetcher.get_bulk_historical(candidate_symbols, days=180)

        regime_params = VIX_REGIMES[self.vix_regime]
        gap_threshold = regime_params["gap_threshold"]
        atr_threshold = regime_params["atr_threshold"]

        logger.info(
            "Filter params  vix_regime=%s  gap_thresh=%.2f%%  atr_thresh=%.2f%%  min_vol=%d",
            self.vix_regime, gap_threshold, atr_threshold, MIN_AVG_VOLUME,
        )

        rows: list[dict] = []
        _dropped: dict[str, int] = {"rows": 0, "liquidity": 0, "gap": 0, "atr": 0}
        for symbol, df in stock_data.items():
            try:
                if len(df) < 50:
                    _dropped["rows"] += 1
                    continue

                # Add indicators
                df = add_all_indicators(df)
                last = df.iloc[-1]

                # ── A) Liquidity filter ──
                avg_vol = last.get("vol_avg_20", 0)
                if avg_vol < MIN_AVG_VOLUME:
                    _dropped["liquidity"] += 1
                    continue

                # ── B) Gap filter ──
                gap_pct = last.get("gap_pct", 0)
                if abs(gap_pct) < gap_threshold:
                    _dropped["gap"] += 1
                    continue

                # ── C) Volume spike ──
                vol_ratio = last.get("volume_ratio", 0)

                # ── D) ATR% filter ──
                atr_pct = last.get("atr_pct", 0)
                if atr_pct < atr_threshold:
                    _dropped["atr"] += 1
                    continue

                # ── E) Delivery % filter ──
                delivery_pct = 0.0
                if "delivery_qty" in df.columns and "volume" in df.columns:
                    dq = df["delivery_qty"].iloc[-1] if not pd.isna(df["delivery_qty"].iloc[-1]) else 0
                    v = df["volume"].iloc[-1] if df["volume"].iloc[-1] > 0 else 1
                    delivery_pct = (dq / v) * 100

                # ── F) Prior-day patterns ──
                patterns = detect_prior_day_patterns(df)

                # ── G) Trend alignment ──
                bias_for_stock = (
                    "long"
                    if self.market_bias in ("BULLISH", "NEUTRAL") and gap_pct > 0
                    else "short"
                )
                is_aligned, trend_score = check_trend_alignment(last, bias=bias_for_stock)

                # ── H) OI signal (placeholder — real OI needs F&O bhavcopy) ──
                price_change = (
                    last["close"] - last["prev_close"] if "prev_close" in last.index else 0
                )
                oi_change_pct = (vol_ratio - 1) * 20  # crude proxy
                oi_signal, oi_score = analyse_oi_signal(price_change, oi_change_pct)

                # ── Sector for this stock ──
                stock_sector = "UNKNOWN"
                for sec, syms in SECTOR_STOCKS.items():
                    if symbol in syms:
                        stock_sector = sec
                        break

                # ── Sector RS score ──
                sec_rs_info = self.sector_rs.get(stock_sector, {})
                sec_rs = sec_rs_info.get("weighted_rs", 0)

                # ── FII alignment ──
                fii_aligned = (
                    (self.fii_dii.get("fii_net", 0) > FII_BULLISH_THRESHOLD and bias_for_stock == "long")
                    or (self.fii_dii.get("fii_net", 0) < FII_BEARISH_THRESHOLD and bias_for_stock == "short")
                )

                rows.append({
                    "symbol": symbol,
                    "sector": stock_sector,
                    "bias": bias_for_stock.upper(),
                    "close": round(last["close"], 2),
                    "gap_pct": round(gap_pct, 2),
                    "atr": round(last["atr"], 2),
                    "atr_pct": round(atr_pct, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "avg_volume": int(avg_vol),
                    "delivery_pct": round(delivery_pct, 1),
                    "rsi": round(last["rsi"], 1),
                    "ema20": round(last["ema20"], 2),
                    "ema50": round(last["ema50"], 2),
                    "trend_aligned": is_aligned,
                    "trend_score": trend_score,
                    "oi_signal": oi_signal,
                    "oi_score": oi_score,
                    "pattern_score": patterns["pattern_score"],
                    "is_inside_bar": patterns["is_inside_bar"],
                    "is_nr7": patterns["is_nr7"],
                    "sector_rs": round(sec_rs, 2),
                    "fii_aligned": fii_aligned,
                })

            except Exception as exc:
                logger.warning("Error processing %s: %s", symbol, exc)
                continue

        logger.info(
            "Filter summary: %d passed | dropped → rows<%d: %d, liquidity: %d, gap: %d, atr: %d",
            len(rows), 50, _dropped["rows"], _dropped["liquidity"],
            _dropped["gap"], _dropped["atr"],
        )
        return pd.DataFrame(rows)
