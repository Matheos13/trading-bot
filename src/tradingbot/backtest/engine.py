"""Backtest engine.

Replays historical candles through a strategy, sizes trades with the risk
manager, fills them on the paper broker, and tracks the equity curve. Returns
a results summary you can print or compare across strategies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..broker.paper import PaperBroker
from ..data.feed import Candle
from ..risk.manager import RiskManager
from ..strategies.base import Signal, Strategy


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mu = _mean(xs)
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def _sharpe(returns: list[float], ann: float) -> float:
    sigma = _std(returns)
    return ann * _mean(returns) / sigma if sigma else 0.0


def _sortino(returns: list[float], ann: float) -> float:
    mu = _mean(returns)
    neg = [r for r in returns if r < 0]
    if not neg:
        return float("inf") if mu > 0 else 0.0
    downside_dev = math.sqrt(sum(r ** 2 for r in neg) / len(neg))
    return ann * mu / downside_dev if downside_dev else 0.0


@dataclass
class BacktestResult:
    start_equity: float
    end_equity: float
    trades: int
    wins: int
    max_drawdown: float
    sharpe: float = field(default=0.0)
    sortino: float = field(default=0.0)

    @property
    def return_pct(self) -> float:
        if self.start_equity == 0:
            return 0.0
        return (self.end_equity - self.start_equity) / self.start_equity * 100

    @property
    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades else 0.0

    def summary(self) -> str:
        sortino_str = f"{self.sortino:.2f}" if math.isfinite(self.sortino) else "∞"
        return (
            "Backtest results\n"
            f"  start equity : {self.start_equity:,.2f}\n"
            f"  end equity   : {self.end_equity:,.2f}\n"
            f"  return       : {self.return_pct:+.2f}%\n"
            f"  trades       : {self.trades}\n"
            f"  win rate     : {self.win_rate:.1f}%\n"
            f"  max drawdown : {self.max_drawdown:.2f}%\n"
            f"  sharpe       : {self.sharpe:.2f}\n"
            f"  sortino      : {sortino_str}"
        )


class BacktestEngine:
    def __init__(self, strategy: Strategy, risk: RiskManager,
                 starting_cash: float = 10_000.0, fee: float = 0.001,
                 periods_per_year: int = 252):
        self.strategy = strategy
        self.risk = risk
        self.broker = PaperBroker(cash=starting_cash, fee=fee)
        self.starting_cash = starting_cash
        self.periods_per_year = periods_per_year

    def run(self, candles: list[Candle]) -> BacktestResult:
        self.broker = PaperBroker(cash=self.starting_cash, fee=self.broker.fee)
        self.strategy.reset()
        peak = self.starting_cash
        max_dd = 0.0
        trades = 0
        wins = 0
        equity_curve: list[float] = [self.starting_cash]

        for candle in candles:
            price = candle.close

            pos = self.broker.position
            if pos.is_open and self.risk.stop_hit(pos.entry_price, price):
                entry = pos.entry_price
                self.broker.sell(price, pos.qty)
                trades += 1
                wins += 1 if price > entry else 0

            signal = self.strategy.on_candle(candle)

            if signal is Signal.BUY and not self.broker.position.is_open:
                equity = self.broker.equity(price)
                qty = self.risk.position_size(equity, price)
                self.broker.buy(price, qty)
            elif signal is Signal.SELL and self.broker.position.is_open:
                entry = self.broker.position.entry_price
                qty = self.broker.position.qty
                self.broker.sell(price, qty)
                trades += 1
                wins += 1 if price > entry else 0

            equity = self.broker.equity(price)
            equity_curve.append(equity)
            peak = max(peak, equity)
            if peak > 0:
                dd = (peak - equity) / peak * 100
                max_dd = max(max_dd, dd)

        if self.broker.position.is_open and candles:
            last = candles[-1].close
            entry = self.broker.position.entry_price
            self.broker.sell(last, self.broker.position.qty)
            trades += 1
            wins += 1 if last > entry else 0

        end_equity = self.broker.equity(candles[-1].close if candles else 0.0)

        returns = [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1] != 0
        ]
        ann = math.sqrt(self.periods_per_year)
        sharpe = _sharpe(returns, ann) if len(returns) >= 2 else 0.0
        sortino = _sortino(returns, ann) if len(returns) >= 2 else 0.0

        return BacktestResult(self.starting_cash, end_equity, trades, wins,
                              max_dd, sharpe, sortino)
