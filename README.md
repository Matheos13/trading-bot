# trading-bot

A modular crypto trading bot — backtest strategies, sweep parameters, and paper-trade live before risking a cent.

> ⚠️ Not financial advice. Trading is risky and most bots lose money. Live trading is intentionally not wired up until a strategy is proven.

---

## Install

```bash
pip install -e .                  # backtest on synthetic data, no other deps
pip install -e ".[live]"          # adds ccxt for real exchange data
cp .env.example .env              # configure exchange, symbol, timeframe
```

---

## Commands

### `backtest`

Replay a strategy on historical candles and print a performance summary.

```bash
tradingbot backtest                          # synthetic data, sma_cross
tradingbot backtest --strategy rsi           # use RSI strategy
tradingbot backtest --live                   # real candles from your exchange
tradingbot backtest --strategy rsi --live
```

Example output:

![Backtest output](docs/backtest.png)

```
Strategy: sma_cross  |  Data: binance BTC/USDT 1h  |  Candles: 500
Backtest results
  start equity : 10,000.00
  end equity   : 10,115.51
  return       : +1.16%
  trades       : 9
  win rate     : 55.6%
  max drawdown : 3.20%
  sharpe       : 0.29
  sortino      : 0.25
```

---

### `sweep`

Grid-search across many parameter combinations and rank them by return.

```bash
tradingbot sweep                             # synthetic data
tradingbot sweep --live                      # real candles
```

Tests 42 combinations: SMA fast/slow pairs (5–20 / 20–100) and RSI period/threshold combos (period 7/14/21, oversold 20–30, overbought 70–80). Results are sorted best-to-worst:

```
──────────────────────────────────────────────────────────────────────────────────────────────
#    strategy    params                      return   sharpe   sortino    win%      dd%  trades
──────────────────────────────────────────────────────────────────────────────────────────────
1    sma_cross   fast=5 slow=50              +2.11%    +0.41     +0.38   60.0%    2.34%       5
2    rsi         period=14 os=25 ob=75       +1.87%    +0.35     +0.29   57.1%    3.10%       7
...
```

Use this to find which params work on a given market before committing to one.

---

### `run`

Start the paper trading loop. Fetches live candles on a timer, runs the strategy, and executes simulated fills.

```bash
tradingbot run                               # sma_cross, poll every 1h
tradingbot run --strategy rsi               # use RSI
tradingbot run --strategy sma_cross --poll 60   # poll every 60 seconds
```

Example output:

```
[paper] starting  strategy=sma_cross  symbol=BTC/USDT  poll=60s  cash=10,000.00
[paper] 2026-11-15 04:09:33  signal=hold  equity=10,000.00
[paper] 2026-11-15 04:10:35  signal=hold  equity=10,000.00
[paper] 2026-11-15 04:11:38  signal=buy   equity=10,000.00
```

Network errors (dropped connections, exchange timeouts) are caught and logged — the bot retries on the next poll instead of crashing.

Press `Ctrl+C` to stop. Final cash is printed on exit.

#### Mac desktop notifications

When the bot opens or closes a position, it sends a macOS notification:

- **`[paper] BUY — BTC/USDT`** · `Bought @ 95,432.00  |  equity 10,187.34`
- **`[paper] SELL — BTC/USDT`** · `Sold @ 96,100.00  |  equity 10,243.11`
- **`[paper] STOP-LOSS — BTC/USDT`** · `Sold @ 92,569.00  |  equity 9,812.45`

No notification fires on HOLD. Silent no-op on non-macOS.

---

## Strategies

### `sma_cross`

Buys when the fast SMA crosses above the slow SMA, sells when it crosses back below. Defaults: `fast=10, slow=30`.

Good for: trending markets. Struggles in choppy/sideways price action.

### `rsi`

Buys when RSI crosses back above the oversold level, sells when it crosses back below the overbought level. Uses Wilder's smoothed average. Defaults: `period=14, oversold=30, overbought=70`.

Good for: mean-reverting markets. Struggles in strong trends.

### Writing your own

Subclass `Strategy`, implement `on_candle`, return a `Signal`:

```python
from tradingbot.strategies.base import Strategy, Signal

class MyStrategy(Strategy):
    name = "my_strategy"

    def on_candle(self, candle):
        # candle.open, candle.high, candle.low, candle.close, candle.volume
        return Signal.HOLD  # or Signal.BUY / Signal.SELL
```

Then register it in `_STRATEGIES` in `__main__.py`.

---

## Configuration

All settings are read from environment variables (or a `.env` file):

| Variable | Default | Description |
|---|---|---|
| `EXCHANGE` | `binance` | ccxt exchange ID |
| `SYMBOL` | `BTC/USDT` | trading pair |
| `TIMEFRAME` | `1h` | candle interval |
| `RISK_PER_TRADE` | `0.02` | fraction of equity risked per trade |
| `STOP_LOSS_PCT` | `0.03` | stop distance as fraction of entry price |
| `STARTING_CASH` | `10000` | starting paper balance |
| `LIMIT` | `200` | candles fetched per poll |
| `MODE` | `paper` | `paper` only — live is not implemented |

---

## Project layout

```
src/tradingbot/
├── config.py            # settings, loaded from .env
├── data/feed.py         # OHLCV candles: ccxt (live) or synthetic (offline)
├── strategies/
│   ├── base.py          # Strategy interface + Signal enum
│   ├── sma_cross.py     # SMA crossover
│   └── rsi.py           # RSI mean-reversion
├── broker/
│   ├── base.py          # Broker interface
│   └── paper.py         # simulated fills, no real money
├── risk/manager.py      # position sizing + stop-losses
├── backtest/engine.py   # replay candles, equity curve, Sharpe/Sortino
├── sweep.py             # parameter grid-search
└── bot.py               # paper trading loop + Mac notifications
```

---

## Safety

Keep `MODE=paper`. Never commit your `.env`. A green backtest is not a promise — markets change, and overfitting is easy. Paper-trade for weeks before considering real funds.

## License

MIT
