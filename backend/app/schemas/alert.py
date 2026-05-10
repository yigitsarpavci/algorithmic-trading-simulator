from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertBase(BaseModel):
    type: str
    ticker: Optional[str] = None
    message: str

class AlertCreate(AlertBase):
    user_id: int

class Alert(AlertBase):
    id: int
    user_id: int
    created_at: datetime
    read: bool

    class Config:
        from_attributes = True
