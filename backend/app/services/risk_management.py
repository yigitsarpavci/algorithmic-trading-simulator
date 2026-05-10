from typing import Dict, Any, Optional

class RiskManagementService:
    def calculate_risk_per_trade(self, portfolio_value: float, risk_percent: float) -> float:
        return portfolio_value * (risk_percent / 100)

    def calculate_position_size(self, entry_price: float, stop_loss: float, max_dollar_risk: float) -> int:
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0: return 0
        return int(max_dollar_risk / stop_distance)

    def validate_trade_risk(self, entry_price: float, stop_loss: float, take_profit: float) -> Dict[str, Any]:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            "risk_reward_ratio": round(rr_ratio, 2),
            "is_valid": rr_ratio >= 1.5,
            "warning": None if rr_ratio >= 1.5 else "Poor Risk/Reward ratio (< 1.5). Consider skipping."
        }

    def calculate_suggested_amount(
        self, 
        entry_price: float, 
        stop_loss: float, 
        take_profit: float,
        portfolio_value: float, 
        risk_percent: float = 1.0,
        max_pos_size_percent: float = 20.0
    ) -> Dict[str, Any]:
        """
        Calculate complete position sizing and risk validation.
        """
        if not stop_loss:
            return {"error": "Stop-loss is required for signal generation."}

        # 1. Risk calculation
        dollar_risk = self.calculate_risk_per_trade(portfolio_value, risk_percent)
        quantity = self.calculate_position_size(entry_price, stop_loss, dollar_risk)
        
        total_cost = quantity * entry_price
        max_allowed_cost = portfolio_value * (max_pos_size_percent / 100)
        
        warning = None
        
        # 2. Position Size Capping
        if total_cost > max_allowed_cost:
            quantity = int(max_allowed_cost / entry_price)
            total_cost = quantity * entry_price
            warning = f"Position size capped at {max_pos_size_percent}% of portfolio."

        # 3. Risk/Reward Validation
        rr_validation = self.validate_trade_risk(entry_price, stop_loss, take_profit)
        if rr_validation["warning"]:
            warning = rr_validation["warning"] if not warning else f"{warning} {rr_validation['warning']}"

        return {
            "suggested_amount": f"{round((total_cost / portfolio_value) * 100, 1)}%",
            "quantity": quantity,
            "dollar_risk": round(dollar_risk, 2),
            "total_cost": round(total_cost, 2),
            "risk_reward_ratio": rr_validation["risk_reward_ratio"],
            "warning": warning
        }

risk_management_service = RiskManagementService()
