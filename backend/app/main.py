import asyncio
import statistics
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.db.session import SessionLocal
from app.services.paper_trading import paper_trading_service
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.services.settings_service import settings_service

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# In-memory price ring buffer (max 120 ticks per ticker for Deep Memory)
_price_history: dict[str, list[float]] = {}
_volume_history: dict[str, float] = {}

# === V8 ACTIVE UNIVERSE ===
# Based on historical performance, strictly limiting to liquid assets
V8_UNIVERSE = {"BTC-USD", "ETH-USD", "SOL-USD", "LTC-USD", "LINK-USD"}

# === DATA-DRIVEN ASSET WEIGHTS ===
# Based on actual win rates from trade history:
# LTC-USD: 25.2% WR → slight boost
# LINK-USD: 25.9% WR → slight boost 
# ETH-USD: 16.4% WR → neutral
# BTC-USD: 8.5% WR → reduce
# SOL-USD: 16.9% WR → neutral
# AVAX-USD: 8.9% WR → reduce
# ATOM-USD: 17.0% WR but massive avg loss -$13,452 → reduce significantly
ASSET_WEIGHTS = {
    "LTC-USD": 1.3,      # Best WR (25.2%)
    "LINK-USD": 1.3,     # Best WR (25.9%)
    "ETH-USD": 1.0,      # Neutral
    "SOL-USD": 0.8,      # Decent WR but volatile
    "BTC-USD": 0.6,      # Low WR (8.5%), reduce exposure
    "AVAX-USD": 0.5,     # Low WR (8.9%), reduce
    "ATOM-USD": 0.3,     # Was 1.5x(!!) — 2nd worst total PnL, massive avg loss
}


def _get_momentum_direction(hist: list[float], lookback: int = 3) -> str:
    """Check if last N ticks are consistently moving in one direction."""
    if len(hist) < lookback + 1:
        return "FLAT"
    
    recent = hist[-(lookback + 1):]
    ups = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    downs = sum(1 for i in range(1, len(recent)) if recent[i] < recent[i-1])
    
    if ups == lookback:
        return "UP"
    elif downs == lookback:
        return "DOWN"
    return "FLAT"


def _is_flat_market(hist: list[float], threshold_pct: float = 0.05) -> bool:
    """Check if price hasn't moved meaningfully (chop/consolidation)."""
    if len(hist) < 10:
        return True
    recent = hist[-10:]
    range_pct = ((max(recent) - min(recent)) / min(recent)) * 100
    return range_pct < threshold_pct


