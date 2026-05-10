from pydantic import BaseModel

class SystemSettings(BaseModel):
    leverage: float = 5.0           # Was 15.0 — reduced to prevent capital vaporization
    commission_rate: float = 0.0004
    slippage_max: float = 0.0002
    risk_per_trade: float = 0.01    # Was 0.05 — reduced from 5% to 1% of portfolio per trade
    tp_pct: float = 0.016           # 1.6% TP (2x the SL for realistic scalping)
    sl_pct: float = 0.008           # Was 0.01 → 0.008 (0.8% floor, wider to avoid spread noise)
    hft_cycle_seconds: float = 2.0

class SettingsService:
    def __init__(self):
        self.settings = SystemSettings()

    def get_settings(self) -> SystemSettings:
        return self.settings

    def update_settings(self, new_settings: dict) -> SystemSettings:
        for key, value in new_settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        return self.settings

settings_service = SettingsService()
