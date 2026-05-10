from typing import Dict, Any
import pandas as pd
from app.services.indicators import calculate_sma

class MarketRegimeService:
    def analyze(self, spy_df: pd.DataFrame, qqq_df: pd.DataFrame, vix_value: float = 15.0) -> Dict[str, Any]:
        """
        Analyze market regime based on SPY, QQQ trends and VIX.
        """
        spy_close = spy_df["close"].iloc[-1]
        spy_dma20 = calculate_sma(spy_df, 20).iloc[-1]
        spy_dma50 = calculate_sma(spy_df, 50).iloc[-1]
        
        qqq_perf = qqq_df["close"].iloc[-1] / qqq_df["close"].iloc[-20]
        spy_perf = spy_df["close"].iloc[-1] / spy_df["close"].iloc[-20]
        
        tech_leadership = qqq_perf > spy_perf
        
        # Mood & Score Logic
        mood = "neutral"
        score = 50
        
        if spy_close > spy_dma20 and spy_close > spy_dma50:
            mood = "bullish" if tech_leadership else "neutral_positive"
            score = 85 if tech_leadership else 70
        elif spy_close < spy_dma20 and spy_close > spy_dma50:
            mood = "neutral"
            score = 50
        elif spy_close < spy_dma50:
            mood = "bearish"
            score = 20
        
        # Risk Level Logic
        risk_level = "medium"
        if vix_value < 15:
            risk_level = "low"
        elif vix_value > 22:
            risk_level = "high"
            score -= 10 # Adjust score for high risk
            
        # Strategy selection
        best_strategy = "VWAP Pullback"
        avoid_today = "Shorting strong trends"
        
        if mood == "bullish":
            best_strategy = "Opening Range Breakout"
            avoid_today = "Counter-trend trades"
        elif mood == "bearish":
            best_strategy = "Short Gaps"
            avoid_today = "Longing pullbacks"
        elif risk_level == "high":
            best_strategy = "Scalping (Low Size)"
            avoid_today = "Holding overnight"

        explanation = f"Market is {mood} with {risk_level} risk. "
        if tech_leadership:
            explanation += "Tech leadership (QQQ) is driving the trend. "
        else:
            explanation += "Broad market performance is leading. "
            
        if spy_close > spy_dma20:
            explanation += "Price is above short-term 20DMA trend. "
        else:
            explanation += "Price is below 20DMA, watch for short-term weakness. "

        return {
            "mood": mood,
            "risk_level": risk_level,
            "best_strategy_today": best_strategy,
            "avoid_today": avoid_today,
            "explanation": explanation,
            "market_regime_score": max(0, min(100, score))
        }

market_regime_service = MarketRegimeService()
