import pytest

from app.services.signal_scoring import SignalScoringEngine

engine = SignalScoringEngine()


class TestTrendScore:
    def test_full_bullish_alignment(self):
        assert engine.calculate_trend_score({"price": 110, "dma_20": 105, "dma_50": 100, "dma_200": 90}) == 100

    def test_short_term_alignment(self):
        assert engine.calculate_trend_score({"price": 110, "dma_20": 105, "dma_50": 100, "dma_200": 120}) == 85

    def test_above_50dma_only(self):
        assert engine.calculate_trend_score({"price": 110, "dma_20": 120, "dma_50": 100, "dma_200": 130}) == 70

    def test_below_200dma_is_weak(self):
        assert engine.calculate_trend_score({"price": 80, "dma_20": 90, "dma_50": 100, "dma_200": 110}) == 20

    def test_missing_data_is_neutral(self):
        assert engine.calculate_trend_score({}) == 50


class TestIntradaySetupScore:
    def test_vwap_pullback_near_vwap_with_neutral_rsi(self):
        score = engine.calculate_intraday_setup_score(
            {"price": 100.2, "vwap": 100.0, "rsi": 50}, "VWAP Pullback"
        )
        assert score == 100  # 90 near VWAP, +10 neutral RSI, capped at 100

    def test_vwap_pullback_above_vwap(self):
        assert engine.calculate_intraday_setup_score(
            {"price": 103, "vwap": 100.0, "rsi": 70}, "VWAP Pullback"
        ) == 70

    def test_overbought_rsi_is_penalized(self):
        assert engine.calculate_intraday_setup_score({"price": 100, "vwap": 100, "rsi": 80}, "Other") == 30

    def test_score_is_clamped_to_0_100(self):
        low = engine.calculate_intraday_setup_score({"rsi": 99}, "Other")
        high = engine.calculate_intraday_setup_score({"price": 100, "vwap": 100, "rsi": 50}, "VWAP Pullback")
        assert 0 <= low <= 100 and 0 <= high <= 100


@pytest.mark.parametrize(
    "rvol,expected",
    [(2.5, 100), (1.8, 85), (1.2, 70), (0.9, 40)],
)
def test_volume_score_thresholds(rvol, expected):
    assert engine.calculate_volume_score({"relative_volume": rvol}) == expected


@pytest.mark.parametrize("rs,expected", [(1.2, 100), (1.02, 80), (0.9, 50)])
def test_relative_strength_score(rs, expected):
    assert engine.calculate_relative_strength_score({"relative_strength_spy": rs}) == expected


def test_news_risk_penalizes_earnings_week():
    assert engine.calculate_news_risk_score({"has_earnings_this_week": True}) == 30
    assert engine.calculate_news_risk_score({}) == 80


def test_historical_score_is_the_win_rate():
    assert engine.calculate_historical_strategy_score({"win_rate": 63}) == 63
    assert engine.calculate_historical_strategy_score({}) == 50


class TestFinalSignal:
    STRONG = {
        "indicators": {
            "price": 100, "dma_20": 95, "dma_50": 90, "dma_200": 80,
            "vwap": 100, "rsi": 50, "relative_volume": 2.5, "relative_strength_spy": 1.2,
        },
        "strategy_name": "VWAP Pullback",
        "strategy_performance": {"win_rate": 70},
        "news_context": {},
    }

    def test_weighted_sum_and_strong_buy(self):
        result = engine.calculate_final_signal_score(90, **self.STRONG)
        # 0.25*90 + 0.20*100 + 0.20*100 + 0.15*100 + 0.10*100 + 0.05*80 + 0.05*70
        assert result["final_score"] == pytest.approx(95.0)
        assert result["signal_type"] == "STRONG_BUY"
        assert set(result["breakdown"]) == {
            "market_regime", "trend", "setup", "volume",
            "relative_strength", "news_risk", "historical_performance",
        }

    def test_avoid_when_everything_is_weak(self):
        weak = {
            "indicators": {"price": 50, "dma_20": 90, "dma_50": 100, "dma_200": 110,
                           "rsi": 90, "relative_volume": 0.5, "relative_strength_spy": 0.8},
            "strategy_name": "Other",
            "strategy_performance": {"win_rate": 20},
            "news_context": {"has_earnings_this_week": True},
        }
        assert engine.calculate_final_signal_score(10, **weak)["signal_type"] == "AVOID"


class _Uniform(SignalScoringEngine):
    """Every component returns the same score, so the weights (which sum to 1.0) give final == score."""

    def __init__(self, value):
        self.value = value

    def calculate_trend_score(self, indicators):
        return self.value

    def calculate_intraday_setup_score(self, indicators, strategy_name):
        return self.value

    def calculate_volume_score(self, indicators):
        return self.value

    def calculate_relative_strength_score(self, indicators):
        return self.value

    def calculate_news_risk_score(self, news_context):
        return self.value

    def calculate_historical_strategy_score(self, strategy_performance):
        return self.value


@pytest.mark.parametrize(
    "score,expected",
    [(100, "STRONG_BUY"), (80, "STRONG_BUY"), (79.9, "BUY"), (65, "BUY"), (64.9, "BUY_WATCH"),
     (55, "BUY_WATCH"), (54.9, "WAIT"), (45, "WAIT"), (44.9, "AVOID"), (0, "AVOID")],
)
def test_signal_type_band_boundaries(score, expected):
    result = _Uniform(score).calculate_final_signal_score(score, {}, "x", {}, {})
    assert result["final_score"] == pytest.approx(score, abs=0.01)
    assert result["signal_type"] == expected
