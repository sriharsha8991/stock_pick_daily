"""
Trade Plan Generator
Creates actionable trade plans with position sizing and cost estimates.
"""

import pandas as pd

from config import (
    CAPITAL_PER_TRADE,
    EXIT_TIME,
    MAX_RISK_PCT,
    MAX_TRADES_PER_DAY,
    STOP_LOSS_ATR_MULTIPLE,
    TARGET_1_ATR_MULTIPLE,
    TARGET_2_ATR_MULTIPLE,
)


class TradePlanGenerator:
    """Convert ranked candidates into concrete entry / SL / target plans."""

    def generate(self, ranked: pd.DataFrame) -> list[dict]:
        """Create actionable trade plans for top picks."""
        if ranked.empty:
            return []

        plans: list[dict] = []
        top_n = min(MAX_TRADES_PER_DAY + 1, len(ranked))  # +1 as buffer

        for i in range(top_n):
            row = ranked.iloc[i]
            entry_price = row["close"]
            atr = row["atr"]
            bias = row["bias"]

            # Position sizing
            sl_points = atr * STOP_LOSS_ATR_MULTIPLE
            risk_per_share = sl_points
            max_risk = CAPITAL_PER_TRADE * MAX_RISK_PCT
            quantity = int(max_risk / risk_per_share) if risk_per_share > 0 else 0
            position_value = quantity * entry_price

            if position_value > CAPITAL_PER_TRADE:
                quantity = int(CAPITAL_PER_TRADE / entry_price)
                position_value = quantity * entry_price

            if bias == "LONG":
                sl = entry_price - sl_points
                t1 = entry_price + atr * TARGET_1_ATR_MULTIPLE
                t2 = entry_price + atr * TARGET_2_ATR_MULTIPLE
            else:
                sl = entry_price + sl_points
                t1 = entry_price - atr * TARGET_1_ATR_MULTIPLE
                t2 = entry_price - atr * TARGET_2_ATR_MULTIPLE

            risk_pct = (sl_points / entry_price) * 100
            reward_t1_pct = (atr * TARGET_1_ATR_MULTIPLE / entry_price) * 100
            reward_t2_pct = (atr * TARGET_2_ATR_MULTIPLE / entry_price) * 100

            # Transaction cost estimate
            brokerage = 40  # ₹20 each side
            stt = position_value * 0.00025
            exchange = position_value * 2 * 0.0000307
            stamp = position_value * 0.00003
            gst = (brokerage + exchange) * 0.18
            total_cost = brokerage + stt + exchange + stamp + gst
            cost_pct = (total_cost / position_value) * 100 if position_value > 0 else 0

            plans.append({
                "rank": i + 1,
                "symbol": row["symbol"],
                "sector": row["sector"],
                "bias": bias,
                "score": row["final_score"],
                "entry": round(entry_price, 2),
                "stop_loss": round(sl, 2),
                "target_1": round(t1, 2),
                "target_2": round(t2, 2),
                "quantity": quantity,
                "position_value": round(position_value, 0),
                "risk_pct": round(risk_pct, 2),
                "reward_t1_pct": round(reward_t1_pct, 2),
                "reward_t2_pct": round(reward_t2_pct, 2),
                "rr_ratio": round(reward_t1_pct / risk_pct, 2) if risk_pct > 0 else 0,
                "total_cost": round(total_cost, 2),
                "cost_pct": round(cost_pct, 3),
                "gap_pct": row["gap_pct"],
                "sector_rs": row["sector_rs"],
                "volume_ratio": row["volume_ratio"],
                "atr_pct": row["atr_pct"],
                "rsi": row["rsi"],
                "oi_signal": row["oi_signal"],
                "delivery_pct": row["delivery_pct"],
                "is_nr7": row.get("is_nr7", False),
                "is_inside_bar": row.get("is_inside_bar", False),
                "pattern_score": row.get("pattern_score", 0),
                "trend_aligned": row["trend_aligned"],
                "exit_time": EXIT_TIME,
            })

        return plans
