from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base

class StrategyPerformance(Base):
    __tablename__ = "strategy_performance"

    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, index=True)
    time_window = Column(String) # DAILY, WEEKLY, ALL_TIME
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_return = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=1.0)
    max_drawdown = Column(Float, default=0.0)
    current_weight = Column(Float, default=1.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ModelUpdate(Base):
    __tablename__ = "model_updates"

    id = Column(Integer, primary_key=True, index=True)
    update_summary = Column(String)
    changed_weights_json = Column(JSON)
    reason = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
