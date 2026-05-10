import asyncio
from app.db.session import SessionLocal
from app.models import WatchlistItem

db = SessionLocal()

new_tickers = [
    "CRM", "ADBE", "SNOW", "PLTR", "DDOG", "CRWD", "NOW", "UBER", "ABNB", "SPOT",
    "RIVN", "LCID", "F", "GM",
    "MARA", "MSTR", "HOOD", "SQ",
    "GS", "MS", "AXP",
    "ABBV", "MRK", "TMO",
    "LMT", "BA", "RTX",
    "NKE", "SBUX", "MCD", "HD"
]

existing = [item.ticker for item in db.query(WatchlistItem).all()]

count = 0
for ticker in new_tickers:
    if ticker not in existing:
        db.add(WatchlistItem(user_id=1, ticker=ticker))
        count += 1

db.commit()
print(f"Added {count} new tickers. Total universe is now {len(existing) + count} tickers.")
