"""Configuration, loaded from environment / .env.

Keep all tunables here so no module reaches for os.environ on its own.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader so we don't need a dependency for one file."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


@dataclass
class Config:
    exchange: str = "binance"
    api_key: str = ""
    api_secret: str = ""
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    risk_per_trade: float = 0.02      # fraction of equity risked per trade
    stop_loss_pct: float = 0.03       # stop distance as fraction of entry price
    mode: str = "paper"               # "paper" | "live"
    starting_cash: float = 10_000.0
    limit: int = 200                  # candles to fetch per poll

    @classmethod
    def load(cls) -> "Config":
        _load_dotenv()
        return cls(
            exchange=os.environ.get("EXCHANGE", "binance"),
            api_key=os.environ.get("API_KEY", ""),
            api_secret=os.environ.get("API_SECRET", ""),
            symbol=os.environ.get("SYMBOL", "BTC/USDT"),
            timeframe=os.environ.get("TIMEFRAME", "1h"),
            risk_per_trade=float(os.environ.get("RISK_PER_TRADE", "0.02")),
            stop_loss_pct=float(os.environ.get("STOP_LOSS_PCT", "0.03")),
            mode=os.environ.get("MODE", "paper"),
            starting_cash=float(os.environ.get("STARTING_CASH", "10000")),
            limit=int(os.environ.get("LIMIT", "200")),
        )
