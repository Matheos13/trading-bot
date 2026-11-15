import pytest
from tradingbot.data.feed import Candle
from tradingbot.strategies.base import Signal
from tradingbot.strategies.sma_cross import SmaCrossStrategy
from tradingbot.strategies.rsi import RsiStrategy


def _candle(close: float) -> Candle:
    return Candle(ts=0, open=close, high=close, low=close, close=close, volume=1.0)


# ── SMA Cross ────────────────────────────────────────────────────────────────

def test_sma_cross_holds_until_enough_data():
    s = SmaCrossStrategy(fast=3, slow=5)
    for price in [10, 11, 12, 13]:
        assert s.on_candle(_candle(price)) is Signal.HOLD


def test_sma_cross_buy_signal():
    s = SmaCrossStrategy(fast=2, slow=4)
    # Feed a falling series so fast < slow, then a rising series to get crossover
    prices = [10, 9, 8, 7, 6, 5, 6, 7, 8, 9, 10, 11, 12]
    signals = [s.on_candle(_candle(p)) for p in prices]
    assert Signal.BUY in signals


def test_sma_cross_sell_signal():
    s = SmaCrossStrategy(fast=2, slow=4)
    # Rising then falling
    prices = [5, 6, 7, 8, 9, 10, 11, 10, 9, 8, 7, 6, 5]
    signals = [s.on_candle(_candle(p)) for p in prices]
    assert Signal.SELL in signals


def test_sma_cross_reset_clears_state():
    s = SmaCrossStrategy(fast=2, slow=4)
    for p in [10, 11, 12, 13, 14]:
        s.on_candle(_candle(p))
    s.reset()
    # After reset, not enough data → HOLD
    assert s.on_candle(_candle(15)) is Signal.HOLD


def test_sma_cross_invalid_params():
    with pytest.raises(ValueError):
        SmaCrossStrategy(fast=10, slow=5)


# ── RSI ──────────────────────────────────────────────────────────────────────

def test_rsi_holds_until_enough_data():
    s = RsiStrategy(period=14)
    for _ in range(14):
        assert s.on_candle(_candle(100)) is Signal.HOLD


def test_rsi_buy_on_oversold_cross():
    s = RsiStrategy(period=5, oversold=30, overbought=70)
    # Drive RSI below 30 with a sharp drop, then recover
    prices = [100] * 5 + [80, 70, 60, 50, 40] + [50, 60, 70, 80]
    signals = [s.on_candle(_candle(p)) for p in prices]
    assert Signal.BUY in signals


def test_rsi_sell_on_overbought_cross():
    s = RsiStrategy(period=5, oversold=30, overbought=70)
    # Drive RSI above 70 with a sharp rise, then drop
    prices = [100] * 5 + [120, 140, 160, 180, 200] + [180, 160, 140, 120]
    signals = [s.on_candle(_candle(p)) for p in prices]
    assert Signal.SELL in signals


def test_rsi_reset_clears_state():
    s = RsiStrategy(period=5)
    for p in [100, 110, 120, 130, 140, 150]:
        s.on_candle(_candle(p))
    s.reset()
    assert s.on_candle(_candle(100)) is Signal.HOLD


def test_rsi_invalid_params():
    with pytest.raises(ValueError):
        RsiStrategy(oversold=70, overbought=30)
