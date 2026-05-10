import pandas as pd
from typing import Dict, Any, Optional
from app.services.indicators import (
    calculate_sma, calculate_rsi, calculate_relative_strength
)

class Pullback20DMAStrategy:
    def name(self) -> str:
        return "Pullback to 20DMA"

    async def analyze(
        self, 
        ticker: str,
        daily_df: pd.DataFrame, 
        spy_df: pd.DataFrame,
        market_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a ticker for a 20DMA Pullback swing trade setup.
        """
        if len(daily_df) < 200:
            return self._wait_signal(ticker, "Insufficient daily data for 200DMA analysis.")

        # 1. Calculate Indicators
        price = float(daily_df["close"].iloc[-1])
        dma20 = calculate_sma(daily_df, 20).iloc[-1]
        dma50 = calculate_sma(daily_df, 50).iloc[-1]
        dma200 = calculate_sma(daily_df, 200).iloc[-1]
        rsi = calculate_rsi(daily_df, 14).iloc[-1]
        rs = calculate_relative_strength(daily_df, spy_df)
        
        # 2. Check Conditions
        above_200 = price > dma200
        above_50 = price > dma50
        near_20 = abs(price - dma20) / dma20 < 0.01 # Within 1% of 20DMA
        rsi_cooled = 40 <= rsi <= 55
        pos_rs = rs > 1.0
        
        market_mood = market_regime.get("mood", "neutral")
        market_ok = market_mood not in ["bearish"]

        # 3. Decision Logic
        if above_200 and above_50 and near_20 and rsi_cooled and pos_rs and market_ok:
            return {
                "ticker": ticker.upper(),
                "strategy_name": self.name(),
                "signal_type": "BUY",
                "confidence": 85,
                "entry_type": "Limit / Market",
                "entry_trigger": f"Price holding support at 20DMA (${round(dma20, 2)})",
                "entry_price": round(price, 2),
                "stop_loss": round(price * 0.9985, 2), # Tighter stop at -0.15%
                "take_profit": round(price * 1.004, 2), # Scalp target 0.4%
                "invalidation_rule": "Close below 20DMA -0.15%",
                "timeframe": "Intraday Scalp",
                "reason": f"Classic swing pullback adapted for scalping. RS vs SPY: {round(rs, 2)}.",
                "risk_note": "A break of the 20DMA invalidates the scalp setup. Exit quickly.",
                "status": "ACTIVE"
            }

        if not above_200:
            return self._avoid_signal(ticker, "Below 200DMA. Long-term trend is bearish.")

        return self._wait_signal(ticker, f"Watching for pullback to 20DMA (${round(dma20, 2)}).")

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

pullback_20dma_strategy = Pullback20DMAStrategy()
