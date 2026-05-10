from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class WatchlistItemBase(BaseModel):
    ticker: str
    asset_type: str
    priority: str

class WatchlistItemCreate(WatchlistItemBase):
    pass

class WatchlistItem(WatchlistItemBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    risk_profile: str = "Moderate"
    portfolio_value: float = 100000.0
    preferred_timeframe: str = "1-5 Days"
    max_risk_per_trade: float = 0.01

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    watchlist_items: List[WatchlistItem] = []

    class Config:
        from_attributes = True
