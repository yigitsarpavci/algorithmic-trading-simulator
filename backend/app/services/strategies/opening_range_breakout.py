import pandas as pd
from typing import Dict, Any, Optional
from app.services.indicators import (
    calculate_opening_range, calculate_vwap, 
    calculate_relative_volume, calculate_relative_strength
)

class OpeningRangeBreakoutStrategy:
    def name(self) -> str:
        return "Opening Range Breakout"

    async def analyze(
        self, 
        ticker: str,
        intraday_df: pd.DataFrame, 
        spy_df: pd.DataFrame,
        market_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a ticker for an Opening Range Breakout (ORB) setup.
        Usually based on the first 30 minutes.
        """
        if len(intraday_df) < 10:
            return self._wait_signal(ticker, "Market just opened. Gathering data.")

        # 1. Calculate OR (30 mins)
        orb = calculate_opening_range(intraday_df, minutes=30)
        or_high = orb["high"]
        or_low = orb["low"]
        or_mid = (or_high + or_low) / 2
        
        price = float(intraday_df["close"].iloc[-1])
        vwap = calculate_vwap(intraday_df).iloc[-1]
        rvol = calculate_relative_volume(intraday_df)
        rs = calculate_relative_strength(intraday_df, spy_df)
        
        # 2. Check Conditions
        is_breakout = price >= or_high
        is_near_high = (or_high - price) / or_high < 0.003 # Within 0.3%
        strong_volume = rvol > 1.5
        pos_rs = rs > 1.05
        market_confirm = market_regime.get("mood") in ["bullish", "neutral_positive"]

        # 3. Decision Logic
        
        # Check if already moved too much
        total_move = (price - or_low) / or_low
        if total_move > 0.05: # 5% move from OR low
            return self._wait_signal(ticker, "Extended after morning move, avoid chasing.")

        if (is_breakout or is_near_high) and strong_volume and pos_rs and market_confirm:
            return {
                "ticker": ticker.upper(),
                "strategy_name": self.name(),
                "signal_type": "BUY_IF_TRIGGER",
                "confidence": 80,
                "entry_type": "Stop-Limit",
                "entry_trigger": f"5-minute candle close above ${round(or_high, 2)} with sustained volume",
                "entry_price": round(or_high + 0.05, 2),
                "stop_loss": round(or_high * 0.9985, 2), # Tighter stop at -0.15%
                "take_profit": round(price * 1.004, 2), # Scalp target 0.4%
                "invalidation_rule": "Close below breakout level -0.15%",
                "timeframe": "Intraday Scalp",
                "reason": f"High volume breakout attempt from 30min opening range. RS: {round(rs, 2)}x SPY.",
                "risk_note": "False breakouts are common if volume fades. Maintain strict stop at VWAP.",
                "status": "ACTIVE"
            }

        return self._wait_signal(ticker, f"Watching for high volume breakout above ${round(or_high, 2)}.")

    def _wait_signal(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": "WAIT",
            "confidence": 50,
            "reason": reason,
            "status": "ACTIVE"
        }

opening_range_breakout_strategy = OpeningRangeBreakoutStrategy()
