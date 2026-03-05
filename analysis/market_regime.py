"""
Market Regime Analyser
Determines overall market bias, VIX regime, and institutional flows.
"""

import logging
from datetime import date

from config import (
    FII_BEARISH_THRESHOLD,
    FII_BULLISH_THRESHOLD,
    MAX_MARKET_GAP,
    MAX_VIX_TO_TRADE,
    VIX_REGIMES,
)
from data.fetcher import DataFetcher

logger = logging.getLogger(__name__)


class MarketRegimeAnalyser:
    """Assess VIX regime, FII/DII flows, global cues, and composite bias."""

    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.vix: float = 15.0
        self.vix_regime: str = "normal"
        self.market_bias: str = "NEUTRAL"
        self.fii_dii: dict = {}
        self.us_data: dict = {}
        self.nifty_prev_close: float = 0.0

    def assess(self) -> dict:
        """Run the full market regime assessment and return a summary dict."""

        # ── India VIX ──
        self.vix = self.fetcher.get_india_vix()
        for regime, params in VIX_REGIMES.items():
            if self.vix <= params["vix_max"]:
                self.vix_regime = regime
                break

        # ── FII / DII ──
        self.fii_dii = self.fetcher.get_fii_dii_data()
        fii_net = self.fii_dii.get("fii_net", 0)
        if fii_net > FII_BULLISH_THRESHOLD:
            fii_signal = "bullish"
        elif fii_net < FII_BEARISH_THRESHOLD:
            fii_signal = "bearish"
        else:
            fii_signal = "neutral"

        # ── Nifty previous close & estimated open ──
        nifty_data = self.fetcher.get_index_data("^NSEI", days=5)
        if not nifty_data.empty:
            self.nifty_prev_close = float(nifty_data["close"].iloc[-1])

        # ── US Markets ──
        self.us_data = self.fetcher.get_us_market_data()
        us_bullish = self.us_data.get("sp500_change_pct", 0) > 0.3

        # ── Pre-open or GIFT Nifty gap ──
        preopen = self.fetcher.get_preopen_data()
        if not preopen.empty and self.nifty_prev_close > 0:
            avg_gap = preopen["change_pct"].mean()
        else:
            avg_gap = 0.0

        # ── Composite bias ──
        if avg_gap > 0.3 and fii_signal != "bearish":
            self.market_bias = "BULLISH"
        elif avg_gap < -0.3 and fii_signal != "bullish":
            self.market_bias = "BEARISH"
        elif us_bullish and fii_signal == "bullish":
            self.market_bias = "BULLISH"
        else:
            self.market_bias = "NEUTRAL"

        # ── Expiry detection ──
        today = date.today()
        is_expiry = today.weekday() == 3  # Thursday = weekly expiry

        # ── Kill switches ──
        kill_reasons: list[str] = []
        if self.vix > MAX_VIX_TO_TRADE:
            kill_reasons.append(f"VIX too high: {self.vix:.1f}")
        if abs(avg_gap) > MAX_MARKET_GAP:
            kill_reasons.append(f"Market gap too wide: {avg_gap:.1f}%")

        regime = {
            "bias": self.market_bias,
            "vix": round(self.vix, 2),
            "vix_regime": self.vix_regime,
            "fii_net": fii_net,
            "fii_signal": fii_signal,
            "dii_net": self.fii_dii.get("dii_net", 0),
            "us_sp500_change": self.us_data.get("sp500_change_pct", 0),
            "us_nasdaq_change": self.us_data.get("nasdaq_change_pct", 0),
            "nifty_gap_est": round(avg_gap, 2),
            "is_expiry": is_expiry,
            "kill_reasons": kill_reasons,
            "tradeable": len(kill_reasons) == 0,
        }
        logger.info("Market regime: %s", regime)
        return regime
