"""Risk manager.

Decides how big a position to take and when a stop-loss is hit. Position size
is derived from how much equity you're willing to lose per trade and how far
away the stop sits — so a tighter stop means a bigger size, same risk.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskManager:
    risk_per_trade: float = 0.02      # fraction of equity to risk per trade
    stop_loss_pct: float = 0.03       # stop distance as fraction of entry

    def position_size(self, equity: float, price: float) -> float:
        """Units to buy so that hitting the stop loses ~risk_per_trade of equity."""
        if price <= 0 or self.stop_loss_pct <= 0:
            return 0.0
        risk_cash = equity * self.risk_per_trade
        risk_per_unit = price * self.stop_loss_pct
        return risk_cash / risk_per_unit

    def stop_price(self, entry_price: float) -> float:
        return entry_price * (1 - self.stop_loss_pct)

    def stop_hit(self, entry_price: float, current_price: float) -> bool:
        return current_price <= self.stop_price(entry_price)
