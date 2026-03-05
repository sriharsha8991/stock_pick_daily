"""
Sector Rotation Analyser
Ranks sectors by relative strength vs Nifty 50.
"""

import logging

from config import SECTOR_INDEX_MAP
from data.fetcher import DataFetcher

logger = logging.getLogger(__name__)


class SectorAnalyser:
    """Compute multi-timeframe sector RS and identify strong / weak sectors."""

    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
        self.sector_rs: dict = {}
        self.strong_sectors: list[str] = []
        self.weak_sectors: list[str] = []

    def analyse(self) -> dict:
        """Return sector scores, strong sectors, and weak sectors."""

        # Nifty returns
        nifty_data = self.fetcher.get_index_data("^NSEI", days=30)
        nifty_ret_5d = nifty_ret_20d = 0.0
        if len(nifty_data) >= 20:
            nifty_ret_5d = (
                (nifty_data["close"].iloc[-1] / nifty_data["close"].iloc[-5]) - 1
            ) * 100
            nifty_ret_20d = (
                (nifty_data["close"].iloc[-1] / nifty_data["close"].iloc[-20]) - 1
            ) * 100

        # Sector returns
        sector_ret_5d = self.fetcher.get_sector_returns(SECTOR_INDEX_MAP, period_days=5)
        sector_ret_20d = self.fetcher.get_sector_returns(SECTOR_INDEX_MAP, period_days=20)

        sector_scores: dict = {}
        for sector in SECTOR_INDEX_MAP:
            rs_5d = sector_ret_5d.get(sector, 0) - nifty_ret_5d
            rs_20d = sector_ret_20d.get(sector, 0) - nifty_ret_20d
            weighted_rs = 0.6 * rs_5d + 0.4 * rs_20d
            sector_scores[sector] = {
                "rs_5d": round(rs_5d, 2),
                "rs_20d": round(rs_20d, 2),
                "weighted_rs": round(weighted_rs, 2),
                "return_5d": sector_ret_5d.get(sector, 0),
            }

        self.sector_rs = sector_scores

        # Top 2 strong, top 1 weak
        sorted_sectors = sorted(
            sector_scores.items(), key=lambda x: x[1]["weighted_rs"], reverse=True
        )
        self.strong_sectors = [s[0] for s in sorted_sectors[:2]]
        self.weak_sectors = [s[0] for s in sorted_sectors[-1:]]

        return {
            "sector_scores": sector_scores,
            "strong_sectors": self.strong_sectors,
            "weak_sectors": self.weak_sectors,
        }
