"""Paper broker — simulated fills against candle prices.

No real money, no network. Tracks cash, one position, a fee per trade, and a
log of fills. This is what the backtester trades through, and what you should
keep using until a strategy is proven.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import Broker, Position


@dataclass
class Fill:
    side: str
    price: float
    qty: float


class PaperBroker(Broker):
    def __init__(self, cash: float = 10_000.0, fee: float = 0.001):
        self.cash = cash
        self.fee = fee
        self.position = Position()
        self.fills: list[Fill] = []

    def buy(self, price: float, qty: float) -> None:
        cost = price * qty
        fee = cost * self.fee
        if cost + fee > self.cash or qty <= 0:
            return
        # blend into average entry if already holding
        total_qty = self.position.qty + qty
        self.position.entry_price = (
            (self.position.entry_price * self.position.qty) + cost
        ) / total_qty
        self.position.qty = total_qty
        self.cash -= cost + fee
        self.fills.append(Fill("buy", price, qty))

    def sell(self, price: float, qty: float) -> None:
        qty = min(qty, self.position.qty)
        if qty <= 0:
            return
        proceeds = price * qty
        fee = proceeds * self.fee
        self.cash += proceeds - fee
        self.position.qty -= qty
        if self.position.qty == 0:
            self.position.entry_price = 0.0
        self.fills.append(Fill("sell", price, qty))

    def equity(self, price: float) -> float:
        return self.cash + self.position.qty * price
