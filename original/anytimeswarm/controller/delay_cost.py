"""Expected loss caused by publishing the plan later: C_delay(tau -> tau + H).

Derived from the incumbent plan itself (no hand-tuned penalty):
  * publishing at mission time t0 + kappa * tau shifts the route of every UAV that is already
    ready by  s_k(tau) = max(0, t0 + kappa * tau - ready_k)
  * waiting time absorbs shift, so task j of route k is lost iff  s_k > tol_j,
        tol_j = (d_j - finish_j) + sum_{i <= j} wait_i
  * C_delay(tau, H) = sum of values of tasks with  s_k(tau) <= tol_j < s_k(tau + H)
kappa (time dilation) converts planning milliseconds into mission milliseconds; kappa = 1 means the
laptop runs in real time. Larger kappa models slower on-board computers or communication latency.
"""
from __future__ import annotations

import numpy as np

from ..simulator.problem import Problem, Solution


class DelayModel:
    def __init__(self, P: Problem, kappa: float):
        self.P, self.kappa = P, float(kappa)
        self._key = None

    def _prepare(self, sol: Solution):
        key = tuple(tuple(r) for r in sol.routes)
        if key == self._key:
            return
        self._key = key
        P = self.P
        ready, tol, val = [], [], []
        for k, r in enumerate(sol.routes):
            if not r:
                continue
            entries, _, _, _ = P.schedule(k, r)
            W = 0.0
            for j, _dep, arr, start, fin in entries:
                W += start - arr
                ready.append(P.ready[k])
                tol.append(P.dl[j] - fin + W)
                val.append(P.task_value(j, k))
        self.ready, self.tol, self.val = (np.asarray(a, float) for a in (ready, tol, val))

    def lost_value(self, sol: Solution, tau_ms: float) -> float:
        self._prepare(sol)
        if self.tol.size == 0:
            return 0.0
        shift = np.maximum(0.0, self.P.t0 + self.kappa * tau_ms / 1000.0 - self.ready)
        return float(self.val[shift > self.tol].sum())

    def cost(self, sol: Solution, tau_ms: float, horizon_ms: float) -> float:
        return self.lost_value(sol, tau_ms + horizon_ms) - self.lost_value(sol, tau_ms)
