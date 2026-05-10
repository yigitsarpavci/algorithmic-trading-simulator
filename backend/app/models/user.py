from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    risk_profile = Column(String, default="Moderate") # Aggressive, Moderate, Conservative
    portfolio_value = Column(Float, default=100000.0) # Paper trading start
    preferred_timeframe = Column(String, default="1-5 Days")
    max_risk_per_trade = Column(Float, default=0.01) # 1%
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    watchlist_items = relationship("WatchlistItem", back_populates="owner")
    signals = relationship("Signal", back_populates="user")
    trades = relationship("PaperTrade", back_populates="user")

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True, nullable=False)
    asset_type = Column(String) # Stock, ETF
    priority = Column(String) # High, Medium, Low
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="watchlist_items")
