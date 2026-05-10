import sqlite3

conn = sqlite3.connect("backend/alphatrigger.db")
try:
    cursor = conn.cursor()
    cursor.execute("SELECT id, portfolio_value FROM users")
    users = cursor.fetchall()
    print("--- User Portfolio ---")
    for u in users:
        print(f"ID: {u[0]} | Portfolio Value: {u[1]}")
        
    cursor.execute("SELECT ticker, paper_entry_price, paper_exit_price, quantity, pnl_dollar, pnl_percent FROM paper_trades WHERE status LIKE 'CLOSED%' ORDER BY pnl_dollar DESC LIMIT 5")
    top_trades = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*), SUM(pnl_dollar) FROM paper_trades WHERE status LIKE 'CLOSED%'")
    agg = cursor.fetchone()
    print(f"\nTotal closed trades: {agg[0]}")
    print(f"Total PnL Dollar from DB: {agg[1]}")
    
    if len(top_trades) > 0:
        print("\n--- Trade Math Check (Top 5 PnL) ---")
        for row in top_trades:
            ticker, entry, exit, qty, pnl_dollar, pnl_pct = row
            print(f"Ticker: {ticker} | Entry: {entry} | Exit: {exit}")
            print(f"  Qty: {qty} | PnL $: {pnl_dollar} | PnL %: {pnl_pct}")
            raw_pnl = ((exit - entry) / entry) if entry else 0
            print(f"  Raw Price Move: {raw_pnl * 100:.4f}%")
            print(f"  Calculated PnL $: {raw_pnl * entry * qty}") # Before leverage
            
except Exception as e:
    print(e)
finally:
    conn.close()
