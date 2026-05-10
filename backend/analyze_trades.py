import sqlite3

conn = sqlite3.connect("backend/alphatrigger.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT t.pnl_dollar, t.pnl_percent, t.max_favorable_excursion, t.max_adverse_excursion, s.strategy_name, t.ticker
    FROM paper_trades t
    JOIN signals s ON t.signal_id = s.id
    WHERE t.status LIKE 'CLOSED%'
""")
rows = cursor.fetchall()

print("--- TRADE ANALYSIS ---")
print(f"Total Closed Trades: {len(rows)}")

if len(rows) > 0:
    total_pnl = sum(r['pnl_dollar'] for r in rows if r['pnl_dollar'] is not None)
    wins = len([r for r in rows if r['pnl_dollar'] is not None and r['pnl_dollar'] > 0])
    win_rate = (wins / len(rows)) * 100
    
    avg_mfe = sum(r['max_favorable_excursion'] for r in rows if r['max_favorable_excursion'] is not None) / len(rows)
    avg_mae = sum(r['max_adverse_excursion'] for r in rows if r['max_adverse_excursion'] is not None) / len(rows)
    
    print(f"Total PnL ($): {total_pnl:.2f}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Avg MFE (Max Favorable): {avg_mfe:.2f}%")
    print(f"Avg MAE (Max Adverse): {avg_mae:.2f}%")

    print("\n--- Top Tickers by PnL ---")
    tickers = {}
    for r in rows:
        t = r['ticker']
        p = r['pnl_dollar'] or 0
        tickers[t] = tickers.get(t, 0) + p
    
    for t, pnl in sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{t}: ${pnl:.2f}")

