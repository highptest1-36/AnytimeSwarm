"""Reference solver: OR-Tools routing (prize-collecting VRP with time windows and energy capacity).

Used ONLY to estimate a best-known objective on static snapshots (small / medium scales). Model
differences, stated in the paper: integer rounding (0.1 s, 1 m, conservative; the plan-stability
term delta is modelled as a per-vehicle arc cost) - the returned plan is re-scored with our objective and re-validated
(any task that violates a constraint after rounding is dropped). It is therefore NOT claimed optimal.
"""
from __future__ import annotations

import math

from ..simulator.problem import Problem, Solution
from .repair import filter_route


def solve_ortools(P: Problem, time_limit_s: float = 5.0) -> Solution | None:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    N, M = P.N, P.M
    if N == 0 or M == 0:
        return Solution(P, [[] for _ in range(M)])
    n_nodes = N + 1 + M
    starts = [N + 1 + k for k in range(M)]
    manager = pywrapcp.RoutingIndexManager(n_nodes, M, starts, [N] * M)
    routing = pywrapcp.RoutingModel(manager)
    D = P.D
    svc = P.sv + [0.0] * (1 + M)

    # per-vehicle arc cost = distance cost + plan-stability penalty delta when entering a task that was
    # previously assigned to ANOTHER UAV -> OR-Tools optimises exactly J (up to integer rounding)
    stab = int(round(100 * P.delta))
    for k in range(M):
        def cost_cb(i, j, k=k):
            a, b = manager.IndexToNode(i), manager.IndexToNode(j)
            pen = stab if (b < N and P.prev[b] >= 0 and P.prev[b] != k) else 0
            return int(round(100 * P.gamma * D[a][b])) + pen
        routing.SetArcCostEvaluatorOfVehicle(routing.RegisterTransitCallback(cost_cb), k)

    time_cbs = []
    for k in range(M):
        sp = P.speed[k]

        def t_cb(i, j, sp=sp):
            a, b = manager.IndexToNode(i), manager.IndexToNode(j)
            return int(math.ceil(10 * (svc[a] + D[a][b] / sp)))
        time_cbs.append(routing.RegisterTransitCallback(t_cb))
    horizon = int(10 * (max(P.dl + P.ready) + 3600))
    routing.AddDimensionWithVehicleTransits(time_cbs, horizon, horizon, False, "Time")
    tdim = routing.GetDimensionOrDie("Time")
    for j in range(N):
        lo, hi = int(math.ceil(10 * P.rel[j])), int(math.floor(10 * (P.dl[j] - P.sv[j])))
        idx = manager.NodeToIndex(j)
        if hi < lo:
            routing.AddDisjunction([idx], 0)
            continue
        tdim.CumulVar(idx).SetRange(lo, hi)
    for k in range(M):
        tdim.CumulVar(routing.Start(k)).SetValue(int(math.ceil(10 * P.ready[k])))

    def e_cb(i, j):
        a, b = manager.IndexToNode(i), manager.IndexToNode(j)
        return int(math.ceil(D[a][b] + P.hover * svc[a]))
    caps = [max(int(P.energy[k] - P.reserve[k]), 0) for k in range(M)]
    routing.AddDimensionWithVehicleCapacity(routing.RegisterTransitCallback(e_cb), 0, caps, True, "Energy")

    for j in range(N):
        lo, hi = int(math.ceil(10 * P.rel[j])), int(math.floor(10 * (P.dl[j] - P.sv[j])))
        if hi < lo:
            continue  # already optional (penalty 0) above
        # hopeless tasks (no UAV can serve them) must stay OPTIONAL, otherwise the model is infeasible
        penalty = 0 if j in P.hopeless else int(round(100 * P.alpha * P.w[j]))
        routing.AddDisjunction([manager.NodeToIndex(j)], penalty)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromMilliseconds(int(time_limit_s * 1000))
    sol = routing.SolveWithParameters(params)
    if sol is None:
        return None
    routes = []
    for k in range(M):
        idx, r = routing.Start(k), []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node < N:
                r.append(node)
            idx = sol.Value(routing.NextVar(idx))
        routes.append(filter_route(P, k, r))
    return Solution(P, routes)
