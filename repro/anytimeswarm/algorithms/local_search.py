"""Baseline: first-improvement local search (insert-unassigned, relocate, swap, intra-route 2-opt)
under a fixed computation budget. It stops by itself at a local optimum."""
from __future__ import annotations

from ..simulator.problem import Problem, Solution
from .insertion import best_in_route, parallel_insert

EPS = 1e-9


def _relocate(P: Problem, sol: Solution, deadline, clock) -> bool:
    for a, ra in enumerate(sol.routes):
        for i, j in enumerate(list(ra)):
            if clock() > deadline:
                return False
            r_wo = ra[:i] + ra[i + 1:]
            d_wo = P.route_eval(a, r_wo)[1]
            removal = -P.task_value(j, a) + P.gamma * (sol.dist[a] - d_wo)
            trial = sol.copy()
            trial.routes[a], trial.dist[a] = r_wo, d_wo
            for b in range(P.M):
                o = best_in_route(P, trial, b, j)
                if o and removal + o[0] > EPS:
                    _, p, d = o
                    trial.routes[b].insert(p, j)
                    trial.dist[b] = d
                    sol.routes, sol.dist = trial.routes, trial.dist
                    return True
    return False


def _swap(P: Problem, sol: Solution, deadline, clock) -> bool:
    for a in range(P.M):
        for b in range(a + 1, P.M):
            ra, rb = sol.routes[a], sol.routes[b]
            for i, x in enumerate(ra):
                if clock() > deadline:
                    return False
                for k, y in enumerate(rb):
                    na, nb = ra[:i] + [y] + ra[i + 1:], rb[:k] + [x] + rb[k + 1:]
                    oka, da = P.route_eval(a, na)
                    if not oka:
                        continue
                    okb, db = P.route_eval(b, nb)
                    if not okb:
                        continue
                    delta = (P.task_value(y, a) + P.task_value(x, b) - P.task_value(x, a) - P.task_value(y, b)
                             - P.gamma * (da + db - sol.dist[a] - sol.dist[b]))
                    if delta > EPS:
                        sol.routes[a], sol.routes[b], sol.dist[a], sol.dist[b] = na, nb, da, db
                        return True
    return False


def _two_opt(P: Problem, sol: Solution, deadline, clock) -> bool:
    for k, r in enumerate(sol.routes):
        for i in range(len(r) - 1):
            if clock() > deadline:
                return False
            for j in range(i + 2, len(r) + 1):
                n = r[:i] + r[i:j][::-1] + r[j:]
                ok, d = P.route_eval(k, n)
                if ok and d < sol.dist[k] - 1e-6:
                    sol.routes[k], sol.dist[k] = n, d
                    return True
    return False


def local_search(P: Problem, sol: Solution, deadline_abs: float, clock) -> tuple[Solution, int, str]:
    moves = 0
    while clock() < deadline_abs:
        before = sol.objective(P)
        parallel_insert(P, sol, sorted(sol.unassigned), regret=1, deadline_ms=deadline_abs, clock=clock)
        improved = sol.objective(P) > before + EPS
        for op in (_relocate, _swap, _two_opt):
            if clock() >= deadline_abs:
                break
            if op(P, sol, deadline_abs, clock):
                improved = True
                break
        if not improved:
            return sol, moves, "local_optimum"
        moves += 1
    return sol, moves, "budget"
