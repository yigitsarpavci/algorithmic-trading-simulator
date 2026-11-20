"""The V8 risk-first exit state machine and position sizing, run against an in-memory SQLite DB."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.db.session import Base
from app.services import paper_trading as pt
from app.services.bot_state import bot_state_service

ENTRY = 100.0


def run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    # Deterministic execution: no random slippage, fresh global risk state, default settings.
    monkeypatch.setattr(pt.random, "random", lambda: 0.0)
    bot_state_service.__init__()
    yield session
    session.close()


def make_trade(db, side="BUY", stop=99.2, take=101.6, age=0, mfe=0.0, entry=ENTRY):
    user = db.query(models.User).first() or models.User(email="t@example.com", portfolio_value=100_000.0)
    db.add(user)
    db.flush()
    signal = models.Signal(
        user_id=user.id, ticker="BTC-USD", signal_type=side, entry_price=entry,
        stop_loss=stop, take_profit=take, strategy_name="test",
    )
    db.add(signal)
    db.flush()
    trade = models.PaperTrade(
        signal_id=signal.id, user_id=user.id, ticker="BTC-USD", paper_entry_price=entry,
        quantity=10, status="OPEN", opened_at=datetime.now(timezone.utc) - timedelta(seconds=age),
        pnl_percent=0.0, pnl_dollar=0.0, max_favorable_excursion=mfe, max_adverse_excursion=0.0,
    )
    db.add(trade)
    db.commit()
    return trade


def tick(db, trade, price, monkeypatch):
    async def quote(_ticker):
        return {"price": price}

    monkeypatch.setattr(pt.market_data, "get_quote", quote)
    run(pt.paper_trading_service._update_single_trade(db, trade))
    db.refresh(trade)
    return trade


def test_hard_stop_closes_a_losing_long(db, monkeypatch):
    trade = tick(db, make_trade(db), 99.0, monkeypatch)
    assert trade.status == "CLOSED_LOSS" and trade.exit_reason == "Hard Stop Hit"
    assert trade.pnl_dollar < 0 and trade.closed_at is not None


def test_hard_stop_for_a_short_triggers_on_a_price_rise(db, monkeypatch):
    trade = tick(db, make_trade(db, side="SELL", stop=100.8, take=98.4), 101.0, monkeypatch)
    assert trade.status == "CLOSED_LOSS" and trade.exit_reason == "Hard Stop Hit"


def test_no_follow_through_after_45_seconds(db, monkeypatch):
    trade = tick(db, make_trade(db, age=60), 100.0, monkeypatch)
    assert trade.status in {"CLOSED_LOSS", "CLOSED_WIN"}
    assert trade.exit_reason == "NO_IMMEDIATE_FOLLOW_THROUGH"


def test_break_even_stop_after_half_r_of_profit(db, monkeypatch):
    # mfe 0.5 >= 0.5R (0.4), but the trade is back at/below zero net of costs.
    trade = tick(db, make_trade(db, age=10, mfe=0.5), 100.0, monkeypatch)
    assert trade.status == "CLOSED_WIN" and trade.exit_reason == "Break-Even Stop"


def test_trailing_stop_after_0_8r_when_price_gives_back_more_than_0_4r(db, monkeypatch):
    trade = tick(db, make_trade(db, age=10, mfe=8.0), 100.3, monkeypatch)
    assert trade.status == "CLOSED_WIN" and trade.exit_reason == "Trailing Stop"


def test_take_profit_target(db, monkeypatch):
    trade = tick(db, make_trade(db, age=10), 101.7, monkeypatch)
    assert trade.status == "CLOSED_WIN" and trade.exit_reason == "Target Hit"
    assert trade.pnl_dollar > 0 and trade.paper_exit_price == pytest.approx(101.7)


def test_time_stop_after_five_minutes(db, monkeypatch):
    trade = tick(db, make_trade(db, age=301, mfe=0.2), 100.05, monkeypatch)
    assert trade.status == "CLOSED_TIMEOUT" and trade.exit_reason == "Time Stop"


def test_open_trade_keeps_running_and_tracks_excursions(db, monkeypatch):
    trade = tick(db, make_trade(db, age=10), 100.2, monkeypatch)
    assert trade.status == "OPEN"
    assert trade.max_favorable_excursion > 0
    assert trade.max_adverse_excursion == 0


def test_closing_a_trade_updates_the_portfolio_and_global_risk_state(db, monkeypatch):
    trade = make_trade(db)
    before = db.query(models.User).first().portfolio_value
    tick(db, trade, 99.0, monkeypatch)
    after = db.query(models.User).first().portfolio_value
    assert after < before
    assert bot_state_service.consecutive_losses == 1


def test_invalid_quotes_are_ignored(db, monkeypatch):
    trade = make_trade(db)
    for bad in ({"error": "boom"}, {"price": 0}, {"price": "x"}, {}):
        async def quote(_t, bad=bad):
            return bad

        monkeypatch.setattr(pt.market_data, "get_quote", quote)
        run(pt.paper_trading_service._update_single_trade(db, trade))
        db.refresh(trade)
        assert trade.status == "OPEN"


def test_open_from_signal_sizes_by_risk_and_prevents_duplicates(db):
    user = models.User(email="s@example.com", portfolio_value=1_000_000.0)
    db.add(user)
    db.flush()
    signal = models.Signal(user_id=user.id, ticker="ETH-USD", signal_type="BUY", entry_price=2_000.0,
                           stop_loss=1_984.0, take_profit=2_032.0)
    db.add(signal)
    db.commit()

    trade = run(pt.paper_trading_service.open_from_signal(db, signal))
    # 1% risk per trade (default) of 1,000,000 at 2,000 per unit
    assert trade.quantity == 5
    assert trade.status == "OPEN"
    assert trade.paper_entry_price == pytest.approx(2_000.0)
    assert trade.pnl_dollar < 0  # entry commission is charged immediately

    again = run(pt.paper_trading_service.open_from_signal(db, signal))
    assert again.id == trade.id


def test_open_from_signal_rejects_a_non_positive_entry_price(db):
    user = models.User(email="z@example.com")
    db.add(user)
    db.flush()
    signal = models.Signal(user_id=user.id, ticker="X", signal_type="BUY", entry_price=0.0)
    db.add(signal)
    db.commit()
    assert run(pt.paper_trading_service.open_from_signal(db, signal)) is None
