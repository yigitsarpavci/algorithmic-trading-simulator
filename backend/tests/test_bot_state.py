from datetime import datetime, timedelta, timezone

from app.services.bot_state import BotStateService


def test_trading_is_allowed_by_default():
    assert BotStateService().is_trading_allowed() == (True, "OK")


def test_five_consecutive_losses_trigger_a_cooldown():
    bot = BotStateService()
    for _ in range(4):
        bot.record_trade_result(-100.0, "BTC-USD")
    assert bot.is_trading_allowed()[0] is True

    bot.record_trade_result(-100.0, "BTC-USD")
    allowed, reason = bot.is_trading_allowed()
    assert allowed is False and reason.startswith("COOLDOWN_ACTIVE")
    assert bot.cooldown_until > datetime.now(timezone.utc) + timedelta(minutes=29)


def test_a_win_resets_the_losing_streak():
    bot = BotStateService()
    for _ in range(4):
        bot.record_trade_result(-50.0, "ETH-USD")
    bot.record_trade_result(75.0, "ETH-USD")
    assert bot.consecutive_losses == 0


def test_expired_cooldown_allows_trading_again():
    bot = BotStateService()
    bot.cooldown_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert bot.is_trading_allowed() == (True, "OK")


def test_daily_loss_cap_halts_trading():
    bot = BotStateService()
    bot.record_trade_result(-bot.max_daily_loss, "SOL-USD")
    assert bot.is_trading_allowed() == (False, "MAX_DAILY_LOSS_REACHED")


def test_new_day_resets_limits():
    bot = BotStateService()
    bot.record_trade_result(-bot.max_daily_loss, "SOL-USD")
    bot.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=10)
    bot.last_reset_day = (datetime.now(timezone.utc).day % 28) + 1  # any different day
    assert bot.is_trading_allowed() == (True, "OK")
    assert bot.daily_realized_loss == 0.0 and bot.consecutive_losses == 0


def test_losing_coin_is_remembered():
    bot = BotStateService()
    bot.record_trade_result(-10.0, "LINK-USD")
    assert "LINK-USD" in bot.last_loss_time_per_coin
