"""Ridge-on-ARIMA-residuals baseline. Cheap, deterministic, hard to beat."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from ton_price_predictor.models.base import BaseForecaster


class RidgeARIMAForecaster(BaseForecaster):
    name = "ridge_arima"

    def __init__(self, lags: int = 24, alpha: float = 1.0) -> None:
        self.lags = lags
        self.alpha = alpha
        self._feature_names: list[str] = []
        self._model = Ridge(alpha=alpha)
        self._resid_std = 0.0

    @property
    def feature_names(self) -> list[str]:
        return self._feature_names

    def _lag_frame(self, closes: pd.Series) -> pd.DataFrame:
        return pd.concat(
            [closes.shift(i).rename(f"lag_{i}") for i in range(1, self.lags + 1)],
            axis=1,
        )

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "RidgeARIMAForecaster":
        closes = features["close"]
        lagged = self._lag_frame(closes).dropna()
        aligned = target.loc[lagged.index]
        self._feature_names = list(lagged.columns)
        self._model.fit(lagged, aligned)
        resid = aligned - self._model.predict(lagged)
        self._resid_std = float(np.std(resid))
        return self

    def predict(self, features: pd.DataFrame) -> tuple[float, float, float]:
        if not self._feature_names:
            raise RuntimeError("model not fitted")
        row = self._lag_frame(features["close"]).tail(1)
        point = float(self._model.predict(row)[0])
        z = 1.645
        return point, point - z * self._resid_std, point + z * self._resid_std