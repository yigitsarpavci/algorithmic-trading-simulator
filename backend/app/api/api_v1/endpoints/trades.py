from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db.session import get_db
from sqlalchemy.sql import func

router = APIRouter()

from app.services.paper_trading import paper_trading_service

@router.get("/", response_model=List[schemas.PaperTrade])
def read_trades(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve paper trades.
    """
    trades = db.query(models.PaperTrade).order_by(models.PaperTrade.opened_at.desc().nullslast()).offset(skip).limit(limit).all()
    return trades

@router.get("/summary")
def get_trade_summary(db: Session = Depends(get_db)) -> Any:
    """
    Get paper trading summary metrics.
    """
    # 1. Total count for the whole history
    total_history = db.query(models.PaperTrade).filter(models.PaperTrade.status.like("CLOSED%")).count()
    
    # 2. Last 200 closed trades for "Recent" performance metrics
    recent_trades = db.query(models.PaperTrade).filter(
        models.PaperTrade.status.like("CLOSED%")
    ).order_by(models.PaperTrade.opened_at.desc()).limit(200).all()
    
    recent_total = len(recent_trades)
    recent_wins = len([t for t in recent_trades if t.pnl_percent is not None and t.pnl_percent > 0])
    total_pnl = sum([t.pnl_dollar for t in recent_trades if t.pnl_dollar is not None])
    
    return {
        "closedTrades": total_history,
        "wins": recent_wins,
        "losses": recent_total - recent_wins,
        "winRate": round((recent_wins / recent_total * 100), 2) if recent_total > 0 else 0,
        "totalReturn": round(sum([t.pnl_percent for t in recent_trades if t.pnl_percent is not None]), 2) if recent_total > 0 else 0,
        "totalPnlDollar": round(total_pnl, 2),
        "active_trades": db.query(models.PaperTrade).filter(models.PaperTrade.status == "OPEN").count(),
        "pending_triggers": db.query(models.PaperTrade).filter(models.PaperTrade.status == "PENDING_TRIGGER").count()
    }

@router.post("/update")
async def update_trades(db: Session = Depends(get_db)) -> Any:
    """
    Update all active and pending paper trades based on current market data.
    """
    await paper_trading_service.update_all_trades(db)
    return {"message": "All paper trades updated successfully."}

@router.post("/open-from-signal/{signal_id}", response_model=schemas.PaperTrade)
async def open_trade(signal_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Manually open a paper trade from an existing signal.
    """
    signal = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    trade = await paper_trading_service.open_from_signal(db, signal)
    return trade
