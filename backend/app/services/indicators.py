import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

def calculate_sma(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    return df[column].rolling(window=period).mean()

def calculate_ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(window=period).mean()

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    # Assumes df is for a single day and has 'time' as index or column
    v = df["volume"]
    p = (df["high"] + df["low"] + df["close"]) / 3
    return (p * v).cumsum() / v.cumsum()

def calculate_relative_volume(df: pd.DataFrame, period: int = 20) -> float:
    """Relative volume of the last candle vs average volume."""
    avg_vol = df["volume"].iloc[:-1].tail(period).mean()
    current_vol = df["volume"].iloc[-1]
    return current_vol / avg_vol if avg_vol > 0 else 1.0

def calculate_relative_strength(stock_df: pd.DataFrame, spy_df: pd.DataFrame) -> float:
    """Relative strength of stock vs SPY over the last 20 periods."""
    stock_perf = stock_df["close"].iloc[-1] / stock_df["close"].iloc[-20]
    spy_perf = spy_df["close"].iloc[-1] / spy_df["close"].iloc[-20]
    return stock_perf / spy_perf if spy_perf > 0 else 1.0

def calculate_opening_range(df: pd.DataFrame, minutes: int = 30) -> Dict[str, float]:
    """Calculate high and low of the first N minutes of the session."""
    # Assumes df index is datetime
    start_time = pd.Timestamp(df.index.min())
    end_time = start_time + pd.Timedelta(minutes=minutes)
    opening_df = df.loc[start_time:end_time]
    return {
        "high": float(opening_df["high"].max()),
        "low": float(opening_df["low"].min())
    }

def calculate_previous_day_high_low(df: pd.DataFrame) -> Dict[str, float]:
    """Get high and low of the previous day from daily candles."""
    # Assumes last row is current day, second to last is previous
    prev_day = df.iloc[-2]
    return {
        "high": float(prev_day["high"]),
        "low": float(prev_day["low"])
    }
