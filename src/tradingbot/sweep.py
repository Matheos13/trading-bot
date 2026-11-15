"""Parameter sweep — grid-search over strategy configs and rank by return.

Builds a grid of SMA fast/slow pairs and RSI period/threshold combos, runs
each through the backtest engine on the same candle set, then prints a table
sorted best-to-worst by return.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

from .backtest.engine import BacktestEngine, BacktestResult
from .data.feed import Candle
from .risk.manager import RiskManager
from .strategies.rsi import RsiStrategy
from .strategies.sma_cross import SmaCrossStrategy


@dataclass
class SweepRow:
    strategy: str
    params: str
    result: BacktestResult


def _sma_grid() -> list[tuple[str, SmaCrossStrategy]]:
    combos = []
    for fast, slow in product([5, 10, 15, 20], [20, 30, 50, 100]):
        if fast < slow:
            combos.append((f"fast={fast} slow={slow}", SmaCrossStrategy(fast, slow)))
    return combos


def _rsi_grid() -> list[tuple[str, RsiStrategy]]:
    combos = []
    for period, oversold, overbought in product([7, 14, 21], [20, 25, 30], [70, 75, 80]):
        label = f"period={period} os={oversold} ob={overbought}"
        combos.append((label, RsiStrategy(period, oversold, overbought)))
    return combos


def run_sweep(candles: list[Candle], risk: RiskManager,
              starting_cash: float = 10_000.0) -> list[SweepRow]:
    rows: list[SweepRow] = []

    for params, strategy in _sma_grid() + _rsi_grid():
        engine = BacktestEngine(strategy, risk, starting_cash=starting_cash, fee=0.001)
        result = engine.run(candles)
        rows.append(SweepRow(strategy.name, params, result))

    rows.sort(key=lambda r: r.result.return_pct, reverse=True)
    return rows


def print_table(rows: list[SweepRow]) -> None:
    C = {
        "rank":     3,
        "strategy": 10,
        "params":   24,
        "return":   8,
        "sharpe":   7,
        "sortino":  8,
        "win":      6,
        "dd":       7,
        "trades":   6,
    }

    def _row(*cells) -> str:
        widths = list(C.values())
        return "  ".join(str(c).ljust(w) if i < 3 else str(c).rjust(w)
                         for i, (c, w) in enumerate(zip(cells, widths)))

    header = _row("#", "strategy", "params", "return", "sharpe",
                  "sortino", "win%", "dd%", "trades")
    sep = "─" * len(header)

    print(sep)
    print(header)
    print(sep)

    for i, row in enumerate(rows, 1):
        r = row.result
        sortino = "∞" if math.isinf(r.sortino) else f"{r.sortino:+.2f}"
        print(_row(
            i,
            row.strategy,
            row.params,
            f"{r.return_pct:+.2f}%",
            f"{r.sharpe:+.2f}",
            sortino,
            f"{r.win_rate:.1f}%",
            f"{r.max_drawdown:.2f}%",
            r.trades,
        ))

    print(sep)
    print(f"  {len(rows)} combinations  |  ranked by return")
