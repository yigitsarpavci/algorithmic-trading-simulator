import asyncio

from app.services.market_data.mock_provider import MockProvider


def run(coro):
    return asyncio.run(coro)


def test_quote_shape_and_ticker_normalization():
    quote = run(MockProvider(seed=1).get_quote("btc-usd"))
    assert quote["ticker"] == "BTC-USD"
    assert quote["provider"] == "mock"
    assert 80_000 <= quote["price"] <= 100_000  # starts near the realistic base price
    assert abs(quote["change"]) < 1.0           # change is measured from the first (open) price
    assert quote["volume"] > 0


def test_prices_follow_a_random_walk_not_random_jumps():
    provider = MockProvider(seed=7)
    prices = [run(provider.get_quote("ETH-USD"))["price"] for _ in range(200)]
    steps = [abs(b / a - 1.0) for a, b in zip(prices, prices[1:])]
    assert max(steps) < 0.02  # no tick moves more than 2%
    assert len(set(prices)) > 50  # but the price does move


def test_same_seed_gives_the_same_sequence():
    first = [run(MockProvider(seed=3).get_quote("SOL-USD"))["price"] for _ in range(1)]
    a, b = MockProvider(seed=3), MockProvider(seed=3)
    seq_a = [run(a.get_quote("SOL-USD"))["price"] for _ in range(10)]
    seq_b = [run(b.get_quote("SOL-USD"))["price"] for _ in range(10)]
    assert seq_a == seq_b and first


def test_change_is_relative_to_the_opening_price():
    provider = MockProvider(seed=5)
    for _ in range(50):
        last = run(provider.get_quote("LINK-USD"))
    expected = (last["price"] / 18.0 - 1) * 100  # LINK-USD opens at its base price
    assert abs(last["change"] - expected) < 0.05


def test_batch_quotes_cover_every_requested_ticker():
    quotes = run(MockProvider(seed=2).get_batch_quotes(["eth-usd", "sol-usd"]))
    assert set(quotes) == {"ETH-USD", "SOL-USD"}


def test_candle_series_are_well_formed():
    provider = MockProvider(seed=4)
    for candles, expected in ((run(provider.get_intraday_candles("X")), 20), (run(provider.get_daily_candles("X")), 30)):
        assert len(candles) == expected
        for c in candles:
            assert c["high"] >= c["low"]
            assert c["volume"] > 0
            assert {"time", "open", "high", "low", "close", "volume"} <= set(c)
