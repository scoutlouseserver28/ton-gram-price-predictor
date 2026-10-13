"""Contract for market-data adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ton_price_predictor.core.types import Candle


class MarketDataAdapter(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, days: int) -> list[Candle]:
        ...

    @abstractmethod
    async def fetch_onchain(self, days: int) -> dict[str, list[float]]:
        ...
</｜｜DSML｜｜ parameter>
</｜｜DSML｜｜ invoke>
</｜｜DSML｜｜ calls>