from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.session import Base

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True)
    price = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    vwap = Column(Float)
    rsi = Column(Float)
    macd = Column(String) # Could be float or JSON, keeping string for simplicity now
    ema_9 = Column(Float)
    dma_20 = Column(Float)
    dma_50 = Column(Float)
    dma_200 = Column(Float)
    atr = Column(Float)
    relative_volume = Column(Float)
    relative_strength_spy = Column(Float)
