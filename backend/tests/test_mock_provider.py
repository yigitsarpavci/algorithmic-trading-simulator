import asyncio

from app.services.market_data.mock_provider import MockProvider

provider = MockProvider()


def run(coro):
    return asyncio.run(coro)


def test_quote_shape_and_ticker_normalization():
    quote = run(provider.get_quote("btc-usd"))
    assert quote["ticker"] == "BTC-USD"
    assert quote["provider"] == "mock"
    assert 90 <= quote["price"] <= 150
    assert -2 <= quote["change"] <= 2


def test_batch_quotes_cover_every_requested_ticker():
    quotes = run(provider.get_batch_quotes(["eth-usd", "sol-usd"]))
    assert set(quotes) == {"ETH-USD", "SOL-USD"}


def test_candle_series_are_well_formed():
    for candles, expected in ((run(provider.get_intraday_candles("X")), 20), (run(provider.get_daily_candles("X")), 30)):
        assert len(candles) == expected
        for c in candles:
            assert c["high"] >= c["low"]
            assert c["volume"] > 0
            assert {"time", "open", "high", "low", "close", "volume"} <= set(c)
