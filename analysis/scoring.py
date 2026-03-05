"""
Scoring & Ranking Engine
Applies weighted multi-factor scoring model and ranks stocks.
"""

import pandas as pd

from config import MIN_SCORE_THRESHOLD, SCORING_WEIGHTS
from utils.helpers import normalize


class ScoringEngine:
    """Normalise indicator values, compute weighted score, and rank."""

    def rank(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """
        Apply weighted scoring model and return the ranked DataFrame.
        Only rows exceeding ``MIN_SCORE_THRESHOLD`` are kept.
        """
        if candidates.empty:
            return candidates

        df = candidates.copy()

        # Normalize all factors to 0-1
        df["gap_score"] = df["gap_pct"].abs().apply(lambda x: normalize(x, 0, 3.0))
        df["rs_score"] = df["sector_rs"].apply(lambda x: normalize(x, -2.0, 2.0))
        df["volume_score"] = df["volume_ratio"].apply(lambda x: normalize(x, 1.0, 5.0))
        df["atr_score"] = df["atr_pct"].apply(lambda x: normalize(x, 1.0, 5.0))
        df["delivery_score"] = df["delivery_pct"].apply(lambda x: normalize(x, 30, 70))
        df["fii_score"] = df["fii_aligned"].astype(float)

        # Compute final score
        w = SCORING_WEIGHTS
        df["final_score"] = (
            w["gap_score"] * df["gap_score"]
            + w["relative_strength"] * df["rs_score"]
            + w["volume_spike"] * df["volume_score"]
            + w["atr_pct"] * df["atr_score"]
            + w["trend_structure"] * df["trend_score"]
            + w["oi_signal"] * df["oi_score"]
            + w["prior_day_pattern"] * df["pattern_score"]
            + w["delivery_pct"] * df["delivery_score"]
            + w["fii_sector_alignment"] * df["fii_score"]
        )
        df["final_score"] = df["final_score"].round(3)

        # Filter by minimum threshold
        df = df[df["final_score"] >= MIN_SCORE_THRESHOLD]

        # Sort descending
        df = df.sort_values("final_score", ascending=False).reset_index(drop=True)

        return df
