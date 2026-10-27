import pytest

from anytimeswarm.simulator.problem import validate
from conftest import make_problem

pytest.importorskip("ortools")
from anytimeswarm.algorithms.ortools_ref import solve_ortools  # noqa: E402


def test_ortools_handles_hopeless_task():
    # task 1 is unreachable in time (hopeless) but has a valid time window -> must stay optional
    P = make_problem([(100, 0, 0, 1000, 10, 1), (50_000, 0, 0, 100, 10, 5)], [(0, 0, 0, 10_000, 10, 0)])
    assert P.hopeless == {1}
    sol = solve_ortools(P, 1.0)
    assert sol is not None and not validate(P, sol)
    assert sol.routes == [[0]]


def test_ortools_respects_stability_penalty():
    # both UAVs can serve the task; serving it with the previous UAV (index 1) avoids the delta penalty
    obj = {"alpha": 1.0, "gamma": 0.0, "delta": 0.3}
    P = make_problem([(100, 0, 0, 1000, 10, 1)], [(0, 0, 0, 10_000, 10, 0), (0, 0, 0, 10_000, 10, 0)],
                     objective=obj, prev=[1])
    sol = solve_ortools(P, 1.0)
    assert sol.routes == [[], [0]]
    assert abs(sol.objective(P) - 1.0) < 1e-9
