"""Study 5: a fallback that accounts for the cost of a late arrival.

The nominal fallback of study 3 keeps every task that the chance constraint gives up and plans it against its nominal
deadline. A late service earns nothing, so the fallback pays off as long as a late arrival costs nothing; the
re-scored held-out runs of studies 3, 4 and 4C (experiments/paper_latepen.py) show that it loses its advantage once a
late arrival costs about half to one and a half times the reward of a task.

Let a late arrival cost lam times the reward r of the task. Attempting a task with probability p of meeting the
deadline then has the expected value p r - (1 - p) lam r, which is non-negative exactly when
    p >= theta(lam) = lam / (1 + lam).
With the affine error model, p >= Phi(z) is the effective deadline d~(z) of study 2. The cost-aware fallback therefore
plans a given-up task against d~(z_lam), z_lam = Phi^-1(theta(lam)), instead of its nominal deadline:

    d_j' = d~_j(z_p)                     if task j can still meet it on some route (protected task),
    d_j' = min(d_j, d~_j(z_lam))         otherwise (fallback task); tasks that cannot meet this either are dropped,

with z_p = max(z, z_lam), so a protected task is never held to a lower probability than a fallback task. For lam = 0,
z_lam = -inf and the rule is the nominal fallback of study 3; as lam grows, it approaches the model without fallback.
lam is a property of the application, not a tuned parameter. A planning model without a probability of meeting the
deadline, such as a proportional buffer, has no counterpart of z_lam and needs a fallback deadline tuned per lam.

study2.py, study3.py and study4.py are frozen and are not modified; this module wraps them.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import ndtri

from .risk import ErrorModel
from .study2 import buffered_problem, solve2
from .study3 import fallback_problem

MIN_DENOM = 0.05        # 1 + b1 + z s1 below this: the effective deadline is no longer defined, use the nominal one

# Competitors tuned for each late cost on the development seeds (docs/13_PROTOCOL_V5.md section 4,
# experiments/analyze_dev5.py): per lam and disturbance level, the member of the family with the best mean u_lam.
#   Prop  proportional buffer c in {0.1, ..., 1.2}, with or without the nominal fallback (b5_grid option string)
#   CCnf  proposed model without fallback, z in {-0.5, 0, 0.5, 1, 1.5}
TUNED = {0.5: {"Prop": {"mid": "prop=0.45;fb=nominal", "high": "prop=0.75;fb=nominal"},
               "CCnf": {"mid": "z=1", "high": "z=0"}},
         1.0: {"Prop": {"mid": "prop=0.3;fb=none", "high": "prop=0.45;fb=none"},
               "CCnf": {"mid": "z=1", "high": "z=0.5"}},
         2.0: {"Prop": {"mid": "prop=0.45;fb=none", "high": "prop=0.75;fb=none"},
               "CCnf": {"mid": "z=1", "high": "z=0.5"}}}


def z_of_cost(lam: float) -> float:
    """Safety factor at which attempting a task breaks even when a late arrival costs lam task rewards."""
    if lam <= 0.0:
        return -math.inf
    return float(ndtri(lam / (1.0 + lam)))


def _deadlines(P, err: ErrorModel, z: float) -> np.ndarray:
    d = np.asarray(P.dl, float)
    if not math.isfinite(z) or 1.0 + err.b1 + z * err.s1 < MIN_DENOM:
        return d
    return np.asarray(buffered_problem(P, err, z).dl, float)


def cost_fallback_problem(P, err: ErrorModel, z: float, lam: float):
    """Chance-constrained copy of P with the cost-aware fallback (see module docstring)."""
    if lam <= 0.0:
        return fallback_problem(P, err, z, "nominal")
    z_l = z_of_cost(lam)
    Q = buffered_problem(P, err, max(z, z_l))
    base_hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    lost = Q.hopeless - base_hopeless
    if lost and z_l < z:
        dfb = _deadlines(P, err, z_l)
        dl = list(Q.dl)
        for j in lost:
            dl[j] = float(max(dl[j], dfb[j]))
        Q.dl = dl
        Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
    Q.n_fallback = len(lost) - len(Q.hopeless & lost)
    return Q


def solve5(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True,
           lam: float | None = None, prop_nofb: float | None = None, **kw4) -> dict:
    """solve4 extended by
        lam        cost-aware fallback of the proposed model with late cost lam (requires z and err),
        prop_nofb  proportional buffer f + c h <= d without any fallback (c = prop_nofb).
    Everything else is passed to study4.solve4 unchanged."""
    if lam is not None:
        err = err or ErrorModel()
        Q = cost_fallback_problem(P, err, z, lam)
        # as in study3.solve3: Q already contains the mean error, so the delay cost prices the spread only
        spread = ErrorModel(err.name, 0.0, 0.0, err.s0, err.s1, err.n)
        out = solve2(base, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, spread, latency_mean_s, None,
                     ms_per_task, None, check)
        out["J"] = out["solution"].objective(P)
        out["n_fallback"] = Q.n_fallback
        return out
    if prop_nofb is not None:
        return solve2(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa,
                      ErrorModel("prop", 0.0, float(prop_nofb), 0.0, 0.0), latency_mean_s, 0.0, ms_per_task, None,
                      check)
    from .study4 import solve4
    return solve4(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, z, ms_per_task,
                  buf_s, check, **kw4)
