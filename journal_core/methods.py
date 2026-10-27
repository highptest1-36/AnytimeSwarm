"""Planner registry of the journal: the conference methods unchanged, plus the execution-aware stopping rule.

| method            | stopping rule                                                                 |
|-------------------|-------------------------------------------------------------------------------|
| (conference)      | anytimeswarm.algorithms.methods.solve, untouched                              |
| anytime_risk      | AnytimeSwarm with the risk-aware delay cost (error model + expected latency)  |

All ALNS variants share the operators, parameters and RNG seed, so they follow the same search trajectory and
differ only in when they stop (same property as in the conference version).
"""
from __future__ import annotations

import numpy as np

from . import ORIGINAL  # noqa: F401
from anytimeswarm.algorithms.alns import run_alns
from anytimeswarm.algorithms.methods import LABELS as _LABELS
from anytimeswarm.algorithms.methods import solve as solve_conference
from anytimeswarm.algorithms.repair import feasibility_first_repair
from anytimeswarm.controller.improvement_model import OnlinePredictor
from anytimeswarm.simulator.problem import validate
from anytimeswarm.utils import now_ms

from .risk import ErrorModel, RiskAdaptive

LABELS = dict(_LABELS) | {"anytime_risk": "AnytimeSwarm-R (risk-aware)", "alns_fixed@40": "ALNS (fixed 40 ms)"}
JOURNAL_METHODS = {"anytime_risk"}


def solve(method: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
          kappa: float | None = None, err: ErrorModel | None = None, latency_mean_s: float = 0.0,
          max_iters: int | None = None, check: bool = True) -> dict:
    if method not in JOURNAL_METHODS:
        return solve_conference(method, P, old_routes, budget_ms, cfg, seed=seed, predictor=predictor, kappa=kappa,
                                max_iters=max_iters, check=check)
    c = cfg["controller"]
    kappa = c["kappa"] if kappa is None else kappa
    clock = now_ms
    t0 = clock()
    rng = np.random.default_rng(seed)
    sol = feasibility_first_repair(P, old_routes)
    t_ff = clock() - t0
    pred = predictor if predictor is not None else OnlinePredictor(c["horizon_ms"])   # as conference make_controller
    ctrl = RiskAdaptive(pred, kappa, c["mu"], c["check_ms"], c["horizon_ms"], c["min_ms"],
                        err=err, latency_mean_s=latency_mean_s)
    res = run_alns(P, sol, cfg["alns"], rng, budget_ms, ctrl, clock, t0, max_iters, False)
    sol = res["solution"]
    out = {"method": method, "t_first_feasible_ms": t_ff, "iters": res["iters"], "stop_reason": res["stop_reason"],
           "trace": res["trace"], "decisions": res["decisions"], "snapshots": None, "J_initial": res["J0"],
           "elapsed_ms": clock() - t0, "solution": sol, "J": sol.objective(P), "n_assigned": sol.n_assigned(),
           "unassigned_reward": sum(P.w[j] for j in sol.unassigned)}
    if check:
        errs = validate(P, sol)
        if errs:
            raise RuntimeError(f"{method} produced an infeasible plan: {errs[:3]}")
    return out
