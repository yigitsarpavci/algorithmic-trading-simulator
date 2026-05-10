from typing import Dict, Any

class SignalScoringEngine:
    def calculate_trend_score(self, indicators: Dict[str, Any]) -> float:
        """
        Score based on moving averages and trend alignment.
        """
        score = 50
        price = indicators.get("price", 0)
        dma20 = indicators.get("dma_20", 0)
        dma50 = indicators.get("dma_50", 0)
        dma200 = indicators.get("dma_200", 0)

        if price > dma20 > dma50 > dma200:
            score = 100
        elif price > dma20 > dma50:
            score = 85
        elif price > dma50:
            score = 70
        elif price < dma200:
            score = 20
        
        return score

    def calculate_intraday_setup_score(self, indicators: Dict[str, Any], strategy_name: str) -> float:
        """
        Score based on specific strategy triggers (VWAP, EMA9, RSI).
        """
        score = 50
        price = indicators.get("price", 0)
        vwap = indicators.get("vwap", 0)
        ema9 = indicators.get("ema_9", 0)
        rsi = indicators.get("rsi", 50)

        if strategy_name == "VWAP Pullback":
            if vwap * 0.995 <= price <= vwap * 1.005: # Near VWAP
                score = 90
            elif price > vwap:
                score = 70
        
        if 40 <= rsi <= 60: # Neutral RSI preferred for pullbacks
            score += 10
        elif rsi > 75: # Overbought
            score -= 20
            
        return max(0, min(100, score))

    def calculate_volume_score(self, indicators: Dict[str, Any]) -> float:
        """
        Score based on relative volume (RVOL).
        """
        rvol = indicators.get("relative_volume", 1.0)
        if rvol > 2.0:
            return 100
        if rvol > 1.5:
            return 85
        if rvol > 1.0:
            return 70
        return 40

    def calculate_relative_strength_score(self, indicators: Dict[str, Any]) -> float:
        """
        Score based on RS vs SPY.
        """
        rs = indicators.get("relative_strength_spy", 1.0)
        if rs > 1.05:
            return 100
        if rs > 1.0:
            return 80
        return 50

    def calculate_news_risk_score(self, news_context: Dict[str, Any]) -> float:
        """
        Score based on upcoming events (Earnings, Macro).
        """
        if news_context.get("has_earnings_this_week"):
            return 30 # Higher risk
        return 80 # Default neutral/good

    def calculate_historical_strategy_score(self, strategy_performance: Dict[str, Any]) -> float:
        """
        Score based on historical win rate of the strategy.
        """
        win_rate = strategy_performance.get("win_rate", 50)
        return win_rate # Direct mapping

    def calculate_final_signal_score(
        self, 
        market_regime_score: float,
        indicators: Dict[str, Any],
        strategy_name: str,
        strategy_performance: Dict[str, Any],
        news_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine all scores into a final signal score with breakdown.
        """
        trend_score = self.calculate_trend_score(indicators)
        setup_score = self.calculate_intraday_setup_score(indicators, strategy_name)
        volume_score = self.calculate_volume_score(indicators)
        rs_score = self.calculate_relative_strength_score(indicators)
        news_score = self.calculate_news_risk_score(news_context)
        hist_score = self.calculate_historical_strategy_score(strategy_performance)

        final_score = (
            0.25 * market_regime_score +
            0.20 * trend_score +
            0.20 * setup_score +
            0.15 * volume_score +
            0.10 * rs_score +
            0.05 * news_score +
            0.05 * hist_score
        )

        signal_type = "WAIT"
        if final_score >= 80:
            signal_type = "STRONG_BUY"
        elif final_score >= 65:
            signal_type = "BUY"
        elif final_score >= 55:
            signal_type = "BUY_WATCH"
        elif final_score >= 45:
            signal_type = "WAIT"
        else:
            signal_type = "AVOID"

        return {
            "final_score": round(final_score, 2),
            "signal_type": signal_type,
            "breakdown": {
                "market_regime": round(market_regime_score, 2),
                "trend": round(trend_score, 2),
                "setup": round(setup_score, 2),
                "volume": round(volume_score, 2),
                "relative_strength": round(rs_score, 2),
                "news_risk": round(news_score, 2),
                "historical_performance": round(hist_score, 2)
            }
        }

scoring_engine = SignalScoringEngine()
