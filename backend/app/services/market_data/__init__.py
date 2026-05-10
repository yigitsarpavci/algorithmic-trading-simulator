from app.core.config import settings
from .base import MarketDataProvider
from .mock_provider import MockProvider
from .yfinance_provider import YFinanceProvider

def get_market_data_provider() -> MarketDataProvider:
    if settings.MARKET_DATA_PROVIDER.lower() == "yfinance":
        return YFinanceProvider()
    return MockProvider()

market_data = get_market_data_provider()