async def trading_orchestrator():
    """
    V7 Trading Orchestrator — Data-Driven Scalper
    
    Key changes from V6:
    - LONGS ONLY (shorts disabled — 14.3% WR, -$5,723 avg)
    - Z-Score threshold raised 0.8 → 1.8 (filter noise)
    - Warmup 3 → 10 ticks (statistical stability)
    - Momentum confirmation: 3 consecutive ticks required
    - Flat market filter: skip choppy conditions
    - Toxic tickers blacklisted (DOT, XRP)
    - Data-driven asset weights (ATOM 1.5x → 0.3x)
    - Timeout 20s → 60s (let winners breathe)
    """
    warmup = 0

    while True:
        conf = settings_service.get_settings()
        db = None
        try:
            db = SessionLocal()
            from app.services.market_data import market_data
            from app.api.api_v1.endpoints.ws import manager
            from app.services.bot_state import bot_state_service

            # Global Risk Check
            is_allowed, reason = bot_state_service.is_trading_allowed()
            if not is_allowed:

                await asyncio.sleep(conf.hft_cycle_seconds)
                continue

            await paper_trading_service.update_all_trades(db)

            tickers = [item.ticker for item in db.query(models.WatchlistItem).all()]
            if not tickers:
                await asyncio.sleep(conf.hft_cycle_seconds)
                continue

            # Log start of cycle
            print(f"HFT Cycle Start: Fetching quotes for {len(tickers)} tickers...")
            try:
                quotes = await asyncio.wait_for(market_data.get_batch_quotes(list(set(tickers))), timeout=5.0)
            except asyncio.TimeoutError:
                print("Market data fetch TIMEOUT - skipping cycle")
                await asyncio.sleep(1)
                continue
            except Exception as e:
                print(f"Market data fetch ERROR: {e}")
                await asyncio.sleep(1)
                continue
            
            print(f"Quotes received: {list(quotes.keys())}")
            
            # Enrich quotes with dynamic change and RS from in-memory history before broadcasting
            btc_hist = _price_history.get("BTC-USD", [])
            btc_roc_global = ((btc_hist[-1] - btc_hist[0]) / btc_hist[0] * 100) if len(btc_hist) >= 10 and btc_hist[0] > 0 else 0.0

            for tk_enrich, qd_enrich in quotes.items():
                hist_enrich = _price_history.get(tk_enrich, [])
                if len(hist_enrich) >= 10 and hist_enrich[0] > 0:
                    start_price = hist_enrich[0]
                    current = qd_enrich.get("price", start_price)
                    if isinstance(current, (int, float)):
                        qd_enrich["change"] = round(((current - start_price) / start_price) * 100, 3)
                        qd_enrich["rs"] = round((qd_enrich["change"] + 100) / (btc_roc_global + 100), 3) if (btc_roc_global + 100) != 0 else 1.00
                else:
                    qd_enrich["change"] = 0.0
                    qd_enrich["rs"] = 1.00

            print(f"BROADCASTING: {quotes}")
            await manager.broadcast({"type": "PRICE_BATCH_UPDATE", "payload": quotes})

            # Update ring buffer (expanded to 120 ticks for better statistical analysis)
            for tk, qd in quotes.items():
                p = qd.get("price")
                if not isinstance(p, (int, float)) or p <= 0:
                    continue
                buf = _price_history.setdefault(tk, [])
                buf.append(float(p))
                if len(buf) > 120:
                    buf.pop(0)
                
                # Update volume history for ALL tickers
                _volume_history[tk] = qd.get("volume", 0)

            # Extended warmup: need 10 ticks minimum for stable statistics
            warmup += 1
            if warmup < 10:

                await asyncio.sleep(conf.hft_cycle_seconds)
                continue

            # BTC leader check
            bh = _price_history.get("BTC-USD", [])
            btc_roc = ((bh[-1] - bh[0]) / bh[0] * 100) if len(bh) >= 2 and bh[0] > 0 else 0.0

            for tk, qd in quotes.items():
                # === V8 UNIVERSE CHECK ===
                if tk not in V8_UNIVERSE:
                    continue

                p = qd.get("price")
                if not isinstance(p, (int, float)) or p <= 0:
                    continue

                hist = _price_history.get(tk, [])
                if len(hist) < 30 or hist[0] <= 0:
                    continue

                # Z-Score Breakout Math
                mean = statistics.mean(hist)
                stdev = statistics.stdev(hist) if len(hist) >= 2 else 0.0001
                stdev = max(stdev, 0.0001)
                z_score = (float(p) - mean) / stdev

                # Dynamic Volatility Check for TP/SL sizing
                rocs = [((hist[i] - hist[i-1])/hist[i-1]*100) for i in range(1, len(hist))]
                volatility = statistics.stdev(rocs) if len(rocs) >= 2 else 0.001
                volatility = max(volatility, 0.0005)

                if db.query(models.PaperTrade).filter(
                    models.PaperTrade.ticker == tk,
                    models.PaperTrade.status.in_(["OPEN", "PENDING_TRIGGER"])
                ).first():
                    continue

                # === V8 ENTRY SCORING SYSTEM ===
                entry_score = 0
                score_details = {}
                
                # 1. Z-Score Strength
                if z_score > 1.5:
                    entry_score += 1
                    score_details["z_score"] = "+1"
                if z_score > 2.5:
                    entry_score += 1
                    score_details["extreme_z"] = "+1"
                    
                # 2. Momentum Confirmation
                momentum_dir = _get_momentum_direction(hist, lookback=2)
                if momentum_dir == "UP":
                    entry_score += 1
                    score_details["momentum"] = "+1"
                    
                # 3. Volatility/Range
                if not _is_flat_market(hist, threshold_pct=0.03):
                    entry_score += 1
                    score_details["volatility"] = "+1"
                    
                # 4. BTC Confirmation
                if btc_roc > -0.01:
                    entry_score += 1
                    score_details["btc_favorable"] = "+1"
                
                # 5. Volume Spike Check
                current_vol = qd.get("volume", 0)
                prev_vol = _volume_history.get(tk, 0)
                if prev_vol > 0 and (current_vol - prev_vol) > 10000: # Simple threshold for now
                    entry_score += 1
                    score_details["vol_spike"] = "+1"
                    
                # 6. Recent Loss Penalty
                penalty = bot_state_service.get_recent_loss_penalty(tk)
                if penalty < 0:
                    entry_score += penalty
                    score_details["loss_penalty"] = str(penalty)
                
                # Threshold: Require at least 4 points to trade
                if entry_score < 4:
                    continue

                # === V8 POSITION SIZING (Risk-Normalized) ===
                # Instead of fixed %, use Risk/Stop_Distance
                dynamic_sl_pct = max(0.008, (volatility * 3.0) / 100)
                dynamic_tp_pct = dynamic_sl_pct * 2.0  # 1:2 RR ratio
                
                user = db.query(models.User).filter(models.User.id == 1).first()
                portfolio_value = user.portfolio_value if user else 10_000_000.0
                
                # Fixed 0.25% risk per trade
                risk_usd = portfolio_value * 0.0025
                
                # Target notional position size based on stop distance
                suggested_notional = risk_usd / dynamic_sl_pct

                signal_type = "BUY"
                strat = "V8 Risk-First Scalp"
                stop_loss = round(float(p) * (1 - dynamic_sl_pct), 6)
                take_profit = round(float(p) * (1 + dynamic_tp_pct), 6)

                sig = models.Signal(
                    ticker=tk, user_id=1, strategy_name=strat, signal_type=signal_type,
                    confidence=int((entry_score / 5.0) * 100), entry_type="Market",
                    entry_trigger=f"{strat} ${float(p):.2f}",
                    entry_price=float(p),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    suggested_amount=suggested_notional,
                    timeframe=f"HFT ({conf.hft_cycle_seconds}s)",
                    market_regime=f"Score:{entry_score} Z:{z_score:.2f} Mom:{momentum_dir}",
                    reason=f"V8 Entry Score: {entry_score}/5",
                    risk_note=f"Risk:0.25% SL:{dynamic_sl_pct*100:.2f}%",
                    score_breakdown=score_details, status="ACTIVE"
                )
                db.add(sig)
                db.commit()
                db.refresh(sig)
                await paper_trading_service.open_from_signal(db, sig)
                await manager.broadcast({
                    "type": "SIGNAL_GENERATED",
                    "payload": {"ticker": tk, "type": "BUY", "price": float(p),
                                "strategy": strat, "timestamp": datetime.now(timezone.utc).isoformat()}
                })

            await manager.broadcast({"type": "SYNC_TRIGGER", "payload": {}})
        except Exception as e:
            import traceback
            print(f"Orchestrator error: {e}")
            traceback.print_exc()
        finally:
            if db:
                db.close()

        await asyncio.sleep(conf.hft_cycle_seconds)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_orchestrator())


@app.get("/")
async def root():
    return {"message": "AlphaTrigger API v7"}
