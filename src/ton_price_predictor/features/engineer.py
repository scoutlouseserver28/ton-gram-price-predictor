"""Feature engineering for TON/USDT candles + on-chain signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ton_price_predictor.config.loader import FeatureCfg


class FeatureEngineer:
    def __init__(self, cfg: FeatureCfg) -> None:
        self.cfg = cfg
        self._indicator_fns = {
            "ema": self._ema,
            "rsi": self._rsi,
            "macd": self._macd,
            "atr": self._atr,
            "obv": self._obv,
            "vwap_dev": self._vwap_dev,
        }

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ret_1"] = out["close"].pct_change()
        out["logret"] = np.log1p(out["ret_1"])

        for window in self.cfg.windows:
            out[f"ret_{window}"] = out["close"].pct_change(window)
            out[f"vol_{window}"] = out["logret"].rolling(window).std()
            out[f"range_{window}"] = (
                out["high"].rolling(window).max() - out["low"].rolling(window).min()
            ) / out["close"]

        for name in self.cfg.indicators:
            fn = self._indicator_fns.get(name)
            if fn is None:
                continue
            out = fn(out)

        # On-chain columns are expected to be merged upstream by the loader;
        # any missing ones are forward-filled so the model sees a dense matrix.
        for col in self.cfg.onchain:
            if col not in out.columns:
                out[col] = np.nan
            out[col] = out[col].ffill().fillna(0.0)

        return out.dropna(subset=["ret_1", "logret"])

    @staticmethod
    def _ema(df: pd.DataFrame, span: int = 24) -> pd.DataFrame:
        df[f"ema_{span}"] = df["close"].ewm(span=span, adjust=False).mean()
        return df

    @staticmethod
    def _rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        delta = df["close"].diff()
        up = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
        down = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
        rs = up / down.replace(0, np.nan)
        df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def _macd(df: pd.DataFrame) -> pd.DataFrame:
        fast = df["close"].ewm(span=12, adjust=False).mean()
        slow = df["close"].ewm(span=26, adjust=False).mean()
        macd = fast - slow
        df["macd"] = macd
        df["macd_signal"] = macd.ewm(span=9, adjust=False).mean()
        df["macd_hist"] = macd - df["macd_signal"]
        return df

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df[f"atr_{period}"] = tr.rolling(period).mean()
        return df

    @staticmethod
    def _obv(df: pd.DataFrame) -> pd.DataFrame:
        sign = np.sign(df["close"].diff()).fillna(0.0)
        df["obv"] = (sign * df["volume"]).cumsum()
        return df

    @staticmethod
    def _vwap_dev(df: pd.DataFrame, window: int = 24) -> pd.DataFrame:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (tp * df["volume"]).rolling(window).sum() / df["volume"].rolling(window).sum()
        df["vwap_dev"] = (df["close"] - vwap) / vwap
        return df