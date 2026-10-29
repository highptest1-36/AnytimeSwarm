"""Study 3: chance-constrained planning with a nominal fallback (exploratory extension of study 2).

Study 2 showed that the chance-constrained model (study2.buffered_problem) is too cautious when the time windows are
short compared with the predicted finish-time error: a task whose effective deadline cannot be met even by a direct
flight becomes hopeless and is never attempted, although the vehicle may have nothing better to do. The fallback keeps
such tasks with a less cautious deadline:

    d_j' = d~_j            if task j can still meet d~_j on some route (protected task),
    d_j' = d_fb,j          otherwise (fallback task), with d_fb,j = d_j (nominal) or d_j - buffer.

All constraints of the protected tasks are unchanged, so a fallback task is only inserted into the slack that the
protected tasks leave. study2.py is frozen (results/frozen_study2_sha256.txt) and is not modified; this module wraps it.
"""
from __future__ import annotations

import numpy as np

from .risk import ErrorModel
from .study2 import buffered_problem, solve2


def fallback_problem(P, err: ErrorModel, z: float, fb: str = "nominal"):
    """Chance-constrained copy of P in which tasks that are hopeless under the effective deadline, but not under the
    nominal one, keep the fallback deadline. fb: 'nominal' or a constant buffer in seconds, e.g. '60'."""
    Q = buffered_problem(P, err, z)
    base_hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    lost = Q.hopeless - base_hopeless
    if lost:
        d = np.asarray(P.dl, float)
        dfb = d if fb == "nominal" else d - float(fb)
        dl = list(Q.dl)
        for j in lost:
            dl[j] = float(max(dl[j], dfb[j]))
        Q.dl = dl
        Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
    Q.n_fallback = len(lost) - len(Q.hopeless & lost)
    return Q


def solve3(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True,
           fb: str | None = None) -> dict:
    """solve2 with the fallback planning model when fb is given; identical to solve2 otherwise."""
    if fb is None or z is None or buf_s is not None:
        return solve2(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, z,
                      ms_per_task, buf_s, check)
    err = err or ErrorModel()
    Q = fallback_problem(P, err, z, fb)
    # Q already contains the mean error: as in solve2, the delay cost then prices the spread only
    spread = ErrorModel(err.name, 0.0, 0.0, err.s0, err.s1, err.n)
    out = solve2(base, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, spread, latency_mean_s, None,
                 ms_per_task, None, check)
    out["J"] = out["solution"].objective(P)
    out["n_fallback"] = Q.n_fallback
    return out
