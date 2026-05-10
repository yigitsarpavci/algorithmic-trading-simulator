from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class StrategyPerformanceBase(BaseModel):
    strategy_name: str
    time_window: Optional[str] = None
    total_trades: int
    win_rate: float
    avg_return: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    current_weight: float

class StrategyPerformance(StrategyPerformanceBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModelUpdateBase(BaseModel):
    update_summary: str
    changed_weights_json: Any
    reason: str

class ModelUpdate(ModelUpdateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
