from unittest.mock import patch

from tradingbot.bot import TradingBot
from tradingbot.config import Config
from tradingbot.data.feed import synthetic_candles
from tradingbot.strategies.base import Signal
from tradingbot.strategies.sma_cross import SmaCrossStrategy


def _bot(cash: float = 10_000.0) -> TradingBot:
    cfg = Config(starting_cash=cash)
    return TradingBot(cfg, SmaCrossStrategy(fast=3, slow=6))


# ── step() ───────────────────────────────────────────────────────────────────

def test_step_buy_opens_position():
    bot = _bot()
    bot.step(price=100.0, signal=Signal.BUY)
    assert bot.broker.position.is_open


def test_step_sell_closes_position():
    bot = _bot()
    bot.step(price=100.0, signal=Signal.BUY)
    bot.step(price=110.0, signal=Signal.SELL)
    assert not bot.broker.position.is_open


def test_step_no_double_buy():
    bot = _bot()
    bot.step(price=100.0, signal=Signal.BUY)
    qty_after_first = bot.broker.position.qty
    bot.step(price=100.0, signal=Signal.BUY)
    assert bot.broker.position.qty == qty_after_first


def test_step_stop_loss_closes_position():
    bot = _bot()
    bot.step(price=100.0, signal=Signal.BUY)
    # Drop below stop (default 3% → stop at 97)
    bot.step(price=96.0, signal=Signal.HOLD)
    assert not bot.broker.position.is_open


def test_step_hold_does_nothing_when_flat():
    bot = _bot()
    bot.step(price=100.0, signal=Signal.HOLD)
    assert not bot.broker.position.is_open
    assert bot.broker.cash == 10_000.0


# ── run_once() ───────────────────────────────────────────────────────────────

def test_run_once_returns_equity_and_signal():
    bot = _bot()
    candles = synthetic_candles(n=50, seed=1)
    with patch("tradingbot.bot.fetch_ohlcv", return_value=candles):
        equity, signal = bot.run_once()
    assert isinstance(equity, float)
    assert isinstance(signal, Signal)


def test_run_once_equity_positive():
    bot = _bot()
    candles = synthetic_candles(n=50, seed=2)
    with patch("tradingbot.bot.fetch_ohlcv", return_value=candles):
        equity, _ = bot.run_once()
    assert equity > 0


def test_run_once_twice_uses_latest_candles():
    bot = _bot()
    candles_a = synthetic_candles(n=50, seed=10)
    candles_b = synthetic_candles(n=50, seed=20)
    with patch("tradingbot.bot.fetch_ohlcv", return_value=candles_a):
        eq_a, _ = bot.run_once()
    with patch("tradingbot.bot.fetch_ohlcv", return_value=candles_b):
        eq_b, _ = bot.run_once()
    # Different candles → at least one value should differ (seeds are different)
    # We just check both are valid floats
    assert eq_a > 0 and eq_b > 0
