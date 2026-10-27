import numpy as np

from anytimeswarm.algorithms.methods import ALL_METHODS, solve
from anytimeswarm.controller.delay_cost import DelayModel
from anytimeswarm.controller.improvement_model import OnlinePredictor
from anytimeswarm.controller.stopping import Adaptive
from anytimeswarm.simulator.executor import MissionExecutor
from anytimeswarm.simulator.scenario import generate_scenario


def _problem(cfg, scale="medium", seed=0):
    sc = generate_scenario(cfg, scale, "arrivals", seed)
    P, old, _ = MissionExecutor(sc, cfg).snapshot(0.0)
    return P


def test_every_method_returns_a_feasible_plan_within_budget(cfg):
    P = _problem(cfg)
    for m in ALL_METHODS:
        r = solve(m, P, None, 40, cfg, seed=1)      # validate() runs inside solve
        assert r["elapsed_ms"] < 40 + 25, (m, r["elapsed_ms"])
        assert r["J"] >= -1e9


def test_alns_never_worse_than_its_initial_plan(cfg):
    P = _problem(cfg, "large")
    base = solve("regret_repair", P, None, 50, cfg)["J"]
    r = solve("alns_fixed", P, None, 80, cfg, seed=2)
    assert r["J"] >= base - 1e-9
    imp = [x[2] for x in r["trace"]["imp"]]
    assert imp == sorted(imp)


def test_same_seed_same_trajectory(cfg):
    P = _problem(cfg)
    a = solve("alns_fixed", P, None, 10_000, cfg, seed=7, max_iters=60)
    b = solve("alns_fixed", P, None, 10_000, cfg, seed=7, max_iters=60)
    assert np.isclose(a["J"], b["J"]) and a["iters"] == b["iters"] == 60


def test_adaptive_stops_early_when_nothing_to_gain(cfg):
    class Zero:
        def predict(self, f):
            return 0.0
    P = _problem(cfg)
    from anytimeswarm.algorithms.alns import run_alns
    from anytimeswarm.algorithms.repair import feasibility_first_repair
    from anytimeswarm.utils import now_ms

    sol = feasibility_first_repair(P, None)
    t0 = now_ms()
    ctrl = Adaptive(Zero(), kappa=1.0, mu=1e-6, check_ms=1, horizon_ms=10, min_ms=1)
    r = run_alns(P, sol, cfg["alns"], np.random.default_rng(0), 300, ctrl, now_ms, t0)
    assert r["stop_reason"] == "adaptive" and now_ms() - t0 < 100


def test_delay_cost_grows_with_kappa(cfg):
    P = _problem(cfg, "large")
    sol = solve("regret_repair", P, None, 50, cfg)["solution"]
    costs = [DelayModel(P, k).lost_value(sol, 500.0) for k in (0, 1, 100, 1000)]
    assert costs[0] == 0 and all(a <= b + 1e-9 for a, b in zip(costs, costs[1:]))


def test_online_predictor_nonnegative():
    from anytimeswarm.controller.features import FEATURES
    f = [0.0] * len(FEATURES)
    assert OnlinePredictor(10).predict(f) >= 0
