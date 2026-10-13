"""Top-level orchestration: fetch -> featurize -> predict -> backtest."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pandas as pd
import structlog

from ton_price_predictor.config.loader import Settings
from ton_price_predictor.core.types import BacktestReport, Direction, Prediction
from ton_price_predictor.features.engineer import FeatureEngineer
from ton_price_predictor.models.ensemble import EnsembleForecaster
from ton_price_predictor.services.market_data import MarketDataService
from ton_price_predictor.utils.backtest import walk_forward

log = structlog.get_logger(__name__)


class PredictionPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.data = MarketDataService(settings)
        self.features = FeatureEngineer(settings.features)
        self.model = EnsembleForecaster(settings.model)

    def _frame(self, symbol: str) -> pd.DataFrame:
        candles = asyncio.run(self.data.load_cached(symbol))
        df = pd.DataFrame([c.__dict__ for c in candles])
        if df.empty:
            raise RuntimeError(f"no cached candles for {symbol}; run `tonpredict fetch` first")
        df = df.set_index("ts").sort_index()
        return self.features.transform(df)

    def predict(self, *, symbol: str, horizon_hours: int) -> Prediction:
        df = self._frame(symbol)
        point, lower, upper, breakdown = self.model.forecast(df, horizon_hours)
        last = float(df["close"].iloc[-1])
        delta = (point - last) / last
        direction = Direction.UP if delta > 0.005 else Direction.DOWN if delta < -0.005 else Direction.FLAT
        confidence = max(0.0, min(1.0, 1.0 - (upper - lower) / max(point, 1e-9)))
        return Prediction(
            symbol=symbol,
            horizon_hours=horizon_hours,
            point=point,
            lower=lower,
            upper=upper,
            direction=direction,
            confidence=confidence,
            generated_at=datetime.now(timezone.utc),
            model_breakdown=breakdown,
        )

    def backtest(self) -> BacktestReport:
        df = self._frame("TONUSDT")
        return walk_forward(
            df,
            self.model,
            fee_bps=self.settings.backtest.fee_bps,
            slippage_bps=self.settings.backtest.slippage_bps,
        )