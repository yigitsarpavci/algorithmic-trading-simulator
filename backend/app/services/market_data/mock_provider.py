import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import MarketDataProvider

# Plausible starting prices so the offline demo looks like a real crypto universe.
_BASE_PRICES = {
    "BTC-USD": 90_000.0,
    "ETH-USD": 3_200.0,
    "SOL-USD": 150.0,
    "LINK-USD": 18.0,
    "LTC-USD": 90.0,
}


class MockProvider(MarketDataProvider):
    """Offline market data: an unbiased per-ticker random walk.

    Prices evolve tick to tick (instead of jumping randomly), so the Z-score, momentum and volume
    logic of the trading engine runs on realistic-looking series without any network access.
    The walk has no built-in edge (persistence defaults to 0), so simulated results are meaningless
    as a performance claim; raise `persistence` only to exercise trending behaviour in tests.
    """

    def __init__(self, seed: Optional[int] = None, volatility: float = 0.0012, persistence: float = 0.0):
        self._rng = random.Random(seed)
        self._volatility = volatility
        self._persistence = persistence
        self._open: Dict[str, float] = {}
        self._price: Dict[str, float] = {}
        self._momentum: Dict[str, float] = {}

    def _step(self, ticker: str) -> float:
        t = ticker.upper()
        price = self._price.get(t)
        if price is None:
            price = _BASE_PRICES.get(t, 100.0)
            self._open[t] = price
        # Optional AR(1) momentum (off by default) plus noise.
        momentum = self._momentum.get(t, 0.0) * self._persistence + self._rng.gauss(0, 0.0004)
        self._momentum[t] = momentum
        price *= 1.0 + momentum + self._rng.gauss(0, self._volatility)
        self._price[t] = price
        return price

    async def get_quote(self, ticker: str) -> Dict[str, Any]:
        t = ticker.upper()
        previous = self._price.get(t)
        price = self._step(t)
        move = abs(price / previous - 1.0) if previous else 0.0
        volume = int(self._rng.randint(100_000, 600_000) * (1.0 + move * 1500))
        return {
            "ticker": t,
            "price": round(price, 4 if price < 1 else 2),
            "change": round((price / self._open[t] - 1.0) * 100, 3),
            "volume": volume,
            "timestamp": datetime.now().isoformat(),
            "provider": "mock",
        }

    def _candles(self, ticker: str, count: int, step: timedelta, spread: float, volume_range) -> List[Dict[str, Any]]:
        t = ticker.upper()
        end = self._price.get(t) or _BASE_PRICES.get(t, 100.0)
        now = datetime.now()
        candles, price = [], end
        for i in range(count):
            price *= 1.0 + self._rng.gauss(0, self._volatility * spread)
            body = price * self._rng.uniform(-0.0004, 0.0004) * spread
            candles.append({
                "time": (now - step * i).isoformat(),
                "open": round(price, 2),
                "high": round(price + abs(body) + price * 0.0003 * spread, 2),
                "low": round(price - abs(body) - price * 0.0003 * spread, 2),
                "close": round(price + body, 2),
                "volume": self._rng.randint(*volume_range),
            })
        return candles

    async def get_intraday_candles(self, ticker: str, interval: str = "5m") -> List[Dict[str, Any]]:
        return self._candles(ticker, 20, timedelta(minutes=5), 4.0, (1_000, 5_000))

    async def get_daily_candles(self, ticker: str) -> List[Dict[str, Any]]:
        return self._candles(ticker, 30, timedelta(days=1), 25.0, (1_000_000, 5_000_000))

    async def get_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for ticker in tickers:
            results[ticker.upper()] = await self.get_quote(ticker)
        return results
