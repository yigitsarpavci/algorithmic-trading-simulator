from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaperTradeBase(BaseModel):
    ticker: str
    paper_entry_price: Optional[float] = None
    quantity: int
    status: str = "OPEN"

class PaperTradeCreate(PaperTradeBase):
    signal_id: int
    user_id: int

class PaperTrade(PaperTradeBase):
    id: int
    signal_id: int
    user_id: int
    paper_exit_price: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    pnl_percent: Optional[float] = None
    pnl_dollar: Optional[float] = None
    max_favorable_excursion: Optional[float] = None
    max_adverse_excursion: Optional[float] = None
    exit_reason: Optional[str] = None

    class Config:
        from_attributes = True
