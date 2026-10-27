import numpy as np

from anytimeswarm.algorithms.insertion import parallel_insert
from anytimeswarm.algorithms.repair import feasibility_first_repair, filter_route
from anytimeswarm.simulator.problem import Solution, delayed_value, empty_solution, validate
from anytimeswarm.simulator.scenario import generate_scenario
from conftest import make_problem


def test_scenario_is_deterministic(cfg):
    a = generate_scenario(cfg, "medium", "failures", 3)
    b = generate_scenario(cfg, "medium", "failures", 3)
    c = generate_scenario(cfg, "medium", "failures", 4)
    assert [(t.x, t.deadline) for t in a.tasks] == [(t.x, t.deadline) for t in b.tasks]
    assert [(e.time, e.kind) for e in a.events] == [(e.time, e.kind) for e in b.events]
    assert [(t.x, t.deadline) for t in a.tasks] != [(t.x, t.deadline) for t in c.tasks]
    assert len(a.tasks) == cfg["scales"]["medium"]["n_tasks"] and len(a.uavs) == cfg["scales"]["medium"]["n_uav"]


def test_route_eval_matches_schedule():
    P = make_problem([(100, 0, 0, 1000, 10, 1), (200, 0, 50, 1000, 10, 2)], [(0, 0, 0, 10_000, 10, 0)])
    ok, d = P.route_eval(0, [0, 1])
    entries, skipped, d2, _ = P.schedule(0, [0, 1])
    assert ok and not skipped and np.isclose(d, d2) and np.isclose(d, 400)
    assert np.isclose(entries[0][4], 20.0)     # arrive 10 s, serve 10 s
    assert np.isclose(entries[1][3], 50.0)     # wait for release at 50
    assert np.isclose(entries[1][4], 60.0)


def test_validate_flags_errors():
    P = make_problem([(100, 0, 0, 5, 10, 1)], [(0, 0, 0, 10_000, 10, 0)])  # deadline 5 < 20
    sol = Solution.__new__(Solution)
    sol.routes, sol.dist, sol.unassigned = [[0]], [200.0], set()
    assert validate(P, sol)
    assert filter_route(P, 0, [0]) == []
    assert 0 in P.hopeless


def test_insertion_and_ffr_are_feasible(cfg):
    from anytimeswarm.simulator.executor import MissionExecutor

    sc = generate_scenario(cfg, "large", "arrivals", 0)
    ex = MissionExecutor(sc, cfg)
    P, old, _ = ex.snapshot(0.0)
    for regret in (1, 2, 3):
        sol = parallel_insert(P, empty_solution(P), list(range(P.N)), regret=regret)
        assert not validate(P, sol)
        assert sol.n_assigned() > 0
    sol = feasibility_first_repair(P, [[j for j in range(P.N)][k::P.M] for k in range(P.M)])
    assert not validate(P, sol)


def test_delayed_value_never_exceeds_on_time_value(cfg):
    from anytimeswarm.simulator.executor import MissionExecutor

    sc = generate_scenario(cfg, "medium", "arrivals", 1)
    P, _, _ = MissionExecutor(sc, cfg).snapshot(0.0)
    sol = feasibility_first_repair(P, None)
    J = sol.objective(P)
    prev = J
    for delay in (0, 30, 120, 600):
        Jd, lost = delayed_value(P, sol, delay)
        assert Jd <= prev + 1e-6
        prev = Jd
    assert np.isclose(delayed_value(P, sol, 0)[0], J)
