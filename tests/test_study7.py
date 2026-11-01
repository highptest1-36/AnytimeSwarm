"""Study 7: late-cost model of the cost-aware fallback, shifted execution errors."""
import math
from dataclasses import replace

import numpy as np
from scipy.special import ndtr

from journal_core import ORIGINAL
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS
from journal_core.risk import ErrorModel
from journal_core.study5 import cost_fallback_problem
from journal_core.study7 import (break_even, cost_fallback_problem7, shifted_levels, solve7)

from anytimeswarm.simulator.executor import run_mission
from anytimeswarm.simulator.problem import validate
from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
HIGH = ErrorModel("high", 20.79, 0.292, 0.0, 0.639)
WBAR = 2.1


def _problem(scale="medium", profile="arrivals", seed=1, shrink=0.5):
    snaps = []
    sc = generate_scenario(CFG, scale, profile, seed)
    run_mission(sc, CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs={"max_iters": 30},
                snapshot_hook=lambda P, old, call, t: snaps.append((P, old)) if call else None)
    P, old = snaps[len(snaps) // 2]
    d = np.asarray(P.dl, float)
    P.dl = list(P.t0 + shrink * (d - P.t0))
    P.hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    return P, old


def test_break_even_of_both_cost_models():
    w = np.array([1.0, 2.0, 3.0, 5.0])
    for lam in (0.5, 1.0, 2.0):
        th = break_even(w, lam, "fee", WBAR)
        assert np.allclose(th * w - (1 - th) * lam * WBAR, 0.0)        # expected value zero at theta_j
        assert np.all(np.diff(th) < 0)                                  # valuable tasks are attempted more readily
        assert np.allclose(break_even(w, lam, "prop", WBAR), lam / (1 + lam))
    assert np.allclose(break_even([WBAR], 1.0, "fee", WBAR), 0.5)


def test_fee_equals_study5_when_rewards_are_equal():
    P, _ = _problem()
    P.w = [WBAR] * P.N
    for lam in (0.5, 1.0, 2.0):
        a, b = cost_fallback_problem7(P, HIGH, 0.5, lam, "fee", WBAR), cost_fallback_problem(P, HIGH, 0.5, lam)
        assert np.allclose(a.dl, b.dl) and a.hopeless == b.hopeless and a.n_fallback == b.n_fallback


def test_prop_is_study5():
    P, _ = _problem()
    a, b = cost_fallback_problem7(P, HIGH, 0.5, 1.0, "prop", WBAR), cost_fallback_problem(P, HIGH, 0.5, 1.0)
    assert a.dl == b.dl and a.hopeless == b.hopeless


def test_fee_guarantee_per_task():
    """Every task planned to finish by its deadline has p >= theta_j under the error model (Proposition 2(iii))."""
    P, _ = _problem()
    for lam in (0.5, 1.0, 2.0):
        Q = cost_fallback_problem7(P, HIGH, 0.5, lam, "fee", WBAR)
        th = break_even(P.w, lam, "fee", WBAR)
        d = np.asarray(P.dl)
        for j in range(P.N):
            f = Q.dl[j]
            h = f - P.t0
            p = ndtr((d[j] - f - HIGH.mean(h)) / HIGH.sd(h))
            assert p >= th[j] - 1e-9 or j in Q.hopeless


def test_fee_deadlines_non_increasing_in_lam():
    P, _ = _problem()
    prev = None
    for lam in (0.25, 0.5, 1.0, 2.0, 4.0):
        d = np.asarray(cost_fallback_problem7(P, HIGH, 0.5, lam, "fee", WBAR).dl)
        if prev is not None:
            assert np.all(d <= prev + 1e-9)
        prev = d


def test_fee_plans_are_feasible():
    P, old = _problem()
    Q = cost_fallback_problem7(P, HIGH, 0.5, 1.0, "fee", WBAR)
    out = solve7("alns_fixed", P, old, 30, CFG, err=HIGH, z=0.5, lam=1.0, cost="fee", w_bar=WBAR)
    assert not validate(Q, out["solution"])


def test_gauss_shift_reproduces_the_calibrated_level():
    ex, _ = shifted_levels(EXEC_LEVELS, LATENCY_LEVELS)
    a = EXEC_LEVELS["high"].for_mission(1234)
    b = ex["high_gauss"].for_mission(1234)
    for u in range(3):
        for t in range(40):
            assert a.leg(u, t, 900.0, -350.0, 15.0) == b.leg(u, t, 900.0, -350.0, 15.0)
            assert a.ground_speed(u, t, 900.0, -350.0, 15.0) == b.ground_speed(u, t, 900.0, -350.0, 15.0)
        assert a.service(u, 60.0) == b.service(u, 60.0)


def test_shifts_change_the_errors_as_intended():
    ex, lat = shifted_levels(EXEC_LEVELS, LATENCY_LEVELS)
    g = ex["high_gauss"].for_mission(7)
    legs = {s: np.array([ex[f"high_{s}"].for_mission(7).leg(u, t, 3000.0, 0.0, 15.0)[0]
                         for u in range(5) for t in range(400)]) for s in ("gauss", "t3", "outlier", "uavbias")}
    base = legs["gauss"]
    assert np.isclose(legs["outlier"].mean() - base.mean(), 0.1 * 90.0, rtol=0.35)   # extra delay ~ out_p * mean
    assert ((legs["outlier"] - base) > 1e-9).mean() < 0.2
    k = lambda x: ((x - x.mean()) ** 4).mean() / x.var() ** 2
    svc = lambda s: np.array([ex[f"high_{s}"].for_mission(7).service(t, 60.0) for t in range(4000)])
    assert k(svc("t3")) > k(svc("gauss"))                                              # heavier tails
    per_uav = legs["uavbias"].reshape(5, 400).mean(axis=1)
    assert per_uav.std() > base.reshape(5, 400).mean(axis=1).std() * 2                 # correlated within a UAV
    hl, ln = lat["high_pareto"], LATENCY_LEVELS["high"]
    a = np.array([hl.sample(3, i) for i in range(4000)])
    b = np.array([ln.sample(3, i) for i in range(4000)])
    assert math.isclose(np.median(a), np.median(b), rel_tol=0.15)
    assert np.percentile(a, 99) > np.percentile(b, 99)
    assert g.shift == "gauss" and replace(g, shift="t3").shift == "t3"
