from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class MarketDataProvider(ABC):
    @abstractmethod
    async def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Get real-time price quote."""
        pass

    @abstractmethod
    async def get_intraday_candles(self, ticker: str, interval: str = "5m") -> List[Dict[str, Any]]:
        """Get intraday OHLCV data."""
        pass

    @abstractmethod
    async def get_daily_candles(self, ticker: str) -> List[Dict[str, Any]]:
        """Get daily OHLCV data."""
        pass

    @abstractmethod
    async def get_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get real-time quotes for multiple tickers."""
        pass
