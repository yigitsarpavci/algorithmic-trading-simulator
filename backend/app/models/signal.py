from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True, nullable=False)
    strategy_name = Column(String)
    signal_type = Column(String) # STRONG_BUY, BUY, etc.
    confidence = Column(Integer) # 0-100
    entry_type = Column(String)
    entry_trigger = Column(String)
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    suggested_amount = Column(String)
    timeframe = Column(String)
    market_regime = Column(String)
    reason = Column(String)
    risk_note = Column(String)
    score_breakdown = Column(JSON, nullable=True)
    status = Column(String, default="ACTIVE") # ACTIVE, EXPIRED, TRIGGERED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="signals")
    paper_trade = relationship("PaperTrade", back_populates="signal", uselist=False)
