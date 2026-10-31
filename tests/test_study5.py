"""Study 5: cost-aware fallback."""
import math

import numpy as np
from scipy.special import ndtr

from journal_core import ORIGINAL
from journal_core.risk import ErrorModel
from journal_core.study2 import buffered_problem
from journal_core.study3 import fallback_problem
from journal_core.study5 import cost_fallback_problem, solve5, z_of_cost

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
    d = np.asarray(P.dl, float)          # short windows, so that the chance constraint gives up tasks
    P.dl = list(P.t0 + shrink * (d - P.t0))
    P.hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    return P, old


def test_break_even_probability():
    for lam in (0.25, 0.5, 1.0, 2.0, 4.0):
        p = float(ndtr(z_of_cost(lam)))
        assert math.isclose(p * 1.0 - (1.0 - p) * lam, 0.0, abs_tol=1e-9)
    assert z_of_cost(0.0) == -math.inf and z_of_cost(1.0) == 0.0


def test_zero_cost_is_the_nominal_fallback():
    P, _ = _problem()
    a, b = cost_fallback_problem(P, HIGH, 0.5, 0.0), fallback_problem(P, HIGH, 0.5, "nominal")
    assert a.dl == b.dl and a.hopeless == b.hopeless


def test_deadlines_lie_between_no_fallback_and_nominal_fallback():
    P, _ = _problem()
    lo = np.asarray(buffered_problem(P, HIGH, 0.5).dl)
    hi = np.asarray(fallback_problem(P, HIGH, 0.5, "nominal").dl)
    prev = hi
    for lam in (0.25, 0.5, 1.0, 2.0):
        d = np.asarray(cost_fallback_problem(P, HIGH, 0.5, lam).dl)
        assert np.all(d <= hi + 1e-9) and np.all(d >= np.minimum(lo, d) - 1e-9)
        assert np.all(d <= prev + 1e-9)          # a higher late cost never loosens a deadline
        prev = d


def test_high_cost_protects_at_the_break_even_level():
    P, _ = _problem()
    lam = 4.0                                     # z_lam = 0.84 > z = 0.5: no fallback, protection at z_lam
    a = cost_fallback_problem(P, HIGH, 0.5, lam)
    assert a.dl == buffered_problem(P, HIGH, z_of_cost(lam)).dl


def test_fallback_tasks_exist_and_plans_are_feasible():
    P, old = _problem()
    Q = cost_fallback_problem(P, HIGH, 0.5, 1.0)
    assert Q.n_fallback > 0
    out = solve5("alns_fixed", P, old, 30, CFG, err=HIGH, z=0.5, lam=1.0)
    assert not validate(Q, out["solution"])


def test_proportional_buffer_without_fallback():
    P, old = _problem()
    out = solve5("regret_repair", P, old, 30, CFG, prop_nofb=0.6)
    Q = buffered_problem(P, ErrorModel("prop", 0.0, 0.6, 0.0, 0.0), 0.0)
    assert not validate(Q, out["solution"])
