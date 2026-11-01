"""Study 7: a late cost that does not scale with the task reward, and execution errors outside the calibrated model.

7a, the late cost. Study 5 derived the cost-aware fallback for a late cost proportional to the task reward,
c_j = lam w_j, which gives one break-even probability lam / (1 + lam) for every task, but scored the runs with a fixed
cost per late task, u_lam = U - lam n_late / n, that is c_j = lam w_bar. Rewards differ between tasks (1, 2, 3 or 5),
so the rule was derived for another cost than the one it was scored with. For a general late cost c_j, attempting task
j with probability p of meeting the deadline has the expected value p w_j - (1 - p) c_j, which is non-negative exactly
when
    p >= theta_j = c_j / (w_j + c_j),
so every task has its own break-even safety factor z_j = Phi^-1(theta_j) and its own effective deadline d~_j(z_j), still
in closed form. Two late-cost models are run:
    cost = "prop"  c_j = lam w_j      theta_j = lam / (1 + lam)                (study 5, journal_core/study5.py)
    cost = "fee"   c_j = lam w_bar    theta_j = lam w_bar / (w_j + lam w_bar)  (w_bar = mean reward of the generator)
and each is scored with its own metric (experiments/analyze_study7.py):
    u_fee  = U - lam n_late / n                        (the study 5 score)
    u_prop = (R_on_time - lam R_late) / R_total.
With equal rewards both rules and both scores coincide.

7b, execution errors outside the model. The affine Gaussian error model and every tuned parameter stay those of the
calibrated "high" level, but the executor draws errors with a different structure (ShiftedExecutionModel):
    t3       heavy tails: speed and service errors Student-t with 3 degrees of freedom, same standard deviation
    outlier  rare long delays: with probability out_p a leg gets an extra delay ~ Exp(out_mean_s) (detour, holding)
    uavbias  correlated errors: one persistent speed bias per UAV and mission on top of the per-leg errors
and HeavyLatencyModel replaces the lognormal plan-dissemination delay by a Pareto delay with the same median.

The frozen modules of studies 2-6 are not modified; this module wraps them.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import numpy as np
from scipy.special import ndtri

from .execution import ExecutionModel, LatencyModel, _rng
from .risk import ErrorModel
from .study2 import solve2
from .study3 import fallback_problem
from .study5 import MIN_DENOM, cost_fallback_problem
from .study6 import solve6


# Competitors tuned on the development seeds (experiments/analyze_dev7.py, docs/16_PROTOCOL_V7.md section 4): per score
# ("fee": u_lam, "w": u^w_lam), late cost lam, family and disturbance level, the member with the best mean score.
TUNED7 = {"fee": {0.5: {"Prop": {"mid": "prop=0.45;fb=nominal", "high": "prop=0.75;fb=nominal"},
                         "CCnf": {"mid": "z=1", "high": "z=0"}},
                   1.0: {"Prop": {"mid": "prop=0.3;fb=none", "high": "prop=0.45;fb=none"},
                         "CCnf": {"mid": "z=1", "high": "z=0.5"}},
                   2.0: {"Prop": {"mid": "prop=0.45;fb=none", "high": "prop=0.75;fb=none"},
                         "CCnf": {"mid": "z=1", "high": "z=0.5"}}},
          "w": {0.5: {"Prop": {"mid": "prop=0.45;fb=nominal", "high": "prop=0.75;fb=nominal"},
                      "CCnf": {"mid": "z=1", "high": "z=0"}},
                1.0: {"Prop": {"mid": "prop=0.3;fb=none", "high": "prop=0.6;fb=none"},
                      "CCnf": {"mid": "z=1", "high": "z=0.5"}},
                2.0: {"Prop": {"mid": "prop=0.45;fb=none", "high": "prop=0.75;fb=none"},
                      "CCnf": {"mid": "z=1", "high": "z=0.5"}}}}


# ---------------------------------------------------------------------------------------------- 7a: late cost
def break_even(w, lam: float, cost: str, w_bar: float) -> np.ndarray:
    """Break-even probability theta_j of every task for late cost lam under the cost model ('prop' or 'fee')."""
    w = np.asarray(w, float)
    if cost == "prop":
        return np.full(w.shape, lam / (1.0 + lam))
    if cost == "fee":
        c = lam * w_bar
        return c / (w + c)
    raise ValueError(cost)


def _dtilde(P, err: ErrorModel, z: np.ndarray) -> np.ndarray:
    """min(d, d~(z_j)) per task; the nominal deadline where 1 + b1 + z_j s1 < MIN_DENOM or z_j = -inf."""
    d = np.asarray(P.dl, float)
    den = 1.0 + err.b1 + z * err.s1
    ok = np.isfinite(z) & (den >= MIN_DENOM)
    zz = np.where(ok, z, 0.0)
    new = P.t0 + (d - P.t0 - err.b0 - zz * err.s0) / np.where(ok, den, 1.0)
    return np.where(ok, np.minimum(d, new), d)


def _hopeless(Q) -> set:
    return {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}


def cost_fallback_problem7(P, err: ErrorModel, z: float, lam: float, cost: str = "prop", w_bar: float = 1.0):
    """Cost-aware fallback with a break-even safety factor per task (module docstring). cost='prop' is study 5."""
    if cost == "prop":
        return cost_fallback_problem(P, err, z, lam)
    if lam <= 0.0:
        return fallback_problem(P, err, z, "nominal")
    zl = ndtri(break_even(P.w, lam, cost, w_bar))
    zp = np.maximum(z, zl)
    Q = copy.copy(P)
    Q.dl = [float(v) for v in _dtilde(P, err, zp)]
    Q.hopeless = _hopeless(Q)
    lost = Q.hopeless - _hopeless(P)
    fb = [j for j in lost if zl[j] < z]
    if fb:
        dfb = _dtilde(P, err, zl)
        dl = list(Q.dl)
        for j in fb:
            dl[j] = float(max(dl[j], dfb[j]))
        Q.dl = dl
        Q.hopeless = _hopeless(Q)
    Q.n_fallback = len(lost) - len(Q.hopeless & lost)
    return Q


def solve7(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True,
           lam: float | None = None, cost: str = "prop", w_bar: float = 1.0, **kw6) -> dict:
    """solve6 with the late-cost model of the cost-aware fallback of the proposed model (cost, w_bar); every other
    method (cost='prop', moment propagation, CBBA, buffers) is passed to study6.solve6 unchanged."""
    if lam is None or cost == "prop" or base == "cbba" or kw6.get("mp") is not None:
        if cost != "prop" and lam is not None:
            raise ValueError("cost='fee' is implemented for the proposed model only")
        return solve6(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, z,
                      ms_per_task, buf_s, check, lam=lam, **kw6)
    err = err or ErrorModel()
    Q = cost_fallback_problem7(P, err, z, lam, cost, w_bar)
    spread = ErrorModel(err.name, 0.0, 0.0, err.s0, err.s1, err.n)   # Q contains the mean error, as in solve5
    out = solve2(base, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, spread, latency_mean_s, None,
                 ms_per_task, None, check)
    out["J"] = out["solution"].objective(P)
    out["n_fallback"] = Q.n_fallback
    return out


# ---------------------------------------------------------------------------------------------- 7b: shifted errors
@dataclass
class ShiftedExecutionModel(ExecutionModel):
    """ExecutionModel with a different error structure (module docstring). shift='gauss' reproduces the parent
    draw for draw. New draws use stream ids 11 and 12, so the parent streams (1, 2, 7) are unchanged."""
    shift: str = "gauss"
    out_p: float = 0.10
    out_mean_s: float = 90.0
    bias_sd: float = 0.08

    def _eps(self, uav_id: int, task_id: int) -> float:
        if not self.speed_cv:
            eps, lim = 0.0, 0.3
        elif self.shift == "t3":
            r = _rng(self.mission_seed, self.seed, 1, uav_id, task_id)
            eps, lim = self.speed_cv / math.sqrt(3.0) * float(r.standard_t(3)), 0.6
        else:
            eps = float(_rng(self.mission_seed, self.seed, 1, uav_id, task_id).normal(0.0, self.speed_cv))
            lim = 0.3
        eps = float(np.clip(eps, -lim, lim))
        if self.shift == "uavbias":
            b = float(np.clip(_rng(self.mission_seed, self.seed, 11, uav_id).normal(0.0, self.bias_sd), -0.2, 0.2))
            eps = float(np.clip(eps + b, -0.45, 0.45))
        return eps

    def _ground(self, dx: float, dy: float, v: float) -> float:
        L = math.hypot(dx, dy)
        wx, wy = getattr(self, "_wind", (0.0, 0.0))
        ux, uy = dx / L, dy / L
        w_par = wx * ux + wy * uy
        w_perp = abs(wx * uy - wy * ux)
        vg = math.sqrt(max(v * v - w_perp * w_perp, (0.2 * v) ** 2)) + w_par
        return max(vg, 0.2 * v)

    def leg(self, uav_id: int, task_id: int, dx: float, dy: float, airspeed: float) -> tuple[float, float]:
        L = math.hypot(dx, dy)
        if L == 0.0:
            return 0.0, 0.0
        v = airspeed * (1.0 + self._eps(uav_id, task_id))
        vg = self._ground(dx, dy, v)
        a = self.accel_mps2
        if math.isinf(a):
            t = L / vg
        elif L >= vg * vg / a:
            t = L / vg + vg / a
        else:
            t = 2.0 * math.sqrt(L / a)
        if self.shift == "outlier":
            r = _rng(self.mission_seed, self.seed, 12, uav_id, task_id)
            if r.random() < self.out_p:
                t += float(r.exponential(self.out_mean_s))
        return t, v * t

    def ground_speed(self, uav_id: int, task_id: int, dx: float, dy: float, airspeed: float) -> float:
        if math.hypot(dx, dy) == 0.0:
            return airspeed
        return self._ground(dx, dy, airspeed * (1.0 + self._eps(uav_id, task_id)))

    def service(self, task_id: int, nominal_s: float) -> float:
        if self.shift != "t3" or not self.service_cv:
            return super().service(task_id, nominal_s)
        r = _rng(self.mission_seed, self.seed, 2, task_id)
        eps = self.service_cv / math.sqrt(3.0) * float(r.standard_t(3))
        return nominal_s * float(np.clip(1.0 + eps, 0.3, 3.0))


@dataclass
class HeavyLatencyModel(LatencyModel):
    """Pareto base delay with the median of the lognormal one (tail index alpha, capped at cap_s), same re-sends."""
    alpha: float = 1.5
    cap_s: float = 300.0

    def sample(self, mission_seed: int, event_index: int) -> float:
        r = _rng(mission_seed, self.seed, 3, event_index)
        xm = self.median_s / 2.0 ** (1.0 / self.alpha)
        d = min(xm * (1.0 - r.random()) ** (-1.0 / self.alpha), self.cap_s)
        losses = 0
        while losses < 5 and r.random() < self.drop_p:
            losses += 1
        return d + losses * self.timeout_s


def shifted_levels(exec_levels: dict, lat_levels: dict) -> tuple[dict, dict]:
    """Execution and latency levels of study 7b, all built on the calibrated 'high' level (name -> model)."""
    from dataclasses import asdict
    h = asdict(exec_levels["high"])
    for k in ("name", "mission_seed"):
        h.pop(k)
    ex = {f"high_{s}": ShiftedExecutionModel(f"high_{s}", **h, shift=s) for s in ("gauss", "t3", "outlier", "uavbias")}
    lh = asdict(lat_levels["high"])
    lh.pop("name")
    lat = {"high_pareto": HeavyLatencyModel("high_pareto", **lh)}
    return ex, lat


def reward_columns(ex) -> dict:
    """Total, on-time and late reward of a finished mission (for the u_prop score of study 7a)."""
    tot = sum(t.reward for t in ex.sc.tasks)
    return {"reward_total": tot, "reward_on_time": sum(ex.tasks[j].reward for j in ex.served),
            "reward_late": sum(ex.tasks[j].reward for j in ex.late)}


def brier_columns(ex, err: ErrorModel) -> dict:
    """Brier score sum and count of the predicted probability of meeting the deadline (same tasks as b4 coverage)."""
    from scipy.special import ndtr
    s, n = 0.0, 0
    for (_u, j, _d, _s, fin) in ex.executed:
        if j not in ex.plan_lead:
            continue
        t_pub, f = ex.plan_lead[j]
        h = f - t_pub
        d = ex.tasks[j].deadline
        sd = float(err.sd(h))
        p = float(ndtr((d - f - err.mean(h)) / sd)) if sd > 0 else float(d - f - err.mean(h) >= 0)
        s += (p - float(fin <= d + 1e-9)) ** 2
        n += 1
    return {"brier_sum": s, "brier_n": n}
