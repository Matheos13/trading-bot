"""SMA crossover — the classic starter strategy.

Buy when the fast moving average crosses above the slow one, sell when it
crosses back below. Simple, transparent, and a good baseline to beat.
"""

from __future__ import annotations

from collections import deque

from ..data.feed import Candle
from .base import Signal, Strategy


class SmaCrossStrategy(Strategy):
    name = "sma_cross"

    def __init__(self, fast: int = 10, slow: int = 30):
        if fast >= slow:
            raise ValueError("fast period must be shorter than slow period")
        self.fast = fast
        self.slow = slow
        self._closes: deque[float] = deque(maxlen=slow)
        self._prev_fast: float | None = None
        self._prev_slow: float | None = None

    def reset(self) -> None:
        self._closes.clear()
        self._prev_fast = None
        self._prev_slow = None

    def _sma(self, period: int) -> float | None:
        if len(self._closes) < period:
            return None
        window = list(self._closes)[-period:]
        return sum(window) / period

    def on_candle(self, candle: Candle) -> Signal:
        self._closes.append(candle.close)
        fast = self._sma(self.fast)
        slow = self._sma(self.slow)

        signal = Signal.HOLD
        if fast is not None and slow is not None \
                and self._prev_fast is not None and self._prev_slow is not None:
            crossed_up = self._prev_fast <= self._prev_slow and fast > slow
            crossed_down = self._prev_fast >= self._prev_slow and fast < slow
            if crossed_up:
                signal = Signal.BUY
            elif crossed_down:
                signal = Signal.SELL

        self._prev_fast = fast
        self._prev_slow = slow
        return signal
