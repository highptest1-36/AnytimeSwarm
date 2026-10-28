"""Study 2 of the journal: literature baselines, the proposed execution-aware replanner and the regime sweep.

Method grammar (experiments/b2_grid.py):  <base>[@budget_ms][~key=value,...][+trigger]

| base            | stopping rule                                                                   | source                |
|-----------------|---------------------------------------------------------------------------------|-----------------------|
| regret_repair   | none (feasibility-first repair, regret-2)                                       | constructive floor    |
| alns_fixed      | fixed budget (default 250 ms, @B for another budget)                            | Ropke & Pisinger 2006 |
| alns_scaled     | fixed budget proportional to the number of open tasks, ~ms=<ms per task>       | size-aware budget     |
| alns_stagnation | no improvement for 20% of the budget                                            | classic early stop    |
| profile         | static performance profile (dev) vs. delay + compute cost                       | Zilberstein 1996      |
| online_curve    | quality curve a - b exp(-c t) fitted online vs. delay + compute cost            | Svegliato et al. 2018 |
| anytime         | learned predictor vs. deterministic delay + compute cost (conference)           | AnytimeSwarm          |
| anytime_risk    | learned predictor vs. risk-aware delay cost (study 1)                           | AnytimeSwarm-R        |
| proposed        | anytime_risk on a chance-constrained planning model (~z=..), own trigger        | this study            |

Options: ~z=<z> plans for finish f_j + m(h_j) + z s(h_j) <= d_j with h_j = f_j - t0 (bias-corrected and
chance-constrained planning, see buffered_problem; any base accepts it); ~buf=<s> plans with a constant time buffer
of <s> seconds instead (robust-buffer baseline). The executor still uses the true deadlines. All ALNS variants share operators, parameters and seed, so they
follow the same search trajectory and differ only in when they stop (and, with ~z, in the deadlines they plan for).
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np

from . import ORIGINAL  # noqa: F401
from anytimeswarm.algorithms.alns import run_alns
from anytimeswarm.algorithms.methods import make_controller
from anytimeswarm.algorithms.repair import feasibility_first_repair
from anytimeswarm.controller.improvement_model import OnlinePredictor
from anytimeswarm.controller.stopping import Adaptive
from anytimeswarm.simulator.problem import validate
from anytimeswarm.utils import now_ms

from .risk import ErrorModel, RiskAdaptive

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILE = ROOT / "models" / "performance_profile_dev.json"
# safety factor of the proposed planning model per calibrated disturbance level, selected on development missions
# (results/tier_b/dev2b_explore.csv: mid -> 0.5, high -> 0); "low" was not explored and follows "mid"
Z_BY_LEVEL = {"nominal": 0.0, "low": 0.5, "mid": 0.5, "high": 0.0}


# ---------------------------------------------------------------------------------------------- planning model
def buffered_problem(P, err: ErrorModel, z: float | None, const_s: float | None = None):
    """Copy of P with chance-constrained deadlines. A planned finish f must satisfy f + m(h) + z s(h) <= d with the lead
    time h = f - t0 of that very finish. Because m and s are linear in h, this is exactly f <= d~ with
        d~ = t0 + (d - t0 - b0 - z s0) / (1 + b1 + z s1),
    so the buffer adapts to how far ahead the task is served. const_s instead subtracts a constant buffer (baseline)."""
    Q = copy.copy(P)
    d = np.asarray(P.dl, float)
    if const_s is not None:
        new = d - const_s
    else:
        c = err.b1 + z * err.s1
        new = P.t0 + (d - P.t0 - err.b0 - z * err.s0) / (1.0 + c)
    Q.dl = [float(min(a, b)) for a, b in zip(d, new)]
    Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
    return Q


def tighten_windows(sc, f: float):
    """Scenario with every time window (deadline - release - service) multiplied by f, deadline changes included."""
    if f == 1.0:
        return sc
    sc = copy.deepcopy(sc)
    by_id = {t.id: t for t in sc.tasks}
    for t in sc.tasks:
        t.deadline = t.release + t.service + f * (t.deadline - t.release - t.service)
    for e in sc.events:
        if e.kind == "deadline":
            t = by_id[e.data["task_id"]]
            e.data["new_deadline"] = t.release + t.service + f * max(e.data["new_deadline"] - t.release - t.service,
                                                                     0.0)
    sc.name = f"{sc.name}-w{f:g}"
    return sc


# ---------------------------------------------------------------------------------------------- stopping rules
class OnlineCurveStop(Adaptive):
    """Meta-level control with online performance prediction in the spirit of Svegliato, Wray and Zilberstein
    (IJCAI 2018): the best objective so far is fitted online with q(t) = a - b exp(-c t) (b >= 0, c on a log grid,
    a and b by least squares), and the search stops when the predicted gain over the next H ms no longer exceeds the
    time cost. The time cost is the same delay + compute cost as AnytimeSwarm, so only the predictor differs."""
    name = "online_curve"
    RATES = np.geomspace(1e-3, 0.5, 16)              # per ms

    def check(self, st) -> str | None:
        if st.iters < 1 or st.elapsed_ms < self.next_check:
            return None
        self.next_check = st.elapsed_ms + self.check_ms
        P, H, t = self.P, self.horizon_ms, st.elapsed_ms
        imp = st.trace["imp"]
        ts = np.array([st.t_init_ms] + [x[0] for x in imp])
        qs = np.array([self.J0] + [x[2] for x in imp])
        # the curve is fitted on the step function sampled at the improvement times and at "now"
        ts, qs = np.append(ts, t), np.append(qs, qs[-1])
        if len(imp) < 2:                               # too few points for a curve: average rate so far
            gain = (qs[-1] - qs[0]) / max(t, 1.0) * H
        else:
            best = (np.inf, 0.0, 0.0)
            for c in self.RATES:
                x = np.exp(-c * ts)
                A = np.c_[np.ones_like(x), -x]
                (a, b), *_ = np.linalg.lstsq(A, qs, rcond=None)
                if b < 0:
                    continue
                sse = float(((A @ np.array([a, b]) - qs) ** 2).sum())
                if sse < best[0]:
                    best = (sse, b, c)
            _, b, c = best
            gain = b * math.exp(-c * t) * (1.0 - math.exp(-c * H))
        dcost = self.delay.cost(st.best, t, H) if self.delay else 0.0
        ccost = self.mu * P.scale * H
        self.decisions.append((t, gain, dcost, ccost))
        return "online_curve" if gain <= dcost + ccost else None

    def start(self, P, J0, budget_ms, trace):
        super().start(P, J0, budget_ms, trace)
        self.J0 = J0


class ProfileStop(Adaptive):
    """Static performance profile (Boddy and Dean; Zilberstein 1996): the expected improvement over the next H ms as a
    function of the elapsed time and the number of open tasks only, estimated offline on development planning calls
    (experiments/b2_build_profile.py). Stops when this expectation no longer exceeds the time cost."""
    name = "profile"
    _table = None

    @classmethod
    def table(cls):
        if cls._table is None:
            d = json.loads(PROFILE_FILE.read_text())
            cls._table = (np.asarray(d["t_ms"]), np.asarray(d["n_edges"]), np.asarray(d["gain_frac"]))
        return cls._table

    def check(self, st) -> str | None:
        if st.iters < 1 or st.elapsed_ms < self.next_check:
            return None
        self.next_check = st.elapsed_ms + self.check_ms
        P, H, t = self.P, self.horizon_ms, st.elapsed_ms
        tg, ne, g = self.table()
        row = min(int(np.searchsorted(ne, P.N, side="right")) - 1, g.shape[0] - 1)
        gain = float(np.interp(t, tg, g[max(row, 0)])) * P.scale
        dcost = self.delay.cost(st.best, t, H) if self.delay else 0.0
        ccost = self.mu * P.scale * H
        self.decisions.append((t, gain, dcost, ccost))
        return "profile" if gain <= dcost + ccost else None


# ---------------------------------------------------------------------------------------------- planner
def parse_method(spec: str):
    """'<base>[@B][~k=v,...][+trigger]' -> (base, budget or None, options dict, trigger or None)."""
    spec, _, trig = spec.partition("+")
    spec, _, opts = spec.partition("~")
    base, _, b = spec.partition("@")
    o = {}
    for kv in filter(None, opts.split(",")):
        k, _, v = kv.partition("=")
        o[k] = v
    return base, (float(b) if b else None), o, (trig or None)


def solve2(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True) -> dict:
    c = cfg["controller"]
    err = err or ErrorModel()
    Q = buffered_problem(P, err, z, buf_s) if (z is not None or buf_s is not None) else P
    if base == "alns_scaled":
        budget_ms = float(np.clip(ms_per_task * max(P.N, 1), 10.0, budget_ms))
    clock = now_ms
    t0 = clock()
    rng = np.random.default_rng(seed)
    sol = feasibility_first_repair(Q, old_routes)
    t_ff = clock() - t0
    res = None
    if base != "regret_repair":
        args = (predictor if predictor is not None else OnlinePredictor(c["horizon_ms"]), kappa, c["mu"],
                c["check_ms"], c["horizon_ms"], c["min_ms"])
        if base in ("anytime_risk", "proposed"):
            # the planning model already contains the mean error (and z spreads) when z is set: the delay cost then
            # only prices the remaining spread around the buffered deadlines
            e = ErrorModel(err.name, 0.0, 0.0, err.s0, err.s1, err.n) if z is not None and buf_s is None else err
            ctrl = RiskAdaptive(*args, err=e, latency_mean_s=latency_mean_s)
        elif base == "online_curve":
            ctrl = OnlineCurveStop(*args)
        elif base == "profile":
            ctrl = ProfileStop(*args)
        elif base == "alns_scaled":
            ctrl = make_controller("alns_fixed", cfg, predictor, kappa)
        else:
            ctrl = make_controller(base, cfg, predictor, kappa)
        res = run_alns(Q, sol, cfg["alns"], rng, budget_ms, ctrl, clock, t0, None, False)
        sol = res["solution"]
    out = {"method": base, "t_first_feasible_ms": t_ff, "iters": res["iters"] if res else 0,
           "stop_reason": res["stop_reason"] if res else "constructive", "elapsed_ms": clock() - t0,
           "solution": sol, "J": sol.objective(P), "n_assigned": sol.n_assigned(),
           "trace": res["trace"] if res else None, "J0": res["J0"] if res else None}
    if check:
        errs = validate(Q, sol)
        if errs:
            raise RuntimeError(f"{base} produced an infeasible plan: {errs[:3]}")
    return out
