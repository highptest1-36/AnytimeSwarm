from anytimeswarm.simulator.entities import Event
from anytimeswarm.simulator.executor import MissionExecutor
from anytimeswarm.simulator.scenario import generate_scenario
from conftest import make_problem


def test_energy_includes_return_and_reserve():
    # out 1000 m + back 1000 m = 2000 m of flight
    task = [(1000, 0, 0, 1e4, 0, 1)]
    assert make_problem(task, [(0, 0, 0, 2000, 10, 0)]).route_eval(0, [0])[0]
    assert not make_problem(task, [(0, 0, 0, 1999, 10, 0)]).route_eval(0, [0])[0]
    assert not make_problem(task, [(0, 0, 0, 2500, 10, 600)]).route_eval(0, [0])[0]   # reserve 600


def test_hover_energy_during_service():
    task = [(1000, 0, 0, 1e4, 100, 1)]   # 100 s service at 5 m/s hover cost = 500 m
    assert make_problem(task, [(0, 0, 0, 2500, 10, 0)], hover=5).route_eval(0, [0])[0]
    assert not make_problem(task, [(0, 0, 0, 2499, 10, 0)], hover=5).route_eval(0, [0])[0]


def test_empty_route_always_allowed():
    P = make_problem([(1000, 0, 0, 1e4, 0, 1)], [(5000, 0, 0, 10, 10, 0)])  # cannot even return
    assert P.route_eval(0, [])[0]


def test_failed_uav_is_removed_and_tasks_return_to_pool(cfg):
    sc = generate_scenario(cfg, "small", "failures", 0)
    ex = MissionExecutor(sc, cfg)
    P0, _, _ = ex.snapshot(0.0)
    ex.apply_event(Event(1.0, "failure", {"uav_id": 0}))
    P1, _, _ = ex.snapshot(1.0)
    assert P1.M == P0.M - 1 and 0 not in P1.uav_ids
