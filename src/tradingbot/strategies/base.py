"""Strategy interface.

A strategy sees candles one at a time and emits a Signal. It holds no money
and places no orders — that's the broker's job. This keeps strategies pure and
easy to test.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from ..data.feed import Candle


class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Strategy(ABC):
    """Base class for all strategies."""

    name: str = "base"

    @abstractmethod
    def on_candle(self, candle: Candle) -> Signal:
        """Receive the next candle, return a trading signal."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear any internal state before a fresh run. Override if needed."""
