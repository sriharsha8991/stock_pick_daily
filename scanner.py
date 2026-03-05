"""
Core Scanner Engine — Thin Orchestrator
Delegates to the focused modules in ``analysis/``.
"""

import logging
from datetime import date

from analysis.market_regime import MarketRegimeAnalyser
from analysis.scoring import ScoringEngine
from analysis.sector_rotation import SectorAnalyser
from analysis.stock_filter import StockFilter
from analysis.trade_plan import TradePlanGenerator
from data.fetcher import DataFetcher

logger = logging.getLogger(__name__)


class IntradayScanner:
    """
    End-to-end pre-market intraday scanner for NSE.

    Each analysis step lives in its own module under ``analysis/``.
    This class wires them together into a single pipeline.

    Usage::

        scanner = IntradayScanner()
        results = scanner.run()
    """

    def __init__(self):
        self.fetcher = DataFetcher()
        self.regime_analyser = MarketRegimeAnalyser(self.fetcher)
        self.sector_analyser = SectorAnalyser(self.fetcher)
        self.scoring_engine = ScoringEngine()
        self.trade_plan_gen = TradePlanGenerator()

    # ═════════════════════════════════════════════════════════
    #  MAIN RUN
    # ═════════════════════════════════════════════════════════
    def run(self) -> dict:
        """Execute the full scanner pipeline. Returns scan results dict."""
        logger.info("=" * 60)
        logger.info("INTRADAY SCANNER — %s", date.today().strftime("%d %b %Y"))
        logger.info("=" * 60)

        # Step 1: Market Regime
        logger.info("Step 1/5: Assessing market regime ...")
        regime = self.regime_analyser.assess()
        if not regime["tradeable"]:
            logger.warning("KILL SWITCH ACTIVE: %s", regime["kill_reasons"])
            return {"regime": regime, "sector_analysis": {}, "candidates": [], "trade_plans": []}

        # Step 2: Sector Analysis
        logger.info("Step 2/5: Analysing sector rotation ...")
        sector_analysis = self.sector_analyser.analyse()

        # Step 3: Stock Filtering
        logger.info("Step 3/5: Filtering stocks ...")
        stock_filter = StockFilter(
            self.fetcher,
            market_bias=self.regime_analyser.market_bias,
            vix_regime=self.regime_analyser.vix_regime,
            fii_dii=self.regime_analyser.fii_dii,
            sector_rs=self.sector_analyser.sector_rs,
            strong_sectors=self.sector_analyser.strong_sectors,
            weak_sectors=self.sector_analyser.weak_sectors,
        )
        candidates = stock_filter.run()
        logger.info("  → %d stocks passed filters", len(candidates))

        # Step 4: Scoring & Ranking
        logger.info("Step 4/5: Scoring & ranking ...")
        ranked = self.scoring_engine.rank(candidates)
        logger.info("  → %d stocks above threshold", len(ranked))

        # Step 5: Trade Plans
        logger.info("Step 5/5: Generating trade plans ...")
        trade_plans = self.trade_plan_gen.generate(ranked)

        return {
            "regime": regime,
            "sector_analysis": sector_analysis,
            "candidates": ranked.to_dict("records") if not ranked.empty else [],
            "trade_plans": trade_plans,
        }
