from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MarketSnapshotBase(BaseModel):
    ticker: str
    timestamp: datetime
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[str] = None
    ema_9: Optional[float] = None
    dma_20: Optional[float] = None
    dma_50: Optional[float] = None
    dma_200: Optional[float] = None
    atr: Optional[float] = None
    relative_volume: Optional[float] = None
    relative_strength_spy: Optional[float] = None

class MarketSnapshotCreate(MarketSnapshotBase):
    pass

class MarketSnapshot(MarketSnapshotBase):
    id: int

    class Config:
        from_attributes = True
