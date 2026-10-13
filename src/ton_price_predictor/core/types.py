"""Shared dataclasses and enums for the prediction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class Horizon(StrEnum):
    H1 = "1h"
    H6 = "6h"
    H24 = "24h"
    H168 = "168h"


@dataclass(slots=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = "TONUSDT"


@dataclass(slots=True)
class Prediction:
    symbol: str
    horizon_hours: int
    point: float
    lower: float
    upper: float
    direction: Direction
    confidence: float
    generated_at: datetime
    model_breakdown: dict[str, float] = field(default_factory=dict)

    def as_table(self) -> str:
        band = f"{self.lower:.4f} .. {self.upper:.4f}"
        return (
            f"{self.symbol} +{self.horizon_hours}h -> {self.point:.4f} USDT "
            f"({self.direction.value}, conf={self.confidence:.2f}) | band {band}"
        )


@dataclass(slots=True)
class BacktestReport:
    trades: int
    hit_rate: float
    sharpe: float
    max_drawdown: float
    pnl_pct: float

    def summary(self) -> str:
        return (
            f"trades={self.trades} hit={self.hit_rate:.2%} "
            f"sharpe={self.sharpe:.2f} mdd={self.max_drawdown:.2%} "
            f"pnl={self.pnl_pct:.2%}"
        )