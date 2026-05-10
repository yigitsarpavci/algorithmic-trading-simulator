import pandas as pd
from typing import Dict, Any

class CryptoMomentumStrategy:
    """
    Ultra-aggressive crypto momentum scalping strategy.
    Designed for 24/7 crypto markets with rapid entry/exit.
    Almost always generates a signal to keep trading active.
    """
    def name(self) -> str:
        return "Crypto Momentum Scalp"

    async def analyze(
        self, 
        ticker: str,
        df: pd.DataFrame, 
        market_regime: Dict[str, Any]
    ) -> Dict[str, Any]:
        if len(df) < 5:
            return self._wait_signal(ticker, "Insufficient data.")

        price = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        
        # Simple momentum: is price moving?
        momentum = (price - prev_close) / prev_close * 100
        
        # Calculate a simple volatility measure
        recent = df["close"].tail(5)
        volatility = (recent.max() - recent.min()) / recent.min() * 100
        
        # For crypto, almost always generate a signal
        if momentum > 0:
            signal_type = "BUY"
            confidence = 80
            reason = f"Bullish momentum: +{momentum:.3f}% | Volatility: {volatility:.2f}%"
        elif momentum < -0.1:
            signal_type = "BUY_WATCH"
            confidence = 65
            reason = f"Dip buy opportunity: {momentum:.3f}% | Volatility: {volatility:.2f}%"
        else:
            signal_type = "BUY"
            confidence = 70
            reason = f"Neutral momentum scalp: {momentum:.3f}% | Volatility: {volatility:.2f}%"

        # Tight scalp margins for crypto
        tp_pct = max(0.002, volatility / 100 * 0.3)  # 0.2% minimum, scales with vol
        sl_pct = max(0.001, volatility / 100 * 0.15)  # 0.1% minimum

        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": signal_type,
            "confidence": confidence,
            "entry_type": "Market",
            "entry_trigger": f"Momentum scalp at ${price:.2f}",
            "entry_price": round(price, 2),
            "stop_loss": round(price * (1 - sl_pct), 2),
            "take_profit": round(price * (1 + tp_pct), 2),
            "invalidation_rule": f"SL at -{sl_pct*100:.2f}%",
            "timeframe": "Crypto Scalp (30s)",
            "reason": reason,
            "risk_note": "Ultra-fast crypto scalp. Automatic 30s timeout.",
            "status": "ACTIVE"
        }

    def _wait_signal(self, ticker: str, reason: str) -> Dict[str, Any]:
        return {
            "ticker": ticker.upper(),
            "strategy_name": self.name(),
            "signal_type": "WAIT",
            "confidence": 0,
            "reason": reason,
            "status": "INACTIVE"
        }

crypto_momentum_strategy = CryptoMomentumStrategy()
