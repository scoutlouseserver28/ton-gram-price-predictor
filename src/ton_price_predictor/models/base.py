"""Abstract forecaster interface implemented by every model in the ensemble."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseForecaster(ABC):
    """Contract: fit on a feature frame, predict a point + quantile band."""

    name: str = "base"

    @property
    @abstractmethod
    def feature_names(self) -> list[str]:
        ...

    @abstractmethod
    def fit(self, features: pd.DataFrame, target: pd.Series) -> "BaseForecaster":
        ...

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> tuple[float, float, float]:
        """Return ``(point, lower, upper)`` for the last row of ``features``."""
        ...