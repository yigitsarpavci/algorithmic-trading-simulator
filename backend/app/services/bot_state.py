from datetime import datetime, timezone, timedelta

class BotStateService:
    def __init__(self):
        self.consecutive_losses = 0
        self.daily_realized_loss = 0.0
        self.cooldown_until = None
        
        # Global limits
        self.max_daily_loss = 200_000.0  # $200k max daily loss
        self.max_consecutive_losses = 5
        self.max_open_positions = 2
        
        # Tracking for recent losses per coin
        self.last_loss_time_per_coin = {}
        
        self.last_reset_day = datetime.now(timezone.utc).day

    def check_daily_reset(self):
        now = datetime.now(timezone.utc)
        if now.day != self.last_reset_day:
            self.daily_realized_loss = 0.0
            self.consecutive_losses = 0
            self.last_reset_day = now.day
            self.cooldown_until = None

    def record_trade_result(self, pnl: float, ticker: str):
        self.check_daily_reset()
        self.daily_realized_loss += pnl
        
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time_per_coin[ticker] = datetime.now(timezone.utc)
            
            if self.consecutive_losses >= self.max_consecutive_losses:
                # 30 minute cooldown after 5 consecutive losses
                self.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        else:
            self.consecutive_losses = 0

    def is_trading_allowed(self) -> tuple[bool, str]:
        self.check_daily_reset()
        
        if self.cooldown_until and datetime.now(timezone.utc) < self.cooldown_until:
            return False, f"COOLDOWN_ACTIVE (until {self.cooldown_until.strftime('%H:%M:%S')} UTC)"
            
        if self.daily_realized_loss <= -self.max_daily_loss:
            return False, "MAX_DAILY_LOSS_REACHED"
            
        return True, "OK"
        
    def get_recent_loss_penalty(self, ticker: str) -> int:
        last_loss = self.last_loss_time_per_coin.get(ticker)
        if last_loss and (datetime.now(timezone.utc) - last_loss).total_seconds() < 900: # 15 mins
            return -2
        return 0

bot_state_service = BotStateService()
