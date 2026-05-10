import yfinance as yf
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import MarketDataProvider
import asyncio

class YFinanceProvider(MarketDataProvider):
    async def get_quote(self, ticker: str) -> Dict[str, Any]:
        try:
            # yfinance is synchronous, wrapping in executor for safety
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            info = await loop.run_in_executor(None, lambda: stock.info)
            
            return {
                "ticker": ticker.upper(),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "change": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "timestamp": datetime.now().isoformat(),
                "provider": "yfinance"
            }
        except Exception as e:
            return {"error": str(e), "ticker": ticker, "provider": "yfinance"}

    async def get_intraday_candles(self, ticker: str, interval: str = "5m") -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            # period '1d' for intraday
            df = await loop.run_in_executor(None, lambda: stock.history(period="1d", interval=interval))
            
            return self._df_to_candles(df)
        except Exception as e:
            return []

    async def get_daily_candles(self, ticker: str) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            stock = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            df = await loop.run_in_executor(None, lambda: stock.history(period="1mo", interval="1d"))
            
            return self._df_to_candles(df)
        except Exception as e:
            return []

    async def get_batch_quotes(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        try:
            loop = asyncio.get_event_loop()
            # yf.download is much faster for batches and prevents rate limiting / hanging
            tickers_str = " ".join(tickers)
            df = await loop.run_in_executor(None, lambda: yf.download(tickers_str, period="1d", group_by="ticker", progress=False))
            
            for ticker in tickers:
                ticker_upper = ticker.upper()
                try:
                    # Handle single ticker vs multiple tickers response structure from yfinance
                    if len(tickers) == 1:
                        ticker_data = df.iloc[-1]
                    else:
                        ticker_data = df[ticker_upper].iloc[-1]
                        
                    results[ticker_upper] = {
                        "ticker": ticker_upper,
                        "price": round(float(ticker_data["Close"]), 2),
                        "change": 0.0, # Approximate, requires previous close for exact percent
                        "volume": int(ticker_data["Volume"]),
                        "timestamp": datetime.now().isoformat(),
                        "provider": "yfinance (batch)"
                    }
                except Exception:
                    # Fallback to single quote if data is missing
                    results[ticker_upper] = await self.get_quote(ticker)
        except Exception as e:
            for ticker in tickers:
                results[ticker.upper()] = {"error": str(e), "ticker": ticker}
                
        return results

    def _df_to_candles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        candles = []
        for index, row in df.iterrows():
            candles.append({
                "time": index.isoformat(),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })
        return candles
