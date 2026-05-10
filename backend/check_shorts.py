import sqlite3

conn = sqlite3.connect("backend/alphatrigger.db")
cursor = conn.cursor()
cursor.execute("SELECT paper_trades.ticker, strategy_name, signal_type, pnl_percent FROM paper_trades JOIN signals ON paper_trades.signal_id = signals.id WHERE signals.signal_type = 'SELL' LIMIT 5")
shorts = cursor.fetchall()

print(f"Found {len(shorts)} short trades executed!")
for s in shorts:
    print(f"Ticker: {s[0]} | Strategy: {s[1]} | Type: {s[2]} | PnL: {s[3]}%")
