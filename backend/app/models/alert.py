from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.db.session import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # SIGNAL_GENERATED, TRIGGER_HIT, SL_HIT, TP_HIT, TRADE_CLOSED, WEIGHT_CHANGED
    ticker = Column(String, nullable=True)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False)
