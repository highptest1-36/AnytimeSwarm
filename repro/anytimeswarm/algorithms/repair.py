"""Module 1 - Feasibility-First Repair (FFR).

Given the previous plan and a new snapshot, produce a FEASIBLE incumbent within milliseconds:
  1. keep each surviving UAV's old route (tasks still open, original order);
  2. walk the route and drop every task whose inclusion breaks a deadline or the energy reserve
     (prefix filter - the result is feasible by construction);
  3. insert orphaned tasks (failed UAV, dropped tasks) + new tasks with regret-2 insertion.
Tasks that cannot be inserted profitably stay explicitly *unassigned* (reported, never hidden).
"""
from __future__ import annotations

from ..simulator.problem import Problem, Solution
from .insertion import parallel_insert


def filter_route(P: Problem, k: int, seq) -> list[int]:
    kept: list[int] = []
    for j in seq:
        ok, _ = P.route_eval(k, kept + [j])
        if ok:
            kept.append(j)
    return kept


def feasibility_first_repair(P: Problem, old_routes: list[list[int]] | None, regret: int = 2) -> Solution:
    routes = [[] for _ in range(P.M)]
    if old_routes:
        for k, r in enumerate(old_routes):
            routes[k] = filter_route(P, k, r)
    sol = Solution(P, routes)
    parallel_insert(P, sol, sorted(sol.unassigned), regret=regret)
    return sol


def construct_from_scratch(P: Problem, regret: int = 2) -> Solution:
    """Ablation "w/o FFR": ignore the previous plan and build a new one from an empty plan."""
    return feasibility_first_repair(P, None, regret)
