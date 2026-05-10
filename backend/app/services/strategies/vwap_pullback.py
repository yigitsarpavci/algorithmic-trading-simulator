import pandas as pd
from typing import Dict, Any, Optional
from app.services.indicators import (
    calculate_vwap, calculate_ema, calculate_rsi, 
    calculate_relative_volume, calculate_sma
)

class VWAPPullbackStrategy:
    def name(self) -> str:
        return "VWAP Pullback"

    async def analyze(
        self, 
        ticker: str,
        df: pd.DataFrame, 
        market_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a ticker for a VWAP Pullback setup.
        """
        if len(df) < 20:
            return self._wait_signal(ticker, "Insufficient data for analysis.")

        # 1. Calculate Indicators
        price = float(df["close"].iloc[-1])
        vwap = calculate_vwap(df).iloc[-1]
        ema9 = calculate_ema(df, 9).iloc[-1]
        rsi = calculate_rsi(df, 14).iloc[-1]
        rvol = calculate_relative_volume(df)
        
        # 2. Check Conditions
        is_above_vwap = price > vwap
        is_near_vwap = abs(price - vwap) / vwap < 0.005 # Within 0.5%
        is_near_ema9 = abs(price - ema9) / ema9 < 0.005
        rsi_neutral = 40 <= rsi <= 65
        
        market_mood = market_regime.get("mood", "neutral")
        market_not_bearish = market_mood not in ["bearish", "neutral_negative"]

        # 3. Decision Logic
        if not market_not_bearish:
            return self._avoid_signal(ticker, f"Market regime is {market_mood}. Risk-off for long pullbacks.")

        if is_above_vwap and (is_near_vwap or is_near_ema9) and rsi_neutral:
            confidence = 85 if market_mood == "bullish" else 75
            if rvol > 1.2: confidence += 5
            
            return {
                "ticker": ticker.upper(),
                "strategy_name": self.name(),
                "signal_type": "BUY" if confidence >= 80 else "BUY_WATCH",
                "confidence": confidence,
                "entry_type": "Limit",
                "entry_trigger": "Price bounce from VWAP/9EMA with volume",
                "entry_price": round(max(vwap, ema9), 2),
                "stop_loss": round(min(vwap, ema9) * 0.9985, 2), # 0.15% tight scalp stop
                "take_profit": round(price * 1.004, 2), # 0.4% quick profit
                "invalidation_rule": "Close below VWAP -0.15%",
                "timeframe": "Intraday Scalp",
                "reason": f"Price holding above VWAP/9EMA in a {market_mood} market. RSI cooled to {round(rsi, 1)}.",
                "risk_note": "High volatility around technical levels. Exit if VWAP support breaks.",
                "status": "ACTIVE"
            }

        if not is_above_vwap:
            return self._wait_signal(ticker, "Price below VWAP. Trend not confirmed.")
            
        return self._wait_signal(ticker, "Setup not mature. Watching for deeper pullback to VWAP/9EMA.")

    def _wait_signal(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": "WAIT",
            "confidence": 50,
            "reason": reason,
            "status": "ACTIVE"
        }

    def _avoid_signal(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": "AVOID",
            "confidence": 20,
            "reason": reason,
            "status": "ACTIVE"
        }

vwap_pullback_strategy = VWAPPullbackStrategy()
