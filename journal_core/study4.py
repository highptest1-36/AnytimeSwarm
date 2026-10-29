"""Study 4: planning models compared on the same search, and online calibration of the error model.

Every planning model below keeps the search, the trigger and the nominal fallback of study 3 and changes only which
finish times are accepted for task j:

| option        | accepted if                                              | source                                  |
|---------------|----------------------------------------------------------|-----------------------------------------|
| (none, ~z)    | f + m(h) + z s(h) <= d,  m, s affine in h (proposed)      | study 2 / 3, effective deadline         |
| ~prop=<c>     | f + c h <= d                                             | buffer proportional to the lead time    |
| ~mp=<z>       | E[F] + z sd[F] <= d, F propagated leg by leg             | moment propagation, Ehmke et al. (2015) |
| ~online=1     | as proposed, (b0, b1, s0, s1) refitted during the mission | online calibration                      |

Moment propagation follows the chance-constrained VRPTW of Ehmke, Campbell and Urban (EJOR 2015): the flight time of
a leg of nominal duration t is normal with mean (1 + a) t + c and sd cv t, the service time is normal with mean
(1 + a_s) s and sd cv_s s, legs are independent, and the start of service max(arrival, release) is approximated by
Clark's (1961) moments of the maximum of a normal variable and a constant. The arc parameters are fitted on the legs
of the development flights (experiments/b4_error_structure.py legs). The check is done along the route inside
route_eval, so it costs a few floating-point operations per stop more than the deterministic check.

Online calibration starts from the error model fitted on the development missions of all disturbance levels together
and refits it, at every planning call, on the pairs (lead time, finish-time error) of the tasks this mission has
completed so far, the development data acting as a prior of weight n0 pairs. It needs neither the disturbance level
nor a level-specific safety factor. The executor is not modified: RegisteringExecutor only makes the running executor
visible to the planner (see b4_grid.py).

study2.py and study3.py are frozen and are not modified; this module wraps them.
"""
from __future__ import annotations

import copy
import json
import math

import numpy as np

from . import kinematic_executor as kx
from anytimeswarm.algorithms.repair import filter_route
from anytimeswarm.simulator.problem import Solution, validate
from .risk import ErrorModel
from .study2 import ROOT, solve2
from .study3 import fallback_problem, solve3

MP_FILE = ROOT / "models" / "mp_model_dev.json"
PAIRS_FILE = ROOT / "results" / "tier_b" / "dev4_errpairs.csv"
_SQ2 = math.sqrt(2.0)
_ISQ2PI = 1.0 / math.sqrt(2.0 * math.pi)

# values selected on development missions (docs/12_PROTOCOL_V4.md, results/tier_b/dev4_tune*.csv; rule: highest mean
# dev utility per disturbance level over both window factors and kappa_B 10/50/200; online: one value for both levels)
Z4_BY_LEVEL = {"mid": 1.0, "high": 0.5}           # proposed effective deadline with the fallback
PROP_BY_LEVEL = {"mid": 0.45, "high": 0.6}
ZMP_BY_LEVEL = {"mid": 1.0, "high": 0.5}
ONLINE = {"n0": 50.0, "z": 0.5}


# ---------------------------------------------------------------------------------------------- moment propagation
class MPProblem:
    """Mixin swapped into a copy of a Problem: route_eval and schedule apply the moment-propagation check.

    Tasks in `relax` (the fallback tasks) only need the nominal finish to meet the deadline."""

    def route_eval(self, k, seq):
        D, N = self.D, self.N
        prev = N + 1 + k
        if not seq:
            return True, D[prev][N]
        t, e, sp = self.ready[k], self.energy[k] - self.reserve[k], self.speed[k]
        rel, dl, sv, hv = self.rel, self.dl, self.sv, self.hover
        a1, c, cv, as1, cvs, z, relax = self._mp
        mu, var = t, 0.0
        dist = 0.0
        for j in seq:
            d = D[prev][j]
            tl = d / sp
            t += tl
            mu += a1 * tl + c
            var += (cv * tl) ** 2
            r = rel[j]
            if t < r:
                t = r
            if var > 0.0:
                sd = math.sqrt(var)
                al = (mu - r) / sd
                if al < 8.0:
                    Ph = 0.5 * (1.0 + math.erf(al / _SQ2))
                    ph = _ISQ2PI * math.exp(-0.5 * al * al)
                    m1 = mu * Ph + r * (1.0 - Ph) + sd * ph
                    m2 = (mu * mu + var) * Ph + r * r * (1.0 - Ph) + (mu + r) * sd * ph
                    mu, var = m1, max(m2 - m1 * m1, 0.0)
            elif mu < r:
                mu = r
            s = sv[j]
            t += s
            mu += as1 * s
            var += (cvs * s) ** 2
            if t > dl[j] or (j not in relax and mu + z * math.sqrt(var) > dl[j]):
                return False, 0.0
            dist += d
            e -= d + hv * s
            prev = j
        d = D[prev][N]
        if e - d < 0.0:
            return False, 0.0
        return True, dist + d

    def schedule(self, k, seq, start_time=None, skip_infeasible=False):
        """Nominal timing as Problem.schedule; a task that fails the check of route_eval is infeasible. Only the
        planner calls this method (validation, delay cost); the executor times the plan on the original problem."""
        if start_time is not None:
            return self._base_schedule(k, seq, start_time, skip_infeasible)
        skipped, kept = [], []
        for j in seq:
            if self.route_eval(k, kept + [j])[0]:
                kept.append(j)
            elif skip_infeasible:
                skipped.append(j)
            else:
                raise ValueError(f"infeasible route for uav {k} at task {j}")
        ent, sk, dist, e = self._base_schedule(k, kept, None, skip_infeasible)
        return ent, skipped + sk, dist, e


