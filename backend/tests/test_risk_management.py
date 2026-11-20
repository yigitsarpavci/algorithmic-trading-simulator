import pytest

from app.services.risk_management import RiskManagementService

svc = RiskManagementService()


def test_risk_per_trade_is_percentage_of_portfolio():
    assert svc.calculate_risk_per_trade(100_000, 0.25) == pytest.approx(250.0)


def test_position_size_divides_dollar_risk_by_stop_distance():
    assert svc.calculate_position_size(entry_price=100, stop_loss=98, max_dollar_risk=250) == 125


def test_position_size_is_zero_without_stop_distance():
    assert svc.calculate_position_size(entry_price=100, stop_loss=100, max_dollar_risk=250) == 0


def test_risk_reward_validation_flags_poor_ratio():
    poor = svc.validate_trade_risk(100, 98, 101)
    good = svc.validate_trade_risk(100, 98, 104)
    assert poor["is_valid"] is False and poor["warning"]
    assert good["is_valid"] is True and good["risk_reward_ratio"] == 2.0


def test_suggested_amount_caps_oversized_positions():
    result = svc.calculate_suggested_amount(
        entry_price=100, stop_loss=99.9, take_profit=100.3,
        portfolio_value=100_000, risk_percent=1.0, max_pos_size_percent=20.0,
    )
    assert result["total_cost"] <= 20_000
    assert "capped" in result["warning"]


def test_suggested_amount_requires_stop_loss():
    assert "error" in svc.calculate_suggested_amount(100, 0, 104, 100_000)
