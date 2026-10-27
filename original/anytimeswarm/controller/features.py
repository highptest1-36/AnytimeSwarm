"""Features h_tau of the anytime search history (used by the improvement predictor).

A search trace is: per-iteration timestamps `iter_t` (ms since the planning call started) and the
list of best-solution improvements `imp` = [(t_ms, iteration, J_best, unassigned_reward_frac)].
All gains are expressed in PERCENT of the reward scale (sum of alpha * w_j of open tasks) so that
instances of different size share one model.
"""
from __future__ import annotations

import math
from bisect import bisect_right

FEATURES = ["log_elapsed", "log_iters", "gain_5ms", "gain_20ms", "gain_half", "log_since_impr",
            "total_gain", "unassigned_frac", "log_n_tasks", "log_n_uav", "iters_per_ms"]


class TraceView:
    """Step-function view of a (possibly still growing) trace."""

    def __init__(self, iter_t, imp, J0: float, scale: float, unassigned0: float):
        self.iter_t, self.imp, self.J0, self.scale, self.u0 = iter_t, imp, J0, max(scale, 1e-9), unassigned0
        self._imp_t = [r[0] for r in imp]

    def refresh(self):
        if len(self._imp_t) != len(self.imp):
            self._imp_t = [r[0] for r in self.imp]

    def J_at(self, t: float) -> float:
        i = bisect_right(self._imp_t, t)
        return self.imp[i - 1][2] if i else self.J0

    def unassigned_at(self, t: float) -> float:
        i = bisect_right(self._imp_t, t)
        return self.imp[i - 1][3] if i else self.u0

    def last_impr(self, t: float) -> float:
        i = bisect_right(self._imp_t, t)
        return self.imp[i - 1][0] if i else 0.0

    def iters_at(self, t: float) -> int:
        return bisect_right(self.iter_t, t)


def features_at(view: TraceView, t: float, n_tasks: int, n_uav: int) -> list[float]:
    s = 100.0 / view.scale
    Jt = view.J_at(t)
    it = view.iters_at(t)
    return [
        math.log1p(t),
        math.log1p(it),
        (Jt - view.J_at(t - 5.0)) * s,
        (Jt - view.J_at(t - 20.0)) * s,
        (Jt - view.J_at(t / 2.0)) * s,
        math.log1p(max(t - view.last_impr(t), 0.0)),
        (Jt - view.J0) * s,
        view.unassigned_at(t),
        math.log1p(n_tasks),
        math.log1p(n_uav),
        it / max(t, 1e-3),
    ]


def target_at(view: TraceView, t: float, horizon_ms: float) -> float:
    """Future improvement (percent of scale) over the next horizon."""
    return (view.J_at(t + horizon_ms) - view.J_at(t)) * 100.0 / view.scale
