"""Market data feed.

Two sources behind one interface:
  - ccxt, for real exchange OHLCV (needs the `live` extra installed)
  - a synthetic random-walk generator, so the backtester runs with zero setup

A Candle is (timestamp_ms, open, high, low, close, volume).
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Candle:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def synthetic_candles(n: int = 500, start: float = 30_000.0,
                      seed: int | None = 42) -> list[Candle]:
    """A random walk with mild trend + noise — enough for a strategy to trade."""
    rng = random.Random(seed)
    candles: list[Candle] = []
    price = start
    ts = 0
    for _ in range(n):
        drift = rng.uniform(-0.004, 0.0045)      # slight upward bias
        o = price
        c = max(1.0, o * (1 + drift))
        hi = max(o, c) * (1 + rng.uniform(0, 0.004))
        lo = min(o, c) * (1 - rng.uniform(0, 0.004))
        vol = rng.uniform(10, 100)
        candles.append(Candle(ts, o, hi, lo, c, vol))
        price = c
        ts += 3_600_000                           # 1h steps
    return candles


def fetch_ohlcv(exchange: str, symbol: str, timeframe: str,
                limit: int = 500) -> list[Candle]:
    """Fetch real candles via ccxt. Raises if ccxt isn't installed."""
    try:
        import ccxt  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "ccxt not installed. Run `pip install trading-bot[live]`, "
            "or use synthetic_candles() for backtesting."
        ) from exc

    client = getattr(ccxt, exchange)()
    raw = client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return [Candle(ts, o, h, l, c, v) for ts, o, h, l, c, v in raw]
