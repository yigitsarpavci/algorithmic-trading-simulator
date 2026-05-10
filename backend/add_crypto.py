from app.db.session import SessionLocal
from app.models import WatchlistItem

db = SessionLocal()

crypto_tickers = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "DOT-USD", "MATIC-USD", "LINK-USD",
    "SHIB-USD", "LTC-USD", "UNI-USD", "ATOM-USD", "APE-USD"
]

existing = [item.ticker for item in db.query(WatchlistItem).all()]

count = 0
for ticker in crypto_tickers:
    if ticker not in existing:
        db.add(WatchlistItem(user_id=1, ticker=ticker))
        count += 1

db.commit()
total = db.query(WatchlistItem).count()
print(f"Added {count} crypto tickers. Total watchlist: {total}")

# Show all crypto tickers in watchlist
cryptos = [item.ticker for item in db.query(WatchlistItem).all() if "-USD" in item.ticker]
print(f"Active crypto tickers: {cryptos}")
db.close()
