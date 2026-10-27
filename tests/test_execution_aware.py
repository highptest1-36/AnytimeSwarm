"""Execution-aware extensions: risk-aware delay cost and extra replanning triggers."""
import copy

import numpy as np
import pytest

from journal_core import ORIGINAL
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS, LatencyModel
from journal_core.kinematic_executor import run_mission_kin
from journal_core.methods import solve
from journal_core.risk import ErrorModel, RiskDelayModel, expected_latency

from anytimeswarm.controller.delay_cost import DelayModel
from anytimeswarm.controller.improvement_model import LearnedPredictor
from anytimeswarm.simulator.executor import run_mission
from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
DET = {"max_iters": 60}


def _problem(scale="medium", profile="arrivals", seed=1):
    snaps = []
    sc = generate_scenario(CFG, scale, profile, seed)
    run_mission(sc, CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs={"max_iters": 30},
                snapshot_hook=lambda P, old, call, t: snaps.append((P, old)) if call else None)
    return snaps[len(snaps) // 2]


def test_zero_error_risk_equals_deterministic_delay_cost():
    P, old = _problem()
    sol = solve("regret_repair", P, old, 50, CFG)["solution"]
    det, risk = DelayModel(P, 50.0), RiskDelayModel(P, 50.0, ErrorModel())
    for tau in [0.0, 10.0, 40.0, 250.0, 2000.0, 20000.0]:
        assert det.lost_value(sol, tau) == pytest.approx(risk.lost_value(sol, tau))
        assert det.cost(sol, tau, 10.0) == pytest.approx(risk.cost(sol, tau, 10.0))


def test_risk_cost_is_smooth_and_monotone():
    P, old = _problem()
    sol = solve("regret_repair", P, old, 50, CFG)["solution"]
    risk = RiskDelayModel(P, 50.0, ErrorModel("t", b0=5.0, b1=0.02, s0=5.0, s1=0.1))
    lost = [risk.lost_value(sol, tau) for tau in np.linspace(0, 20000, 41)]
    assert all(b >= a - 1e-9 for a, b in zip(lost, lost[1:]))      # waiting longer never lowers expected loss
    assert risk.cost(sol, 100.0, 10.0) >= 0.0


def test_error_model_fit_recovers_parameters():
    rng = np.random.default_rng(0)
    h = rng.uniform(0, 600, 20000)
    e = 3.0 + 0.05 * h + rng.normal(0, 2.0 + 0.1 * h)
    m = ErrorModel.fit("x", h, e)
    assert m.b0 == pytest.approx(3.0, abs=1.0) and m.b1 == pytest.approx(0.05, abs=0.005)
    assert m.s1 == pytest.approx(0.1, rel=0.1) and m.s0 == pytest.approx(2.0, abs=1.0)


def test_expected_latency():
    assert expected_latency(LatencyModel()) == 0.0
    lat = LATENCY_LEVELS["high"]
    draws = np.array([lat.sample(s, e) for s in range(300) for e in range(20)])
    assert draws.mean() == pytest.approx(expected_latency(lat), rel=0.1)


def test_deviation_trigger_adds_replans_only_under_disturbance():
    sc = generate_scenario(CFG, "small", "arrivals", 2)
    nom = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=2, solve_kwargs=DET,
                          trigger="deviation:30")
    base = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=2, solve_kwargs=DET)
    assert nom["n_extra_replans"] == 0 and nom["utility_rate"] == base["utility_rate"]
    dis = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=2, solve_kwargs=DET,
                          xm=EXEC_LEVELS["mid"], trigger="deviation:30")
    assert dis["n_extra_replans"] > 0
    assert dis["n_replans"] < 200                                    # no runaway triggering


def test_periodic_trigger_and_risk_method_run():
    sc = generate_scenario(CFG, "small", "deadlines", 4)
    pred = LearnedPredictor.load(ORIGINAL / "models" / "improvement_model.json")
    m = run_mission_kin(copy.deepcopy(sc), CFG, "anytime_risk", 50, kappa=10.0, seed=4, xm=EXEC_LEVELS["low"],
                        predictor=pred,
                        lat=LATENCY_LEVELS["low"], trigger="periodic:120", keep_log=True,
                        solve_kwargs={"err": ErrorModel("t", 2.0, 0.03, 5.0, 0.1),
                                      "latency_mean_s": expected_latency(LATENCY_LEVELS["low"])})
    assert m["n_extra_replans"] > 0 and 0.0 <= m["utility_rate"] <= 1.0
    assert len(m["_calib"]) == m["served"] + m["late_served"]