_MP_CLS = {}


def mp_problem(P, mp: dict, z: float, fb: str | None = "nominal"):
    """Copy of P whose feasibility check is moment propagation with safety factor z (and the nominal fallback)."""
    base_cls = type(P)
    if base_cls not in _MP_CLS:
        _MP_CLS[base_cls] = type("MP" + base_cls.__name__, (MPProblem, base_cls), {"_base_schedule": base_cls.schedule})
    Q = copy.copy(P)
    Q.__class__ = _MP_CLS[base_cls]
    Q._mp = (1.0 + mp["a"], mp["c"], mp["cv"], 1.0 + mp["a_s"], mp["cv_s"], float(z), frozenset())
    Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
    n_fb = 0
    if fb is not None:
        base_hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
        lost = frozenset(Q.hopeless - base_hopeless)
        if lost:
            Q._mp = Q._mp[:-1] + (lost,)
            Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
            n_fb = len(lost - Q.hopeless)
    Q.n_fallback = n_fb
    return Q


def load_mp() -> dict:
    return json.loads(MP_FILE.read_text())


# ---------------------------------------------------------------------------------------------- online calibration
class RegisteringExecutor(kx.KinematicExecutor):
    """The tier B executor, unchanged, that registers itself so that the planner can read the completed tasks."""
    current = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        RegisteringExecutor.current = self


class OnlineCalibrator:
    """Weighted refit of the error model: development pairs of all levels with total weight n0, plus the pairs of the
    tasks completed so far in this mission with weight one each."""

    def __init__(self, n0: float, pool: tuple | None = None):
        if pool is None:
            import pandas as pd
            d = pd.read_csv(PAIRS_FILE)
            pool = (d.h.to_numpy(float), d.e.to_numpy(float))
        self.h0, self.e0 = pool
        self.n0 = float(n0)
        self.prior = ErrorModel.fit("pooled", self.h0, self.e0)

    def model(self, pairs) -> ErrorModel:
        if not pairs:
            return self.prior
        h1, e1 = np.asarray(pairs, float).T
        h = np.r_[self.h0, h1]
        e = np.r_[self.e0, e1]
        w = np.r_[np.full(self.h0.size, self.n0 / self.h0.size), np.ones(h1.size)]
        A = np.c_[np.ones_like(h), h]
        sw = np.sqrt(w)
        b = np.linalg.lstsq(A * sw[:, None], e * sw, rcond=None)[0]
        r = np.abs(e - A @ b) * np.sqrt(np.pi / 2.0)
        c = np.linalg.lstsq(A * sw[:, None], r * sw, rcond=None)[0]
        if c[1] < 0:
            c = np.array([float(np.average(r, weights=w)), 0.0])
        return ErrorModel("online", float(b[0]), float(b[1]), float(max(c[0], 0.0)), float(c[1]), int(h1.size))


_CAL = {}


def online_model(n0: float) -> ErrorModel:
    if n0 not in _CAL:
        _CAL[n0] = OnlineCalibrator(n0)
    ex = RegisteringExecutor.current
    pairs = ex.calibration_pairs() if ex is not None else []
    return _CAL[n0].model(pairs)


# ---------------------------------------------------------------------------------------------- planner
def solve4(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True,
           fb: str | None = None, prop: float | None = None, mp: dict | None = None, z_mp: float | None = None,
           online_n0: float | None = None) -> dict:
    """solve3 with one of the planning models of the table above; identical to solve3 without the new options."""
    if prop is not None:
        out = solve3(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa,
                     ErrorModel("prop", 0.0, float(prop), 0.0, 0.0), latency_mean_s, 0.0, ms_per_task, None, check,
                     fb or "nominal")
    elif online_n0 is not None:
        out = solve3(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, online_model(online_n0),
                     latency_mean_s, z, ms_per_task, None, check, fb or "nominal")
    elif mp is not None:
        Q = mp_problem(P, mp, z_mp, fb)
        e = err or ErrorModel()
        spread = ErrorModel(e.name, 0.0, 0.0, e.s0, e.s1, e.n)
        out = solve2(base, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, spread, latency_mean_s, None,
                     ms_per_task, None, False)
        # Under moment propagation, removing a task can make a route infeasible: one long leg may carry more variance
        # than the two legs it replaces ((t1 + t2)^2 > t1^2 + t2^2). The search assumes that removals keep a route
        # feasible, so every route is filtered once more before publication (Problem prefix filter, as in the repair).
        sol, n_fix = out["solution"], 0
        if any(not Q.route_eval(k, r)[0] for k, r in enumerate(sol.routes)):
            routes = []
            for k, r in enumerate(sol.routes):
                f = filter_route(Q, k, r)
                n_fix += len(r) - len(f)
                routes.append(f)
            sol = Solution(Q, routes)
        if check:
            errs = validate(Q, sol)
            if errs:
                raise RuntimeError(f"{base} produced an infeasible plan: {errs[:3]}")
        out.update(solution=sol, J=sol.objective(P), n_fallback=Q.n_fallback, n_mp_fix=n_fix,
                   n_assigned=sol.n_assigned())
    else:
        out = solve3(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, z,
                     ms_per_task, buf_s, check, fb)
    return out
