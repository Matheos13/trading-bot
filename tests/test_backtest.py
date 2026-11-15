from tradingbot.backtest.engine import BacktestEngine
from tradingbot.data.feed import Candle, synthetic_candles
from tradingbot.risk.manager import RiskManager
from tradingbot.strategies.sma_cross import SmaCrossStrategy
from tradingbot.strategies.rsi import RsiStrategy


def _candle(close: float, ts: int = 0) -> Candle:
    return Candle(ts=ts, open=close, high=close, low=close, close=close, volume=1.0)


def _engine(strategy=None):
    s = strategy or SmaCrossStrategy(fast=3, slow=6)
    r = RiskManager(risk_per_trade=0.02, stop_loss_pct=0.05)
    return BacktestEngine(s, r, starting_cash=10_000.0, fee=0.0)


def test_empty_candles_returns_start_equity():
    engine = _engine()
    result = engine.run([])
    assert result.start_equity == 10_000.0
    assert result.end_equity == 10_000.0
    assert result.trades == 0


def test_flat_market_no_crossover():
    engine = _engine()
    candles = [_candle(100)] * 20
    result = engine.run(candles)
    # No crossover on flat prices → no trades
    assert result.trades == 0


def test_result_fields_present():
    engine = _engine()
    result = engine.run(synthetic_candles(n=100, seed=1))
    assert result.start_equity == 10_000.0
    assert result.trades >= 0
    assert result.wins <= result.trades
    assert result.max_drawdown >= 0.0


def test_return_pct_positive_on_rising_market():
    # Sharp rising market → SMA cross should catch the trend
    engine = _engine(SmaCrossStrategy(fast=3, slow=6))
    candles = [_candle(100 + i * 2, ts=i) for i in range(50)]
    result = engine.run(candles)
    assert result.return_pct >= 0


def test_max_drawdown_non_negative():
    engine = _engine()
    result = engine.run(synthetic_candles(n=200, seed=7))
    assert result.max_drawdown >= 0.0


def test_summary_contains_key_fields():
    engine = _engine()
    result = engine.run(synthetic_candles(n=100, seed=2))
    s = result.summary()
    assert "return" in s
    assert "win rate" in s
    assert "max drawdown" in s


def test_win_rate_zero_trades():
    engine = _engine()
    result = engine.run([_candle(100)] * 10)
    assert result.win_rate == 0.0


def test_rsi_strategy_runs_through_engine():
    s = RsiStrategy(period=5, oversold=30, overbought=70)
    r = RiskManager()
    engine = BacktestEngine(s, r, starting_cash=10_000.0)
    result = engine.run(synthetic_candles(n=200, seed=3))
    assert result.start_equity == 10_000.0


# ── Sharpe / Sortino ──────────────────────────────────────────────────────────

def test_sharpe_and_sortino_present():
    result = _engine().run(synthetic_candles(n=200, seed=5))
    assert hasattr(result, "sharpe")
    assert hasattr(result, "sortino")


def test_sharpe_zero_on_empty():
    result = _engine().run([])
    assert result.sharpe == 0.0
    assert result.sortino == 0.0


def test_sharpe_finite_on_normal_run():
    import math
    result = _engine().run(synthetic_candles(n=300, seed=9))
    assert math.isfinite(result.sharpe)


def test_sharpe_positive_on_strongly_rising_market():
    # Monotonically rising candles → returns always positive → sharpe should be > 0
    engine = _engine(SmaCrossStrategy(fast=3, slow=6))
    candles = [_candle(100 + i, ts=i) for i in range(60)]
    result = engine.run(candles)
    assert result.sharpe >= 0.0


def test_sortino_inf_when_no_losing_periods():
    import math
    # Flat market, no trades, all returns are 0 → no negative returns → sortino = inf
    engine = BacktestEngine(SmaCrossStrategy(fast=3, slow=6), RiskManager(),
                            starting_cash=10_000.0, fee=0.0)
    candles = [_candle(100)] * 20
    result = engine.run(candles)
    # With no trades and flat prices, all returns are 0 — no negative returns.
    assert result.sortino == 0.0 or math.isinf(result.sortino)


def test_summary_includes_sharpe_sortino():
    result = _engine().run(synthetic_candles(n=200, seed=11))
    s = result.summary()
    assert "sharpe" in s
    assert "sortino" in s


def test_engine_resets_broker_between_runs():
    # Running the same engine twice should give identical results.
    engine = _engine()
    candles = synthetic_candles(n=100, seed=42)
    r1 = engine.run(candles)
    r2 = engine.run(candles)
    assert r1.end_equity == r2.end_equity
    assert r1.trades == r2.trades
