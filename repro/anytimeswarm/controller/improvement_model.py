"""Predict E[Delta J_search | h_tau] over the next H ms (in percent of the reward scale).

LearnedPredictor : Poisson GLM (log link) on standardised trace features, fitted OFFLINE on
                   development scenarios (experiments/03_train_improvement_model.py). Prediction is
                   one dot product + exp (~microseconds), so it is cheap enough to call every 5 ms.
OnlinePredictor  : no training; extrapolates the recent improvement rate (ablation baseline).
"""
from __future__ import annotations

import json
import math

import numpy as np

from .features import FEATURES


class LearnedPredictor:
    name = "learned"

    def __init__(self, mean=None, std=None, coef=None, intercept=0.0, horizon_ms=10.0, meta=None):
        self.mean = np.asarray(mean, float) if mean is not None else None
        self.std = np.asarray(std, float) if std is not None else None
        self.coef = np.asarray(coef, float) if coef is not None else None
        self.intercept = float(intercept)
        self.horizon_ms = float(horizon_ms)
        self.meta = meta or {}

    def fit(self, X, y, alpha: float = 1e-3):
        from sklearn.linear_model import PoissonRegressor

        X = np.asarray(X, float)
        y = np.clip(np.asarray(y, float), 0, None)
        self.mean, self.std = X.mean(0), X.std(0) + 1e-9
        glm = PoissonRegressor(alpha=alpha, max_iter=3000).fit((X - self.mean) / self.std, y)
        self.coef, self.intercept = glm.coef_, float(glm.intercept_)
        return self

    def predict(self, f) -> float:
        z = (np.asarray(f, float) - self.mean) / self.std
        return float(math.exp(min(float(z @ self.coef) + self.intercept, 20.0)))

    def predict_many(self, X) -> np.ndarray:
        z = (np.asarray(X, float) - self.mean) / self.std
        return np.exp(np.minimum(z @ self.coef + self.intercept, 20.0))

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"features": FEATURES, "mean": self.mean.tolist(), "std": self.std.tolist(),
                       "coef": self.coef.tolist(), "intercept": self.intercept,
                       "horizon_ms": self.horizon_ms, "meta": self.meta}, f, indent=2)

    @classmethod
    def load(cls, path) -> "LearnedPredictor":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d["features"] != FEATURES:
            raise ValueError("feature list changed since the predictor was trained - retrain it")
        return cls(d["mean"], d["std"], d["coef"], d["intercept"], d["horizon_ms"], d.get("meta"))


class OnlinePredictor:
    """Recent improvement rate x horizon (no learning)."""
    name = "online"

    def __init__(self, horizon_ms=10.0):
        self.horizon_ms = float(horizon_ms)

    def predict(self, f) -> float:
        i20, ihalf, ie = FEATURES.index("gain_20ms"), FEATURES.index("gain_half"), FEATURES.index("log_elapsed")
        t = math.expm1(f[ie])
        rate = max(f[i20] / 20.0, f[ihalf] / max(t / 2.0, 1.0), 0.0)
        return rate * self.horizon_ms
