# trading-bot

A modular crypto trading bot built to be understood, tested, and extended — **backtest and paper-trade first, risk real money last (if ever).**

> ⚠️ Not financial advice. Trading is risky and most bots lose money. This is a learning project. Live trading is intentionally not wired up until a strategy is proven.

## What's inside

```
src/tradingbot/
├── config.py            # all settings, loaded from .env
├── data/feed.py         # OHLCV candles: ccxt (live) or synthetic (offline)
├── strategies/
│   ├── base.py          # Strategy interface + Signal enum
│   └── sma_cross.py     # SMA crossover (the starter strategy)
├── broker/
│   ├── base.py          # Broker interface
│   └── paper.py         # simulated fills, no real money
├── risk/manager.py      # position sizing + stop losses
├── backtest/engine.py   # replay candles, track equity + drawdown
└── bot.py               # live/paper loop (paper only for now)
```

Each piece does one job and talks to the next through a small interface, so you can swap a strategy or broker without touching the rest.

## Quick start

```bash
pip install -e .
tradingbot backtest
```

Example output:

```
Strategy: sma_cross  |  Data: synthetic data  |  Candles: 500
Backtest results
  start equity : 10,000.00
  end equity   : 10,115.51
  return       : +1.16%
  trades       : 9
  win rate     : 55.6%
  max drawdown : 3.20%
```

Runs with zero setup on synthetic data. To backtest on real candles:

```bash
pip install -e ".[live]"      # adds ccxt
cp .env.example .env          # set EXCHANGE/SYMBOL/TIMEFRAME
tradingbot backtest --live
```

## How a trade happens

1. `data/feed` yields the next candle.
2. `strategies/sma_cross` sees it and returns BUY / SELL / HOLD.
3. `risk/manager` sizes the trade so a stop-loss costs a fixed % of equity.
4. `broker/paper` fills it and updates cash + position.
5. `backtest/engine` records the equity curve and drawdown.

## Writing your own strategy

Subclass `Strategy`, implement `on_candle`, return a `Signal`:

```python
from tradingbot.strategies.base import Strategy, Signal

class MyStrategy(Strategy):
    name = "my_strategy"
    def on_candle(self, candle):
        return Signal.HOLD
```

## Roadmap

- [ ] more strategies (RSI, breakout, mean-reversion)
- [ ] walk-forward + out-of-sample testing
- [ ] real broker adapter (behind heavy guardrails)
- [ ] metrics: Sharpe, Sortino, profit factor
- [ ] parameter sweep / optimization

## Safety

Keep `MODE=paper`. Never commit your `.env`. A green backtest is not a promise — markets change, and overfitting is easy. Paper-trade for weeks before you even think about real funds.

## License

MIT
