import pandas as pd
from typing import Dict, Any, Optional
from app.services.indicators import (
    calculate_relative_volume, calculate_relative_strength
)

class BreakoutConsolidationStrategy:
    def name(self) -> str:
        return "Breakout from Consolidation"

    async def analyze(
        self, 
        ticker: str,
        daily_df: pd.DataFrame, 
        spy_df: pd.DataFrame,
        market_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a ticker for a breakout from a tight consolidation range.
        """
        if len(daily_df) < 20:
            return self._wait_signal(ticker, "Insufficient data for 20-day analysis.")

        # 1. Calculate Indicators
        last_20_days = daily_df.tail(20)
        high_20 = last_20_days["high"].max()
        price = float(daily_df["close"].iloc[-1])
        
        # Consolidation check: Range of last 10 days
        last_10_days = daily_df.tail(10)
        range_10 = (last_10_days["high"].max() - last_10_days["low"].min()) / last_10_days["low"].min()
        is_tight = range_10 < 0.05 # Range within 5% over 10 days
        
        rvol = calculate_relative_volume(daily_df)
        rs = calculate_relative_strength(daily_df, spy_df)
        
        # 2. Check Conditions
        near_20d_high = (high_20 - price) / high_20 < 0.015 # Within 1.5% of 20d high
        breakout_attempt = price >= high_20 * 0.995
        volume_expanding = rvol > 1.3
        pos_rs = rs > 1.05
        
        market_mood = market_regime.get("mood", "neutral")
        market_ok = market_mood in ["bullish", "neutral_positive"]

        # 3. Decision Logic
        if not market_ok:
            return self._wait_signal(ticker, f"Market regime ({market_mood}) does not support breakout risk.")

        if is_tight and near_20d_high and pos_rs:
            signal_type = "BUY_IF_TRIGGER"
            confidence = 75
            
            if breakout_attempt and volume_expanding:
                signal_type = "BUY"
                confidence = 85

            return {
                "ticker": ticker.upper(),
                "strategy_name": self.name(),
                "signal_type": signal_type,
                "confidence": confidence,
                "entry_type": "Stop-Limit",
                "entry_trigger": f"Price break and hold above ${round(high_20, 2)} with volume > 1.5x avg",
                "entry_price": round(high_20 + 0.10, 2),
                "stop_loss": round(high_20 * 0.9985, 2), # Tighter stop at -0.15%
                "take_profit": round(price * 1.004, 2), # Scalp target 0.4%
                "invalidation_rule": "Closing back inside the consolidation range -0.15%",
                "timeframe": "Intraday Scalp",
                "reason": f"Consolidation range is tight ({round(range_10*100, 1)}% over 10 days). Relative strength is positive.",
                "risk_note": "Watch for 'fakeouts' if volume does not sustain the break. Stop is placed at the bottom of the base.",
                "status": "ACTIVE"
            }

        if price > high_20 * 1.05:
            return self._wait_signal(ticker, "Price is too extended from the consolidation base.")

        return self._wait_signal(ticker, "Watching for range contraction and volume expansion near 20-day high.")

    def _wait_signal(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": "WAIT",
            "confidence": 50,
            "reason": reason,
            "status": "ACTIVE"
        }

breakout_consolidation_strategy = BreakoutConsolidationStrategy()
