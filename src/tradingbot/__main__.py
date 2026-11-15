"""CLI entry point.

  tradingbot backtest                        run a backtest on synthetic data
  tradingbot backtest --live                 backtest on real candles (needs ccxt + keys)
  tradingbot backtest --strategy rsi         use RSI strategy (default: sma_cross)

  tradingbot run                             start paper trading loop (1h poll)
  tradingbot run --strategy rsi             use RSI strategy
  tradingbot run --poll 300                  poll every 300 seconds

  tradingbot sweep                           grid-search parameters on synthetic data
  tradingbot sweep --live                    grid-search on real candles
"""

from __future__ import annotations

import sys

from .backtest.engine import BacktestEngine
from .bot import TradingBot
from .sweep import print_table, run_sweep
from .config import Config
from .data.feed import fetch_ohlcv, synthetic_candles
from .risk.manager import RiskManager
from .strategies.rsi import RsiStrategy
from .strategies.sma_cross import SmaCrossStrategy

_STRATEGIES = {
    "sma_cross": lambda: SmaCrossStrategy(fast=10, slow=30),
    "rsi": lambda: RsiStrategy(period=14, oversold=30, overbought=70),
}


def _parse_strategy(args: list[str], default: str = "sma_cross") -> str:
    for i, arg in enumerate(args):
        if arg.startswith("--strategy="):
            return arg.split("=", 1)[1]
        if arg == "--strategy" and i + 1 < len(args):
            return args[i + 1]
    return default


def _parse_int_flag(args: list[str], flag: str, default: int) -> int:
    for i, arg in enumerate(args):
        if arg.startswith(f"{flag}="):
            return int(arg.split("=", 1)[1])
        if arg == flag and i + 1 < len(args):
            return int(args[i + 1])
    return default


_BACKTEST_HELP = """\
backtest — replay a strategy on historical candles

  --strategy NAME   strategy to use: sma_cross (default), rsi
  --live            fetch real candles via ccxt (needs API keys in .env)
  -h, --help        show this message
"""

_RUN_HELP = """\
run — start the paper trading loop

  --strategy NAME   strategy to use: sma_cross (default), rsi
  --poll SECONDS    how often to poll for new candles (default: 3600)
  -h, --help        show this message
"""


def _backtest(args: list[str]) -> None:
    if "-h" in args or "--help" in args:
        print(_BACKTEST_HELP)
        return
    cfg = Config.load()
    strategy_name = _parse_strategy(args)

    if strategy_name not in _STRATEGIES:
        print(f"Unknown strategy '{strategy_name}'. Available: {', '.join(_STRATEGIES)}")
        sys.exit(1)

    if "--live" in args:
        candles = fetch_ohlcv(cfg.exchange, cfg.symbol, cfg.timeframe, limit=500)
        source = f"{cfg.exchange} {cfg.symbol} {cfg.timeframe}"
    else:
        candles = synthetic_candles()
        source = "synthetic data"

    strategy = _STRATEGIES[strategy_name]()
    risk = RiskManager(cfg.risk_per_trade, cfg.stop_loss_pct)
    engine = BacktestEngine(strategy, risk, starting_cash=cfg.starting_cash)
    result = engine.run(candles)

    print(f"Strategy: {strategy.name}  |  Data: {source}  |  Candles: {len(candles)}")
    print(result.summary())


def _run(args: list[str]) -> None:
    if "-h" in args or "--help" in args:
        print(_RUN_HELP)
        return
    cfg = Config.load()
    strategy_name = _parse_strategy(args)
    poll = _parse_int_flag(args, "--poll", default=3600)

    if strategy_name not in _STRATEGIES:
        print(f"Unknown strategy '{strategy_name}'. Available: {', '.join(_STRATEGIES)}")
        sys.exit(1)

    strategy = _STRATEGIES[strategy_name]()
    bot = TradingBot(cfg, strategy)
    try:
        bot.run_forever(poll_seconds=poll)
    except KeyboardInterrupt:
        price_hint = bot.broker.equity(0)  # cash only after Ctrl+C
        print(f"\n[paper] stopped.  cash={bot.broker.cash:,.2f}")


def _sweep(args: list[str]) -> None:
    if "-h" in args or "--help" in args:
        print("sweep — grid-search strategy parameters\n\n"
              "  --live      use real candles (default: synthetic)\n"
              "  -h, --help  show this message\n")
        return
    cfg = Config.load()
    if "--live" in args:
        candles = fetch_ohlcv(cfg.exchange, cfg.symbol, cfg.timeframe, limit=500)
        source = f"{cfg.exchange} {cfg.symbol} {cfg.timeframe}"
    else:
        candles = synthetic_candles()
        source = "synthetic data"

    risk = RiskManager(cfg.risk_per_trade, cfg.stop_loss_pct)
    print(f"Sweeping parameters  |  Data: {source}  |  Candles: {len(candles)}\n")
    rows = run_sweep(candles, risk, starting_cash=cfg.starting_cash)
    print_table(rows)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "backtest":
        _backtest(args[1:])
        return
    if args[0] == "run":
        _run(args[1:])
        return
    if args[0] == "sweep":
        _sweep(args[1:])
        return
    print(f"Unknown command: {args[0]}\n")
    print(__doc__)


if __name__ == "__main__":
    main()
