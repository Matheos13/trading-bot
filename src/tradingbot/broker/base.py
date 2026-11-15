"""Broker interface.

A broker holds cash and a position, and fills orders. The backtester and a
future live broker both implement this, so the rest of the bot doesn't care
which one it's talking to.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Position:
    qty: float = 0.0            # units of the asset held
    entry_price: float = 0.0    # average entry price

    @property
    def is_open(self) -> bool:
        return self.qty > 0


class Broker(ABC):
    @abstractmethod
    def buy(self, price: float, qty: float) -> None: ...

    @abstractmethod
    def sell(self, price: float, qty: float) -> None: ...

    @abstractmethod
    def equity(self, price: float) -> float:
        """Total account value (cash + position marked at `price`)."""
        ...
