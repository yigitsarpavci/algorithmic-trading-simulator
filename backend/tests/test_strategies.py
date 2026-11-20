import asyncio

import numpy as np
import pandas as pd
import pytest

from app.services.strategies.crypto_momentum import crypto_momentum_strategy
from app.services.strategies.vwap_pullback import vwap_pullback_strategy


def run(coro):
    return asyncio.run(coro)


def candles(closes, volume=1000):
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame({
        "open": closes, "high": closes * 1.001, "low": closes * 0.999,
        "close": closes, "volume": [volume] * len(closes),
    })


class TestCryptoMomentum:
    def test_waits_without_enough_data(self):
        signal = run(crypto_momentum_strategy.analyze("btc-usd", candles([1, 2, 3]), {}))
        assert signal["signal_type"] == "WAIT" and signal["status"] == "INACTIVE"
        assert signal["ticker"] == "BTC-USD"

    def test_buys_positive_momentum_with_sane_levels(self):
        df = candles([100, 100.1, 100.2, 100.3, 100.5])
        signal = run(crypto_momentum_strategy.analyze("eth-usd", df, {}))
        assert signal["signal_type"] == "BUY" and signal["confidence"] == 80
        assert signal["stop_loss"] < signal["entry_price"] < signal["take_profit"]
        assert signal["entry_type"] == "Market"

    def test_dip_is_a_buy_watch(self):
        df = candles([100, 100, 100, 100, 99.5])
        signal = run(crypto_momentum_strategy.analyze("sol-usd", df, {}))
        assert signal["signal_type"] == "BUY_WATCH" and signal["confidence"] == 65

    def test_flat_market_is_a_neutral_scalp(self):
        signal = run(crypto_momentum_strategy.analyze("ltc-usd", candles([100] * 6), {}))
        assert signal["signal_type"] == "BUY" and signal["confidence"] == 70


class TestVwapPullback:
    def test_needs_twenty_candles(self):
        signal = run(vwap_pullback_strategy.analyze("msft", candles([100] * 10), {"mood": "bullish"}))
        assert signal["signal_type"] == "WAIT"
        assert "Insufficient data" in signal["reason"]

    def test_avoids_longs_in_a_bearish_market(self):
        signal = run(vwap_pullback_strategy.analyze("msft", candles([100] * 30), {"mood": "bearish"}))
        assert signal["signal_type"] == "AVOID" and signal["confidence"] == 20

    def test_waits_when_price_is_below_vwap(self):
        closes = list(np.linspace(100, 110, 29)) + [95]
        signal = run(vwap_pullback_strategy.analyze("msft", candles(closes), {"mood": "neutral"}))
        assert signal["signal_type"] == "WAIT"
        assert "below VWAP" in signal["reason"]

    def test_signal_levels_are_ordered_when_a_setup_triggers(self):
        # Gentle drift keeps price right at VWAP/EMA9 with a neutral RSI.
        closes = 100 + np.sin(np.linspace(0, 6, 40)) * 0.3
        signal = run(vwap_pullback_strategy.analyze("aapl", candles(closes), {"mood": "bullish"}))
        assert signal["signal_type"] in {"BUY", "BUY_WATCH", "WAIT"}
        if signal["signal_type"] in {"BUY", "BUY_WATCH"}:
            assert signal["stop_loss"] < signal["entry_price"]
            assert signal["confidence"] >= 75
