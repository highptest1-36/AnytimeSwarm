"""Cheapest (greedy) and regret-k parallel insertion. Used as constructive baselines, as the repair
step of feasibility-first repair, and as ALNS repair operators."""
from __future__ import annotations

import numpy as np

from ..simulator.problem import Problem, Solution

BIG = 1e9


def best_in_route(P: Problem, sol: Solution, k: int, j: int):
    """Best feasible insertion of task j into route k -> (delta_J, pos, new_dist) or None."""
    # cheap lower bound: direct flight from the UAV start must reach j in time
    if P.ready[k] + P.D[P.N + 1 + k][j] / P.speed[k] + P.sv[j] > P.dl[j]:
        return None
    r = sol.routes[k]
    base = sol.dist[k]
    gain = P.task_value(j, k)
    best = None
    for p in range(len(r) + 1):
        ok, d = P.route_eval(k, r[:p] + [j] + r[p:])
        if ok:
            dv = gain - P.gamma * (d - base)
            if best is None or dv > best[0]:
                best = (dv, p, d)
    return best


def parallel_insert(P: Problem, sol: Solution, tasks, regret: int = 1, noise: float = 0.0,
                    rng: np.random.Generator | None = None, only_positive: bool = True,
                    deadline_ms: float | None = None, clock=None) -> Solution:
    """Insert `tasks` (and leave the rest unassigned) in place.
    regret=1 -> cheapest insertion (pick the globally best delta);
    regret=k -> pick the task with the largest regret (sum of best minus k-th best route)."""
    pending = [j for j in tasks if j not in P.hopeless]
    if not pending:
        return sol
    M = P.M
    cache = {j: [best_in_route(P, sol, k, j) for k in range(M)] for j in pending}
    amp = noise * max(P.w) * P.alpha if noise > 0 else 0.0
    while pending:
        if deadline_ms is not None and clock is not None and clock() > deadline_ms:
            break
        best_j, best_key, best_opt = None, None, None
        for j in pending:
            opts = sorted((o[0], k) for k, o in enumerate(cache[j]) if o is not None)
            if not opts:
                continue
            opts.reverse()
            top = opts[0][0]
            if regret <= 1:
                key = top
            else:
                key = sum(top - opts[i][0] for i in range(1, min(regret, len(opts))))
                if len(opts) < regret:
                    key += BIG * (regret - len(opts))
                key += 1e-6 * top
            if amp:
                key += amp * (2 * rng.random() - 1)
            if best_key is None or key > best_key:
                best_j, best_key, best_opt = j, key, opts[0]
        if best_j is None:
            break
        dv, k = best_opt
        if only_positive and dv <= 0:
            pending.remove(best_j)
            continue
        _, p, d = cache[best_j][k]
        sol.routes[k].insert(p, best_j)
        sol.dist[k] = d
        sol.unassigned.discard(best_j)
        pending.remove(best_j)
        for j in pending:
            cache[j][k] = best_in_route(P, sol, k, j)
    return sol
