import numpy as np
import pandas as pd
import pytest

from app.services.market_regime import MarketRegimeService

service = MarketRegimeService()


def frame(closes):
    return pd.DataFrame({"close": np.asarray(closes, dtype=float)})


def rising(end):
    return frame(np.linspace(100, end, 60))


def falling():
    return frame(np.linspace(150, 100, 60))


def pullback():
    """Uptrend that dips below the 20DMA but stays above the 50DMA."""
    return frame(list(np.linspace(100, 150, 55)) + [141, 140, 139, 138, 137])


def test_bullish_when_spy_trends_up_and_tech_leads():
    result = service.analyze(rising(150), rising(200), vix_value=12)
    assert result["mood"] == "bullish"
    assert result["risk_level"] == "low"
    assert result["market_regime_score"] == 85
    assert result["best_strategy_today"] == "Opening Range Breakout"
    assert "Tech leadership" in result["explanation"]


def test_neutral_positive_when_tech_does_not_lead():
    result = service.analyze(rising(150), rising(120), vix_value=18)
    assert result["mood"] == "neutral_positive"
    assert result["risk_level"] == "medium"
    assert result["market_regime_score"] == 70
    assert "Broad market" in result["explanation"]


def test_bearish_below_the_50dma_and_high_vix_lowers_the_score():
    result = service.analyze(falling(), falling(), vix_value=30)
    assert result["mood"] == "bearish"
    assert result["risk_level"] == "high"
    assert result["market_regime_score"] == 10  # 20 - 10 for high risk
    assert result["best_strategy_today"] == "Short Gaps"


def test_pullback_is_neutral_and_high_vix_prefers_small_size():
    calm = service.analyze(pullback(), pullback(), vix_value=18)
    assert calm["mood"] == "neutral"
    assert calm["market_regime_score"] == 50
    assert "watch for short-term weakness" in calm["explanation"]

    stressed = service.analyze(pullback(), pullback(), vix_value=30)
    assert stressed["best_strategy_today"] == "Scalping (Low Size)"
    assert stressed["avoid_today"] == "Holding overnight"


@pytest.mark.parametrize("vix,risk", [(10, "low"), (15, "medium"), (22, "medium"), (23, "high")])
def test_vix_buckets(vix, risk):
    assert service.analyze(rising(150), rising(150), vix_value=vix)["risk_level"] == risk


def test_score_is_always_within_bounds():
    for spy in (rising(150), falling(), pullback()):
        for vix in (10, 40):
            assert 0 <= service.analyze(spy, spy, vix_value=vix)["market_regime_score"] <= 100
