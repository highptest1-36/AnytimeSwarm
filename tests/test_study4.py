"""Study 4 planning models: moment propagation, proportional buffer and online calibration."""
import numpy as np
import pytest

from journal_core import ORIGINAL
from journal_core.risk import ErrorModel
from journal_core.study3 import solve3
from journal_core.study4 import OnlineCalibrator, mp_problem, solve4

from anytimeswarm.simulator.executor import run_mission
from anytimeswarm.simulator.problem import validate
from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
ZERO = {"a": 0.0, "c": 0.0, "cv": 0.0, "a_s": 0.0, "cv_s": 0.0}
HIGH = {"a": 0.8, "c": -6.8, "cv": 1.15, "a_s": 0.03, "cv_s": 0.25}


def _problem(scale="medium", profile="arrivals", seed=1):
    snaps = []
    sc = generate_scenario(CFG, scale, profile, seed)
    run_mission(sc, CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs={"max_iters": 30},
                snapshot_hook=lambda P, old, call, t: snaps.append((P, old)) if call else None)
    return snaps[len(snaps) // 2]


def _routes(P, n=300, seed=0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        k = int(rng.integers(P.M))
        yield k, list(rng.choice(P.N, size=int(rng.integers(1, min(6, P.N) + 1)), replace=False))


def test_mp_without_error_is_the_nominal_check():
    P, _ = _problem()
    Q = mp_problem(P, ZERO, 1.0, fb=None)
    for k, r in _routes(P):
        assert Q.route_eval(k, r) == P.route_eval(k, r)
    assert Q.hopeless == P.hopeless


def test_mp_is_monotone_in_z_and_never_looser_than_nominal():
    P, _ = _problem()
    q0, q1 = mp_problem(P, HIGH, 0.0, fb=None), mp_problem(P, HIGH, 1.0, fb=None)
    for k, r in _routes(P):
        a, b, c = P.route_eval(k, r)[0], q0.route_eval(k, r)[0], q1.route_eval(k, r)[0]
        assert (c <= b) and (b <= a)


def test_mp_fallback_keeps_only_newly_hopeless_tasks():
    P, _ = _problem()
    Q = mp_problem(P, HIGH, 1.0, fb="nominal")
    assert Q.hopeless == P.hopeless
    sol = solve4("regret_repair", P, None, 50, CFG, mp=HIGH, z_mp=1.0, fb="nominal")["solution"]
    assert not validate(Q, sol)


def test_solve4_without_options_is_solve3():
    P, old = _problem()
    err = ErrorModel("t", 10.0, 0.05, 2.0, 0.2)
    a = solve3("regret_repair", P, old, 50, CFG, err=err, z=0.5, fb="nominal")
    b = solve4("regret_repair", P, old, 50, CFG, err=err, z=0.5, fb="nominal")
    assert a["solution"].routes == b["solution"].routes and a["J"] == b["J"]


def test_proportional_buffer_is_the_affine_model_without_intercept():
    P, old = _problem()
    a = solve4("regret_repair", P, old, 50, CFG, prop=0.2, fb="nominal")
    b = solve3("regret_repair", P, old, 50, CFG, err=ErrorModel("p", 0.0, 0.2, 0.0, 0.0), z=0.0, fb="nominal")
    assert a["solution"].routes == b["solution"].routes
    c = solve4("regret_repair", P, old, 50, CFG, prop=0.0, fb="nominal")
    d = solve4("regret_repair", P, old, 50, CFG)
    assert c["solution"].routes == d["solution"].routes


def test_online_calibration_moves_from_prior_to_mission_data():
    rng = np.random.default_rng(0)
    h0 = rng.uniform(50, 600, 5000)
    e0 = 10 + 0.1 * h0 + rng.normal(0, 1 + 0.2 * h0)
    cal = OnlineCalibrator(50, (h0, e0))
    assert cal.model([]).b1 == pytest.approx(cal.prior.b1)
    h1 = rng.uniform(50, 600, 3000)
    e1 = 30 + 0.4 * h1 + rng.normal(0, 1 + 0.6 * h1)
    m = cal.model(list(zip(h1, e1)))
    assert m.b1 == pytest.approx(0.4, abs=0.05) and m.s1 == pytest.approx(0.6, rel=0.15)
    few = cal.model(list(zip(h1[:5], e1[:5])))
    assert abs(few.b1 - cal.prior.b1) < abs(m.b1 - cal.prior.b1)


def test_mp_plan_is_feasible_after_search():
    P, old = _problem("large", "failures", 2)
    Q = mp_problem(P, HIGH, 2.0, fb="nominal")
    for s in range(3):
        out = solve4("alns_fixed", P, old, 40, CFG, seed=s, mp=HIGH, z_mp=2.0, fb="nominal")
        assert not validate(Q, out["solution"])
