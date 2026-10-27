"""Risk-aware delay cost for the AnytimeSwarm stopping rule (execution-aware extension).

Conference rule:  stop when  E[gain over H]  <=  C_delay(tau, H) + mu * scale * H, with the deterministic
    C_delay(tau, H) = sum_j v_j * ( 1[s(tau+H) > tol_j] - 1[s(tau) > tol_j] ),   s(tau) = shift of the route start.

Under execution uncertainty the finish time of task j is  F_j = f_j + s + e_j  with an error e_j whose mean and
spread grow with the lead time h_j = f_j - t0 (planned finish minus planning time). Task j is lost iff
s + e_j > tol_j, hence
    C_risk(tau, H) = sum_j v_j * ( P[e_j > tol_j - s(tau+H)] - P[e_j > tol_j - s(tau)] ),
    e_j ~ Normal( m(h_j), sd(h_j)^2 ),  m(h) = b0 + b1 h,  sd(h) = s0 + s1 h
(the spread grows about linearly with the lead time on the development data; see b2_calibrate_errors.py).
The shift also contains the expected plan-dissemination latency L:  s(tau) = max(0, t0 + kappa tau + L - ready_k).
With b = c = 0 and L = 0 the step function of the conference rule is recovered exactly.
The error model is fitted on DEVELOPMENT missions only (experiments/b2_calibrate_errors.py).
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.special import ndtr

from . import ORIGINAL  # noqa: F401
from anytimeswarm.controller.delay_cost import DelayModel
from anytimeswarm.controller.stopping import Adaptive


@dataclass
class ErrorModel:
    name: str = "zero"
    b0: float = 0.0
    b1: float = 0.0
    s0: float = 0.0
    s1: float = 0.0
    n: int = 0

    def mean(self, h):
        return self.b0 + self.b1 * h

    def sd(self, h):
        return np.maximum(self.s0 + self.s1 * np.asarray(h, float), 0.0)

    @classmethod
    def fit(cls, name: str, h, e) -> "ErrorModel":
        """Least squares for the mean; the spread from the absolute residuals, E|r| = sd * sqrt(2/pi) under a
        normal law (less sensitive to the heavy tail than squared residuals)."""
        h, e = np.asarray(h, float), np.asarray(e, float)
        A = np.c_[np.ones_like(h), h]
        b = np.linalg.lstsq(A, e, rcond=None)[0]
        r = np.abs(e - A @ b) * np.sqrt(np.pi / 2.0)
        c = np.linalg.lstsq(A, r, rcond=None)[0]
        if c[1] < 0:                                   # spread must not decrease with the lead time
            c = np.array([r.mean(), 0.0])
        return cls(name, float(b[0]), float(b[1]), float(max(c[0], 0.0)), float(c[1]), int(h.size))

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load_all(cls, path) -> dict:
        return {k: cls(**v) for k, v in json.loads(Path(path).read_text()).items() if isinstance(v, dict)}


class RiskDelayModel(DelayModel):
    def __init__(self, P, kappa: float, err: ErrorModel, latency_mean_s: float = 0.0):
        super().__init__(P, kappa)
        self.err, self.L = err, float(latency_mean_s)

    def _prepare(self, sol):
        key = tuple(tuple(r) for r in sol.routes)
        if key == self._key:
            return
        super()._prepare(sol)
        P = self.P
        lead = []
        for k, r in enumerate(sol.routes):
            if not r:
                continue
            entries, _, _, _ = P.schedule(k, r)
            lead += [fin - P.t0 for (_j, _d, _a, _s, fin) in entries]
        lead = np.asarray(lead, float)
        self.mu_e = self.err.mean(lead)
        self.sd_e = self.err.sd(lead)

    def lost_value(self, sol, tau_ms: float) -> float:
        self._prepare(sol)
        if self.tol.size == 0:
            return 0.0
        shift = np.maximum(0.0, self.P.t0 + self.kappa * tau_ms / 1000.0 + self.L - self.ready)
        margin = self.tol - shift - self.mu_e
        with np.errstate(divide="ignore", invalid="ignore"):
            p = np.where(self.sd_e > 0, ndtr(-margin / np.where(self.sd_e > 0, self.sd_e, 1.0)),
                         (margin < 0).astype(float))
        return float(self.val @ p)


class RiskAdaptive(Adaptive):
    name = "risk_adaptive"

    def __init__(self, *args, err: ErrorModel | None = None, latency_mean_s: float = 0.0, **kw):
        super().__init__(*args, **kw)
        self.err, self.L = err or ErrorModel(), latency_mean_s

    def start(self, P, J0, budget_ms, trace):
        super().start(P, J0, budget_ms, trace)
        self.delay = RiskDelayModel(P, self.kappa, self.err, self.L)


def expected_latency(lat) -> float:
    """Mean of a LatencyModel (lognormal base + geometric re-sends, at most 5)."""
    base = lat.median_s * math.exp(lat.sigma ** 2 / 2.0) if lat.median_s > 0 else 0.0
    p, q = lat.drop_p, 0.0
    for k in range(1, 6):
        q += (p ** k)                                  # P(at least k losses) = p^k
    return base + q * lat.timeout_s
