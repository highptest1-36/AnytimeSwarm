"""Module 3 - stopping policies for the anytime search (the core contribution).

All policies share one interface: `start(...)` once, then `check(state)` every search iteration;
`check` returns a stop reason (str) or None. The hard compute deadline B is enforced by the search
engine itself, independent of the policy.

FixedBudget  : always uses the full budget B                              (baseline)
Stagnation   : stops after no improvement for max(min_ms, frac * B)        (classic early stop)
Adaptive     : AnytimeSwarm - stop when
                   E[Delta J_search over next H | h_tau]  <=  C_delay(tau, H) + mu * scale * H
"""
from __future__ import annotations

from .delay_cost import DelayModel
from .features import TraceView, features_at


class FixedBudget:
    name = "fixed"

    def start(self, P, J0, budget_ms, trace):
        pass

    def check(self, st) -> str | None:
        return None


class Stagnation:
    name = "stagnation"

    def __init__(self, frac: float = 0.2, min_ms: float = 5.0):
        self.frac, self.min_ms = frac, min_ms

    def start(self, P, J0, budget_ms, trace):
        self.patience = max(self.min_ms, self.frac * budget_ms)

    def check(self, st) -> str | None:
        last = st.trace["imp"][-1][0] if st.trace["imp"] else st.t_init_ms
        return "stagnation" if st.elapsed_ms - last >= self.patience else None


class Adaptive:
    name = "adaptive"

    def __init__(self, predictor, kappa: float = 1.0, mu: float = 3e-5, check_ms: float = 5.0,
                 horizon_ms: float = 10.0, min_ms: float = 2.0, use_delay: bool = True):
        self.predictor, self.kappa, self.mu = predictor, kappa, mu
        self.check_ms, self.horizon_ms, self.min_ms, self.use_delay = check_ms, horizon_ms, min_ms, use_delay

    def start(self, P, J0, budget_ms, trace):
        self.P = P
        self.view = TraceView(trace["iter_t"], trace["imp"], J0, P.scale, trace["u0"])
        self.delay = DelayModel(P, self.kappa) if self.use_delay else None
        self.next_check = self.min_ms
        self.decisions = []   # (tau, predicted gain, delay cost, compute cost) -> for analysis plots

    def check(self, st) -> str | None:
        if st.iters < 1 or st.elapsed_ms < self.next_check:
            return None
        self.next_check = st.elapsed_ms + self.check_ms
        self.view.refresh()
        P, H = self.P, self.horizon_ms
        f = features_at(self.view, st.elapsed_ms, P.N, P.M)
        gain = self.predictor.predict(f) * P.scale / 100.0
        dcost = self.delay.cost(st.best, st.elapsed_ms, H) if self.delay else 0.0
        ccost = self.mu * P.scale * H
        self.decisions.append((st.elapsed_ms, gain, dcost, ccost))
        return "adaptive" if gain <= dcost + ccost else None
