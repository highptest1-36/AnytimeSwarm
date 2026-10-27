"""Module 2 - anytime improvement: Adaptive Large Neighbourhood Search (Ropke & Pisinger, 2006).

Anytime properties
  * the incumbent is always feasible (destroy keeps feasibility, repair only makes feasible moves);
  * the best solution is kept at all times and can be published at any interruption;
  * cooling is per ITERATION (budget independent): with the same seed every stopping policy follows
    the same search trajectory, so policies differ ONLY in when they stop.
Every planning call records a trace: per-iteration timestamps + best-solution improvements.
"""
from __future__ import annotations

import math

import numpy as np

from ..simulator.problem import Problem, Solution
from .insertion import parallel_insert


# ----------------------------------------------------------------------------- destroy operators
def _assigned(sol: Solution):
    return [(j, k) for k, r in enumerate(sol.routes) for j in r]


def _remove(P: Problem, sol: Solution, tasks) -> None:
    tasks = set(tasks)
    for k, r in enumerate(sol.routes):
        if tasks.intersection(r):
            sol.routes[k] = [j for j in r if j not in tasks]
            sol.dist[k] = P.route_eval(k, sol.routes[k])[1]
    sol.unassigned |= tasks


def random_removal(P, sol, q, rng):
    a = _assigned(sol)
    pick = rng.choice(len(a), size=min(q, len(a)), replace=False)
    _remove(P, sol, [a[i][0] for i in pick])


def worst_removal(P, sol, q, rng, p: float = 3.0):
    contrib = []
    for k, r in enumerate(sol.routes):
        for i, j in enumerate(r):
            d_wo = P.route_eval(k, r[:i] + r[i + 1:])[1]
            contrib.append((P.task_value(j, k) - P.gamma * (sol.dist[k] - d_wo), j))
    contrib.sort()
    chosen = []
    while contrib and len(chosen) < q:
        idx = int(len(contrib) * rng.random() ** p)
        chosen.append(contrib.pop(idx)[1])
    _remove(P, sol, chosen)


def related_removal(P, sol, q, rng):
    a = [j for j, _ in _assigned(sol)]
    seed = a[rng.integers(len(a))]
    span = max(P.dl) - min(P.rel) + 1.0
    diag = float(P.Dn[: P.N, : P.N].max()) + 1.0
    rel = sorted(a, key=lambda j: P.D[seed][j] / diag + abs(P.dl[j] - P.dl[seed]) / span)
    _remove(P, sol, rel[:q])


def route_removal(P, sol, q, rng):
    ks = [k for k, r in enumerate(sol.routes) if r]
    k = ks[rng.integers(len(ks))]
    r = sol.routes[k]
    if len(r) <= q:
        _remove(P, sol, r[:])
    else:
        s = int(rng.integers(len(r) - q + 1))
        _remove(P, sol, r[s:s + q])


DESTROY = [random_removal, worst_removal, related_removal, route_removal]
REPAIR = [(1, 0.0), (1, 1.0), (2, 0.0), (2, 1.0)]  # (regret, noise on/off)


class SearchState:
    __slots__ = ("elapsed_ms", "iters", "best", "best_J", "trace", "t_init_ms")


# ----------------------------------------------------------------------------- engine
def run_alns(P: Problem, sol0: Solution, cfg: dict, rng: np.random.Generator, budget_ms: float,
             controller, clock, t_start: float, max_iters: int | None = None,
             record_solutions: bool = False) -> dict:
    """budget_ms is a hard deadline for the WHOLE planning call measured from t_start
    (feasibility-first repair time included)."""
    a = cfg
    J0 = sol0.objective(P)
    u0 = sum(P.w[j] for j in sol0.unassigned) / max(sum(P.w), 1e-9)
    trace = {"iter_t": [], "imp": [], "u0": u0}
    cur, Jc = sol0, J0
    best, Jb = sol0.copy(), J0
    T = -a["init_accept_worse"] * max(abs(J0), 1.0) / math.log(a["init_accept_prob"])
    wd, wr = np.ones(len(DESTROY)), np.ones(len(REPAIR))
    rho, (s1, s2, s3) = a["reaction"], a["scores"]
    st = SearchState()
    st.trace, st.best, st.best_J, st.iters = trace, best, Jb, 0
    st.t_init_ms = clock() - t_start
    controller.start(P, J0, budget_ms, trace)
    snapshots = [(st.t_init_ms, J0, [r[:] for r in best.routes])] if record_solutions else None
    reason, it = "budget", 0
    deadline_abs = t_start + budget_ms
    while True:
        now = clock()
        st.elapsed_ms = now - t_start
        if now >= deadline_abs:
            reason = "budget"
            break
        if max_iters is not None and it >= max_iters:
            reason = "max_iters"
            break
        st.iters = it
        r = controller.check(st)
        if r:
            reason = r
            break
        n_ass = cur.n_assigned()
        cand = cur.copy()
        if n_ass:
            di = int(rng.choice(len(DESTROY), p=wd / wd.sum()))
            q = int(round(rng.uniform(*a["removal_frac"]) * n_ass))
            q = max(a["min_remove"], min(q, a["max_remove"], n_ass))
            DESTROY[di](P, cand, q, rng)
        else:
            di = -1
        ri = int(rng.choice(len(REPAIR), p=wr / wr.sum()))
        regret, noisy = REPAIR[ri]
        parallel_insert(P, cand, sorted(cand.unassigned), regret, a["noise"] * noisy, rng,
                        deadline_ms=deadline_abs, clock=clock)
        Jn = cand.objective(P)
        score = 0.0
        if Jn > Jb + 1e-9:
            best, Jb, score = cand.copy(), Jn, s1
            st.best, st.best_J = best, Jb
            t_imp = clock() - t_start
            trace["imp"].append((t_imp, it, Jb, sum(P.w[j] for j in best.unassigned) / max(sum(P.w), 1e-9)))
            if record_solutions:
                snapshots.append((t_imp, Jb, [r_[:] for r_ in best.routes]))
        elif Jn > Jc + 1e-9:
            score = s2
        elif rng.random() < math.exp(min(0.0, (Jn - Jc)) / max(T, 1e-9)):
            score = s3
        if score > 0:
            cur, Jc = cand, Jn
        if di >= 0:
            wd[di] = max((1 - rho) * wd[di] + rho * score, 0.1)
        wr[ri] = max((1 - rho) * wr[ri] + rho * score, 0.1)
        T *= a["cooling"]
        it += 1
        trace["iter_t"].append(clock() - t_start)
    return {"solution": best, "J": Jb, "J0": J0, "iters": it, "stop_reason": reason, "trace": trace,
            "snapshots": snapshots, "decisions": getattr(controller, "decisions", None)}
