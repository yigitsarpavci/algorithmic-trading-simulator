import pandas as pd
import pytest

from app.services.indicators import (
    calculate_atr,
    calculate_relative_volume,
    calculate_rsi,
    calculate_sma,
    calculate_vwap,
)


def _frame():
    return pd.DataFrame({
        "high": [11, 12, 13, 14, 15, 16],
        "low": [9, 10, 11, 12, 13, 14],
        "close": [10, 11, 12, 13, 14, 15],
        "volume": [100, 100, 100, 100, 100, 300],
    })


def test_sma_matches_manual_mean():
    sma = calculate_sma(_frame(), 3)
    assert sma.iloc[-1] == pytest.approx((13 + 14 + 15) / 3)


def test_rsi_is_100_for_monotonic_rise():
    assert calculate_rsi(_frame(), 3).iloc[-1] == pytest.approx(100.0)


def test_atr_equals_constant_range():
    assert calculate_atr(_frame(), 3).iloc[-1] == pytest.approx(2.0)


def test_vwap_is_volume_weighted_typical_price():
    df = _frame().iloc[:2]
    expected = ((10 * 100) + (11 * 100)) / 200
    assert calculate_vwap(df).iloc[-1] == pytest.approx(expected)


def test_relative_volume_compares_last_candle_to_average():
    assert calculate_relative_volume(_frame(), 5) == pytest.approx(3.0)
