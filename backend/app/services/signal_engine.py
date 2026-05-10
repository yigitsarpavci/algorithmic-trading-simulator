import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app import models, schemas
from app.services.market_data import market_data
from app.services.market_regime import market_regime_service
from app.services.signal_scoring import scoring_engine
from app.services.strategies.vwap_pullback import vwap_pullback_strategy
from app.services.strategies.opening_range_breakout import opening_range_breakout_strategy
from app.services.strategies.pullback_20dma import pullback_20dma_strategy
from app.services.strategies.breakout_consolidation import breakout_consolidation_strategy
from app.services.strategies.crypto_momentum import crypto_momentum_strategy
from datetime import datetime
import time

from app.services.risk_management import risk_management_service
from app.services.ai_explainer import ai_explainer

class SignalEngine:
    def __init__(self):
        self._spy_cache = None
        self._qqq_cache = None
        self._regime_cache = None
        self._cache_time = None

    async def _get_market_context(self):
        """Fetch SPY/QQQ/Regime once per cycle and cache for 30s."""
        now = time.time()
        if self._cache_time and (now - self._cache_time) < 300 and self._spy_cache is not None:
            return self._spy_cache, self._qqq_cache, self._regime_cache
        
        spy_daily = await market_data.get_daily_candles("SPY")
        qqq_daily = await market_data.get_daily_candles("QQQ")
        
        df_spy = pd.DataFrame(spy_daily)
        if not df_spy.empty:
            df_spy['time'] = pd.to_datetime(df_spy['time'])
            df_spy.set_index('time', inplace=True)

        df_qqq = pd.DataFrame(qqq_daily)
        if not df_qqq.empty:
            df_qqq['time'] = pd.to_datetime(df_qqq['time'])
            df_qqq.set_index('time', inplace=True)
        
        regime = market_regime_service.analyze(df_spy, df_qqq)
        
        self._spy_cache = df_spy
        self._qqq_cache = df_qqq
        self._regime_cache = regime
        self._cache_time = now
        return df_spy, df_qqq, regime

    async def run_for_ticker(self, ticker: str, db: Session, df_spy=None, df_qqq=None, regime=None) -> Optional[models.Signal]:
        """
        Run the complete signal generation pipeline for a single ticker.
        Accepts pre-fetched market context for speed.
        """
        try:
            # 1. Fetch ticker-specific data only (no more SPY/QQQ per ticker!)
            quote = await market_data.get_quote(ticker)
            if "error" in quote: return None
            
            daily_candles = await market_data.get_daily_candles(ticker)
            intraday_candles = await market_data.get_intraday_candles(ticker)
            
            if df_spy is None or df_qqq is None or regime is None:
                df_spy, df_qqq, regime = await self._get_market_context()
            
            if not daily_candles: return None
            
            df_daily = pd.DataFrame(daily_candles)
            if not df_daily.empty:
                df_daily['time'] = pd.to_datetime(df_daily['time'])
                df_daily.set_index('time', inplace=True)

            df_intraday = pd.DataFrame(intraday_candles)
            if not df_intraday.empty:
                df_intraday['time'] = pd.to_datetime(df_intraday['time'])
                df_intraday.set_index('time', inplace=True)
            
            # 2. Run Strategies
            strategies_results = []
            
            # Crypto tickers get the ultra-fast momentum strategy
            is_crypto = '-USD' in ticker.upper()
            if is_crypto:
                crypto_res = await crypto_momentum_strategy.analyze(ticker, df_daily, regime)
                strategies_results.append(crypto_res)
            
            # Also run standard strategies
            vwap_res = await vwap_pullback_strategy.analyze(ticker, df_intraday, regime)
            strategies_results.append(vwap_res)
            
            orb_res = await opening_range_breakout_strategy.analyze(ticker, df_intraday, df_spy, regime)
            strategies_results.append(orb_res)
            
            dma20_res = await pullback_20dma_strategy.analyze(ticker, df_daily, df_spy, regime)
            strategies_results.append(dma20_res)
            
            breakout_res = await breakout_consolidation_strategy.analyze(ticker, df_daily, df_spy, regime)
            strategies_results.append(breakout_res)
            
            # 3. Filter for actual BUY/BUY_WATCH signals
            actionable_signals = [s for s in strategies_results if s["signal_type"] in ["BUY", "BUY_IF_TRIGGER", "BUY_WATCH"]]
            
            if not actionable_signals:
                return None
            
            # 4. Risk Management & Position Sizing
            processed_signals = []
            for s in actionable_signals:
                risk_data = risk_management_service.calculate_suggested_amount(
                    entry_price=s["entry_price"],
                    stop_loss=s["stop_loss"],
                    take_profit=s["take_profit"],
                    portfolio_value=100000.0,
                    risk_percent=1.0,
                    max_pos_size_percent=15.0
                )
                
                if "error" in risk_data: continue

                final_signal_type = s["signal_type"]
                if risk_data["risk_reward_ratio"] < 1.5:
                    final_signal_type = "BUY_WATCH"

                # 5. Scoring
                indicators = {
                    "price": quote["price"],
                    "relative_volume": 1.5,
                    "relative_strength_spy": 1.1,
                    "rsi": 50,
                    "dma_20": quote["price"] * 0.98,
                    "dma_50": quote["price"] * 0.95,
                    "dma_200": quote["price"] * 0.85,
                    "vwap": quote["price"] * 0.99
                }
                
                score_data = scoring_engine.calculate_final_signal_score(
                    market_regime_score=regime["market_regime_score"],
                    indicators=indicators,
                    strategy_name=s["strategy_name"],
                    strategy_performance={"win_rate": 60},
                    news_context={"has_earnings_this_week": False}
                )
                
                processed_signals.append({
                    **s, 
                    "signal_type": final_signal_type,
                    "risk_data": risk_data, 
                    "score_data": score_data
                })
            
            if not processed_signals: return None
            
            best_raw = max(processed_signals, key=lambda x: x["score_data"]["final_score"])
            
            # 6. AI Explanation
            explanation = await ai_explainer.explain_signal(
                ticker=ticker.upper(),
                signal_data=best_raw,
                indicators=indicators,
                market_regime=regime
            )

            # 7. Close any existing ACTIVE signals for this ticker
            existing_signals = db.query(models.Signal).filter(
                models.Signal.ticker == ticker.upper(),
                models.Signal.status == "ACTIVE"
            ).all()
            for old_signal in existing_signals:
                old_signal.status = "SUPERSEDED"
                db.add(old_signal)

            # 8. Save to Database
            signal = models.Signal(
                ticker=ticker.upper(),
                user_id=1,
                strategy_name=best_raw["strategy_name"],
                signal_type=best_raw["signal_type"],
                confidence=int(best_raw["score_data"]["final_score"]),
                entry_type=best_raw["entry_type"],
                entry_trigger=best_raw["entry_trigger"],
                entry_price=best_raw["entry_price"],
                stop_loss=best_raw["stop_loss"],
                take_profit=best_raw["take_profit"],
                suggested_amount=best_raw["risk_data"]["suggested_amount"],
                timeframe=best_raw["timeframe"],
                market_regime=regime["mood"],
                reason=explanation["ai_explanation"],
                risk_note=f"{explanation['ai_risk_warning']} | {best_raw['risk_data']['warning'] or ''}",
                score_breakdown=best_raw["score_data"]["breakdown"],
                status="ACTIVE"
            )
            db.add(signal)
            db.commit()
            db.refresh(signal)
            
            return signal
            
        except Exception as e:
            print(f"Error generating signal for {ticker}: {e}")
            return None

    async def run_batch(self, db: Session):
        """
        Run for all tickers sequentially but with cached SPY/QQQ.
        SPY/QQQ fetched ONCE = eliminates 100+ redundant API calls.
        """
        watchlist = db.query(models.WatchlistItem).all()
        
        # Pre-fetch market context ONCE for entire batch
        df_spy, df_qqq, regime = await self._get_market_context()
        
        results = []
        for item in watchlist:
            sig = await self.run_for_ticker(item.ticker, db, df_spy, df_qqq, regime)
            if sig: results.append(sig)
        return results

signal_engine = SignalEngine()
