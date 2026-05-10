import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from .base import MarketDataProvider

class MockProvider(MarketDataProvider):
    async def get_quote(self, ticker: str) -> Dict[str, Any]:
        price = 100.0 + random.uniform(-10, 50)
        return {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "change": round(random.uniform(-2, 2), 2),
            "volume": random.randint(100000, 1000000),
            "timestamp": datetime.now().isoformat(),
            "provider": "mock"
        }

    async def get_intraday_candles(self, ticker: str, interval: str = "5m") -> List[Dict[str, Any]]:
        candles = []
        base_price = 150.0
        now = datetime.now()
        for i in range(20):
            base_price += random.uniform(-1, 1)
            candles.append({
                "time": (now - timedelta(minutes=i*5)).isoformat(),
                "open": round(base_price, 2),
                "high": round(base_price + random.uniform(0, 0.5), 2),
                "low": round(base_price - random.uniform(0, 0.5), 2),
                "close": round(base_price + random.uniform(-0.2, 0.2), 2),
                "volume": random.randint(1000, 5000)
            })
        return candles

    async def get_daily_candles(self, ticker: str) -> List[Dict[str, Any]]:
        candles = []
        base_price = 200.0
        now = datetime.now()
        for i in range(30):
            base_price += random.uniform(-5, 5)
            candles.append({
                "time": (now - timedelta(days=i)).isoformat(),
                "open": round(base_price, 2),
                "high": round(base_price + random.uniform(0, 5), 2),
                "low": round(base_price - random.uniform(0, 5), 2),
                "close": round(base_price + random.uniform(-2, 2), 2),
                "volume": random.randint(1000000, 5000000)
            })
        return candles

    async def get_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for ticker in tickers:
            results[ticker.upper()] = await self.get_quote(ticker)
        return results
