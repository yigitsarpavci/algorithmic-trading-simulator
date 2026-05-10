from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db.session import get_db

router = APIRouter()

@router.get("/")
async def read_watchlist(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve watchlist items with live market data.
    """
    from app.services.market_data import market_data
    
    items = db.query(models.WatchlistItem).offset(skip).limit(limit).all()
    
    if not items:
        return []
        
    tickers = [item.ticker for item in items]
    quotes = await market_data.get_batch_quotes(tickers)
    
    enriched_items = []
    for item in items:
        quote = quotes.get(item.ticker.upper(), {})
        enriched_items.append({
            "id": item.id,
            "ticker": item.ticker,
            "asset_type": item.asset_type,
            "priority": item.priority,
            "price": quote.get("price", 0),
            "change": quote.get("change", 0),
            "volume": quote.get("volume", "-"),
            "user_id": item.user_id
        })
        
    return enriched_items

@router.post("/", response_model=schemas.WatchlistItem)
def create_watchlist_item(
    *,
    db: Session = Depends(get_db),
    item_in: schemas.WatchlistItemCreate
) -> Any:
    """
    Create new watchlist item.
    """
    item = models.WatchlistItem(
        ticker=item_in.ticker.upper(),
        asset_type=item_in.asset_type,
        priority=item_in.priority,
        user_id=1 # Mock user for now
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{id}", response_model=schemas.WatchlistItem)
def delete_watchlist_item(
    *,
    db: Session = Depends(get_db),
    id: int
) -> Any:
    """
    Delete a watchlist item.
    """
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return item
