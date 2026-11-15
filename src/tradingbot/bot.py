"""Live/paper trading loop.

Wires a strategy to a broker and steps it forward on each new candle. This is
the skeleton for real-time trading; it runs in paper mode by default. Do NOT
switch to a live broker until a strategy has proven itself in backtests and
extended paper trading.
"""

from __future__ import annotations

import time
from datetime import datetime

from .broker.paper import PaperBroker
from .config import Config
from .data.feed import fetch_ohlcv
from .risk.manager import RiskManager
from .strategies.base import Signal, Strategy


class TradingBot:
    def __init__(self, config: Config, strategy: Strategy):
        self.config = config
        self.strategy = strategy
        self.risk = RiskManager(config.risk_per_trade, config.stop_loss_pct)
        # Only the paper broker is wired up for now — live is intentionally absent.
        self.broker = PaperBroker(cash=config.starting_cash)

    def step(self, price: float, signal: Signal) -> None:
        pos = self.broker.position
        if pos.is_open and self.risk.stop_hit(pos.entry_price, price):
            self.broker.sell(price, pos.qty)
        if signal is Signal.BUY and not self.broker.position.is_open:
            qty = self.risk.position_size(self.broker.equity(price), price)
            self.broker.buy(price, qty)
        elif signal is Signal.SELL and self.broker.position.is_open:
            self.broker.sell(price, self.broker.position.qty)

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
        print(
            f"[paper] starting  strategy={self.strategy.name}"
            f"  symbol={self.config.symbol}  poll={poll_seconds}s"
            f"  cash={self.config.starting_cash:,.2f}"
        )
        while True:
            equity, signal = self.run_once()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[paper] {ts}  signal={signal.value:<4}  equity={equity:,.2f}")
            time.sleep(poll_seconds)
