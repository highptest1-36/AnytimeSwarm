"""Study 6: CBBA and moment propagation with the cost-aware fallback."""
import time

from journal_core import ORIGINAL
from journal_core.risk import ErrorModel
from journal_core.study4 import load_mp, mp_problem
from journal_core.study5 import cost_fallback_problem
from journal_core.study6 import cbba, mp_cost_problem, solve6

from anytimeswarm.simulator.executor import run_mission
from anytimeswarm.simulator.problem import validate
from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
HIGH = ErrorModel("high", 20.79, 0.292, 0.0, 0.639)


def _problem(scale="medium", profile="arrivals", seed=1, shrink=0.5):
    snaps = []
    sc = generate_scenario(CFG, scale, profile, seed)
    run_mission(sc, CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs={"max_iters": 30},
                snapshot_hook=lambda P, old, call, t: snaps.append((P, old)) if call else None)
    P, old = snaps[len(snaps) // 2]
    P.dl = list(P.t0 + shrink * (__import__("numpy").asarray(P.dl, float) - P.t0))
    P.hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    return P, old


def test_cbba_is_feasible_and_conflict_free():
    for scale in ("small", "medium", "large"):
        P, _ = _problem(scale, shrink=1.0)
        sol, rounds, reason = cbba(P, 1e9)
        assert not validate(P, sol)
        assert reason == "converged" and rounds >= 1
        assert sol.n_assigned() > 0


def test_cbba_no_agent_can_outbid_after_convergence():
    """At convergence, no agent has a positive marginal score above the winning bid of a task it does not hold."""
    from anytimeswarm.algorithms.insertion import best_in_route
    P, _ = _problem("medium", shrink=1.0)
    sol, _, _ = cbba(P, 1e9)
    for j in sol.unassigned - P.hopeless:
        for k in range(P.M):
            o = best_in_route(P, sol, k, j)
            assert o is None or o[0] <= 1e-9


def test_cbba_on_the_proposed_model():
    P, _ = _problem()
    Q = cost_fallback_problem(P, HIGH, 0.5, 1.0)
    out = solve6("cbba", P, None, 1e9, CFG, err=HIGH, z=0.5, lam=1.0)
    assert not validate(Q, out["solution"])


def test_cbba_respects_the_budget():
    P, _ = _problem("large", shrink=1.0)
    t = time.perf_counter()
    cbba(P, 5.0)
    assert time.perf_counter() - t < 2.0


def test_mp_cost_zero_is_the_nominal_fallback():
    P, _ = _problem()
    mp = load_mp()["high"]
    a, b = mp_cost_problem(P, mp, 0.5, 0.0), mp_problem(P, mp, 0.5, "nominal")
    assert a._mp == b._mp and a.hopeless == b.hopeless


def test_mp_cost_accepts_between_no_fallback_and_nominal_fallback():
    P, _ = _problem()
    mp = load_mp()["high"]
    none, nom, ca = mp_problem(P, mp, 0.5, None), mp_problem(P, mp, 0.5, "nominal"), mp_cost_problem(P, mp, 0.5, 1.0)
    single = lambda Q: {(k, j) for k in range(P.M) for j in range(P.N) if Q.route_eval(k, [j])[0]}  # noqa: E731
    assert single(none) <= single(ca) <= single(nom)
    assert ca.n_fallback > 0


def test_mp_cost_plans_are_feasible():
    P, old = _problem()
    mp = load_mp()["high"]
    out = solve6("alns_fixed", P, old, 30, CFG, err=HIGH, mp=mp, z_mp=0.5, lam=1.0)
    assert not validate(mp_cost_problem(P, mp, 0.5, 1.0), out["solution"])
