"""Method registry: every planner is called as solve(method, P, old_routes, budget_ms, ...).

| method            | initial plan        | improvement | stopping                        |
|-------------------|---------------------|-------------|---------------------------------|
| greedy_repair     | FFR, cheapest ins.  | -           | -                               |
| regret_repair     | FFR, regret-2       | -           | -                               |
| ls_fixed          | FFR, regret-2       | local search| budget or local optimum         |
| alns_fixed        | FFR, regret-2       | ALNS        | full budget B                   |
| alns_stagnation   | FFR, regret-2       | ALNS        | no improvement for 20% of B     |
| anytime           | FFR, regret-2       | ALNS        | adaptive (learned + delay cost) |  <- AnytimeSwarm
| anytime_online    | FFR, regret-2       | ALNS        | adaptive, online predictor      |  ablation
| anytime_nodelay   | FFR, regret-2       | ALNS        | adaptive, C_delay = 0           |  ablation
| anytime_noffr     | from scratch        | ALNS        | adaptive                        |  ablation
| alns_iters        | FFR, regret-2       | ALNS        | fixed #iterations (deterministic; scenario generation only)
All ALNS variants share operators, parameters and the RNG seed -> identical search trajectory.
"""
from __future__ import annotations

import numpy as np

from ..controller.improvement_model import LearnedPredictor, OnlinePredictor
from ..controller.stopping import Adaptive, FixedBudget, Stagnation
from ..simulator.problem import Problem, validate
from ..utils import now_ms
from .alns import run_alns
from .local_search import local_search
from .repair import construct_from_scratch, feasibility_first_repair

ALL_METHODS = ["greedy_repair", "regret_repair", "ls_fixed", "alns_fixed", "alns_stagnation", "anytime",
               "anytime_online", "anytime_nodelay", "anytime_noffr"]
KAPPA_DEPENDENT = {"anytime", "anytime_online", "anytime_noffr"}

LABELS = {
    "greedy_repair": "Greedy repair", "regret_repair": "Regret-2 repair", "ls_fixed": "LS (fixed B)",
    "alns_fixed": "ALNS (fixed B)", "alns_stagnation": "ALNS (stagnation stop)",
    "anytime": "AnytimeSwarm (proposed)", "anytime_online": "w/o learned predictor",
    "anytime_nodelay": "w/o delay cost", "anytime_noffr": "w/o feasibility-first repair",
    "oracle_stop": "Oracle stop", "ortools": "OR-Tools (ref.)", "alns_ref": "ALNS 3 s (ref.)",
}


def make_controller(method: str, cfg: dict, predictor=None, kappa: float | None = None):
    c = cfg["controller"]
    kappa = c["kappa"] if kappa is None else kappa
    if method in ("alns_fixed", "alns_iters", "alns_ref"):
        return FixedBudget()
    if method == "alns_stagnation":
        return Stagnation(c["stagnation_frac"], c["stagnation_min_ms"])
    if method.startswith("anytime"):
        if method == "anytime_online" or predictor is None:
            pred = OnlinePredictor(c["horizon_ms"])
        else:
            pred = predictor
        return Adaptive(pred, kappa, c["mu"], c["check_ms"], c["horizon_ms"], c["min_ms"],
                        use_delay=(method != "anytime_nodelay"))
    raise ValueError(method)


def solve(method: str, P: Problem, old_routes, budget_ms: float, cfg: dict, seed: int = 0,
          predictor: LearnedPredictor | None = None, kappa: float | None = None,
          max_iters: int | None = None, record_solutions: bool = False, check: bool = True) -> dict:
    clock = now_ms
    t0 = clock()
    rng = np.random.default_rng(seed)
    if method == "greedy_repair":
        sol = feasibility_first_repair(P, old_routes, regret=1)
    else:
        sol = construct_from_scratch(P) if method == "anytime_noffr" else feasibility_first_repair(P, old_routes)
    t_ff = clock() - t0
    out = {"method": method, "t_first_feasible_ms": t_ff, "iters": 0, "stop_reason": "constructive",
           "trace": None, "decisions": None, "snapshots": None}
    if method == "ls_fixed":
        sol, moves, reason = local_search(P, sol, t0 + budget_ms, clock)
        out.update(iters=moves, stop_reason=reason)
    elif method not in ("greedy_repair", "regret_repair"):
        ctrl = make_controller(method, cfg, predictor, kappa)
        res = run_alns(P, sol, cfg["alns"], rng, budget_ms, ctrl, clock, t0, max_iters, record_solutions)
        sol = res["solution"]
        out.update(iters=res["iters"], stop_reason=res["stop_reason"], trace=res["trace"],
                   decisions=res["decisions"], snapshots=res["snapshots"], J_initial=res["J0"])
    out["elapsed_ms"] = clock() - t0
    out["solution"] = sol
    out["J"] = sol.objective(P)
    out["n_assigned"] = sol.n_assigned()
    out["unassigned_reward"] = sum(P.w[j] for j in sol.unassigned)
    if check:
        errs = validate(P, sol)
        if errs:
            raise RuntimeError(f"{method} produced an infeasible plan: {errs[:3]}")
    return out
