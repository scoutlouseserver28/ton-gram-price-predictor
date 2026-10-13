"""YAML + env config loader with pydantic validation."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class SourceCfg(BaseModel):
    base_url: str
    api_key_env: str | None = None
    rate_limit_per_min: int = 60
    symbol: str | None = None
    interval: str | None = None


class DataCfg(BaseModel):
    cache_dir: Path = Path("data/cache")
    raw_dir: Path = Path("data/raw")
    history_days: int = 720
    resample: str = "1h"


class FeatureCfg(BaseModel):
    windows: list[int] = Field(default_factory=lambda: [6, 24, 72, 168])
    indicators: list[str] = Field(default_factory=list)
    onchain: list[str] = Field(default_factory=list)


class ModelCfg(BaseModel):
    primary: str = "lightgbm_quantile"
    ensemble_weights: dict[str, float] = Field(default_factory=dict)
    horizons_hours: list[int] = Field(default_factory=lambda: [1, 6, 24, 168])


class BacktestCfg(BaseModel):
    start: str
    end: str
    fee_bps: int = 10
    slippage_bps: int = 5


class Settings(BaseModel):
    app: dict[str, Any] = Field(default_factory=dict)
    logging: dict[str, Any] = Field(default_factory=dict)
    data: DataCfg = Field(default_factory=DataCfg)
    sources: dict[str, SourceCfg] = Field(default_factory=dict)
    features: FeatureCfg = Field(default_factory=FeatureCfg)
    model: ModelCfg = Field(default_factory=ModelCfg)
    backtest: BacktestCfg


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_env(cfg: dict[str, Any]) -> dict[str, Any]:
    """Replace ``${VAR}`` placeholders with environment values."""
    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str) and node.startswith("${") and node.endswith("}"):
            return os.environ.get(node[2:-1], "")
        return node
    return walk(cfg)


@lru_cache(maxsize=4)
def load_settings(path: Path = Path("config/settings.yaml")) -> Settings:
    raw = _resolve_env(_read_yaml(path))
    return Settings.model_validate(raw)