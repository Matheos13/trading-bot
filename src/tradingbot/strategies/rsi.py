"""RSI (Relative Strength Index) mean-reversion strategy.

Buy when RSI crosses back above the oversold level, sell when it crosses back
below the overbought level. Uses Wilder's smoothed average, which is the
standard RSI formulation.
"""

from __future__ import annotations

from collections import deque

from ..data.feed import Candle
from .base import Signal, Strategy


class RsiStrategy(Strategy):
    name = "rsi"

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        if oversold >= overbought:
            raise ValueError("oversold level must be below overbought level")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self._closes: deque[float] = deque(maxlen=period + 1)
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None
        self._prev_rsi: float | None = None

    def reset(self) -> None:
        self._closes.clear()
        self._avg_gain = None
        self._avg_loss = None
        self._prev_rsi = None

    def _rsi(self) -> float | None:
        if len(self._closes) < self.period + 1:
            return None

        changes = [b - a for a, b in zip(list(self._closes), list(self._closes)[1:])]

        if self._avg_gain is None:
            # Seed with the simple average of the first `period` changes.
            gains = [c for c in changes if c > 0]
            losses = [-c for c in changes if c < 0]
            self._avg_gain = sum(gains) / self.period
            self._avg_loss = sum(losses) / self.period
        else:
            # Wilder's smoothed average for subsequent candles.
            last = changes[-1]
            gain = last if last > 0 else 0.0
            loss = -last if last < 0 else 0.0
            self._avg_gain = (self._avg_gain * (self.period - 1) + gain) / self.period
            self._avg_loss = (self._avg_loss * (self.period - 1) + loss) / self.period

        if self._avg_loss == 0:
            return 100.0
        rs = self._avg_gain / self._avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def on_candle(self, candle: Candle) -> Signal:
        self._closes.append(candle.close)
        rsi = self._rsi()

        signal = Signal.HOLD
        if rsi is not None and self._prev_rsi is not None:
            if self._prev_rsi <= self.oversold and rsi > self.oversold:
                signal = Signal.BUY
            elif self._prev_rsi >= self.overbought and rsi < self.overbought:
                signal = Signal.SELL

        self._prev_rsi = rsi
        return signal
