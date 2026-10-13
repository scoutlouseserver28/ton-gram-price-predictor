"""Weighted ensemble that blends the individual forecasters and returns a band."""

from __future__ import annotations

import pandas as pd

from ton_price_predictor.config.loader import ModelCfg
from ton_price_predictor.models.base import BaseForecaster
from ton_price_predictor.models.lightgbm_quantile import LightGBMQuantileForecaster
from ton_price_predictor.models.ridge_arima import RidgeARIMAForecaster

_REGISTRY: dict[str, type[BaseForecaster]] = {
    "lightgbm_quantile": LightGBMQuantileForecaster,
    "ridge_arima": RidgeARIMAForecaster,
}


class EnsembleForecaster:
    def __init__(self, cfg: ModelCfg) -> None:
        self.cfg = cfg
        self.members: dict[str, BaseForecaster] = {
            name: _REGISTRY[name](horizon_hours=cfg.horizons_hours[-1])
            for name in cfg.ensemble_weights
            if name in _REGISTRY
        }
        self._fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "EnsembleForecaster":
        for member in self.members.values():
            member.fit(features, target)
        self._fitted = True
        return self

    def forecast(
        self, features: pd.DataFrame, horizon_hours: int
    ) -> tuple[float, float, float, dict[str, float]]:
        if not self._fitted:
            # Lazy fit on the provided frame — good enough for a single-shot CLI call.
            target = features["close"].pct_change().shift(-horizon_hours).dropna()
            self.fit(features.loc[target.index], target)

        weights = self.cfg.ensemble_weights
        total_w = sum(weights.values()) or 1.0
        points: dict[str, float] = {}
        lowers: list[float] = []
        uppers: list[float] = []
        blended = 0.0
        for name, member in self.members.items():
            w = weights.get(name, 0.0) / total_w
            p, lo, hi = member.predict(features)
            points[name] = p
            blended += w * p
            lowers.append(lo)
            uppers.append(hi)

        lower = min(lowers) if lowers else blended * 0.98
        upper = max(uppers) if uppers else blended * 1.02
        return blended, lower, upper, points