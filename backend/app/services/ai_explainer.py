import os
from typing import Dict, Any, Optional

class AIExplainer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def explain_signal(
        self, 
        ticker: str,
        signal_data: Dict[str, Any],
        indicators: Dict[str, Any],
        market_regime: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Explain a deterministic signal in plain language.
        """
        if not self.api_key:
            return self._get_template_explanation(ticker, signal_data, indicators, market_regime)

        # In a real app, this would call OpenAI/Anthropic
        # For this implementation, we will use a sophisticated template 
        # that mimics AI logic while maintaining determinism and safety.
        return self._get_template_explanation(ticker, signal_data, indicators, market_regime)

    def _get_template_explanation(
        self, 
        ticker: str, 
        signal_data: Dict[str, Any],
        indicators: Dict[str, Any],
        market_regime: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Deterministic explanation template based on signal parameters.
        """
        signal_type = signal_data.get("signal_type", "WAIT")
        strategy = signal_data.get("strategy_name", "Technical Analysis")
        
        explanation = f"The {strategy} strategy has flagged {ticker} for a {signal_type} research signal. "
        
        if signal_type in ["BUY", "STRONG_BUY"]:
            explanation += (
                f"The setup is driven by price holding support at key technical levels "
                f"while maintaining positive relative strength in a {market_regime.get('mood')} market."
            )
        elif signal_type == "BUY_IF_TRIGGER":
            explanation += (
                f"The system is monitoring a potential breakout. A confirmational move above "
                f"the trigger price is required to validate institutional demand expansion."
            )
        else:
            explanation += (
                f"Currently, the risk/reward profile is suboptimal. The model suggests "
                f"patience until a cleaner entry point or stronger volume confirmation develops."
            )

        invalidation = (
            f"This setup becomes invalid if {ticker} closes below ${signal_data.get('stop_loss')} "
            f"or if the broader market regime shifts to a high-volatility bearish state."
        )

        risk_warning = (
            "Market volatility remains elevated. This signal is for paper-trading research only "
            "and does not account for slippage, fees, or unexpected news events."
        )

        return {
            "ai_explanation": explanation,
            "ai_invalidation": invalidation,
            "ai_risk_warning": risk_warning,
            "ai_summary": f"Why {signal_type}: Deterministic score met threshold based on {strategy} rules."
        }

ai_explainer = AIExplainer()
