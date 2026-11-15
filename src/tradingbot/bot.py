"""Live/paper trading loop.

Wires a strategy to a broker and steps it forward on each new candle. This is
the skeleton for real-time trading; it runs in paper mode by default. Do NOT
switch to a live broker until a strategy has proven itself in backtests and
extended paper trading.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime

from .broker.paper import PaperBroker
from .config import Config
from .data.feed import fetch_ohlcv
from .risk.manager import RiskManager
from .strategies.base import Signal, Strategy


def _notify(title: str, body: str) -> None:
    """Send a macOS desktop notification. Silent no-op on non-macOS."""
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{body}" with title "{title}"'],
            check=False, capture_output=True,
        )
    except FileNotFoundError:
        pass


class TradingBot:
    def __init__(self, config: Config, strategy: Strategy):
        self.config = config
        self.strategy = strategy
        self.risk = RiskManager(config.risk_per_trade, config.stop_loss_pct)
        # Only the paper broker is wired up for now — live is intentionally absent.
        self.broker = PaperBroker(cash=config.starting_cash)

    def step(self, price: float, signal: Signal) -> None:
        sym = self.config.symbol
        pos = self.broker.position

        if pos.is_open and self.risk.stop_hit(pos.entry_price, price):
            self.broker.sell(price, pos.qty)
            if not self.broker.position.is_open:
                eq = self.broker.equity(price)
                _notify(f"[paper] STOP-LOSS — {sym}",
                        f"Sold @ {price:,.2f}  |  equity {eq:,.2f}")

        if signal is Signal.BUY and not self.broker.position.is_open:
            qty = self.risk.position_size(self.broker.equity(price), price)
            self.broker.buy(price, qty)
            if self.broker.position.is_open:
                eq = self.broker.equity(price)
                _notify(f"[paper] BUY — {sym}",
                        f"Bought @ {price:,.2f}  |  equity {eq:,.2f}")

        elif signal is Signal.SELL and self.broker.position.is_open:
            self.broker.sell(price, self.broker.position.qty)
            if not self.broker.position.is_open:
                eq = self.broker.equity(price)
                _notify(f"[paper] SELL — {sym}",
                        f"Sold @ {price:,.2f}  |  equity {eq:,.2f}")

    def run_once(self) -> tuple[float, Signal]:
        """Pull the latest candles, feed the strategy, act once.

        Returns (equity, last_signal).
        """
        candles = fetch_ohlcv(
            self.config.exchange, self.config.symbol,
            self.config.timeframe, limit=self.config.limit,
        )
        self.strategy.reset()
        signal = Signal.HOLD
        for candle in candles:
            signal = self.strategy.on_candle(candle)
        price = candles[-1].close
        self.step(price, signal)
        return self.broker.equity(price), signal

    def run_forever(self, poll_seconds: int = 3600) -> None:  # pragma: no cover
        if self.config.mode == "live":
            raise RuntimeError(
                "Live mode is not implemented. Paper-trade and backtest first."
            )
        sys.stdout.reconfigure(line_buffering=True)  # flush every line when piped
        print(
            f"[paper] starting  strategy={self.strategy.name}"
            f"  symbol={self.config.symbol}  poll={poll_seconds}s"
            f"  cash={self.config.starting_cash:,.2f}"
        )
        while True:
            try:
                equity, signal = self.run_once()
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[paper] {ts}  signal={signal.value:<4}  equity={equity:,.2f}")
            except Exception as exc:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[paper] {ts}  ERROR: {exc} — retrying next poll")
            time.sleep(poll_seconds)
