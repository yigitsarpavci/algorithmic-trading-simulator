from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SignalBase(BaseModel):
    ticker: str
    strategy_name: str
    signal_type: str
    confidence: int
    entry_type: str
    entry_trigger: str
    entry_price: float
    stop_loss: float
    take_profit: float
    suggested_amount: str
    timeframe: str
    market_regime: str
    reason: str
    risk_note: str
    score_breakdown: Optional[dict] = None
    status: str = "ACTIVE"

class SignalCreate(SignalBase):
    user_id: int

class Signal(SignalBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
