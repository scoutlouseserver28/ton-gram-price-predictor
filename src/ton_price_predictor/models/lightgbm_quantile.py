"""LightGBM quantile forecaster for TON (GRAM) price horizons."""

from __future__ import annotations

import lightgbm as lgb
import pandas as pd

from ton_price_predictor.models.base import BaseForecaster


class LightGBMQuantileForecaster(BaseForecaster):
    name = "lightgbm_quantile"

    def __init__(self, horizon_hours: int = 24, seed: int = 6767) -> None:
        self.horizon_hours = horizon_hours
        self.seed = seed
        self._feature_names: list[str] = []
        params = dict(
            objective="quantile",
            learning_rate=0.03,
            num_leaves=63,
            min_data_in_leaf=64,
            feature_fraction=0.85,
            bagging_fraction=0.85,
            bagging_freq=1,
            seed=seed,
            verbosity=-1,
        )
        self._models: dict[float, lgb.LGBMRegressor] = {
            alpha: lgb.LGBMRegressor(alpha=alpha, n_estimators=800, **params)
            for alpha in (0.05, 0.5, 0.95)
        }

    @property
    def feature_names(self) -> list[str]:
        return self._feature_names

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "LightGBMQuantileForecaster":
        self._feature_names = [c for c in features.columns if c != "target"]
        X = features[self._feature_names]
        for model in self._models.values():
            model.fit(X, target)
        return self

    def predict(self, features: pd.DataFrame) -> tuple[float, float, float]:
        if not self._feature_names:
            raise RuntimeError("model not fitted")
        X = features[self._feature_names].tail(1)
        lower = float(self._models[0.05].predict(X)[0])
        point = float(self._models[0.5].predict(X)[0])
        upper = float(self._models[0.95].predict(X)[0])
        return point, lower, upper