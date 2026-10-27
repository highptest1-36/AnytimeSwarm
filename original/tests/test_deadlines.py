from anytimeswarm.simulator.entities import Event
from anytimeswarm.simulator.executor import MissionExecutor, run_mission
from anytimeswarm.simulator.scenario import generate_scenario
from conftest import make_problem


def test_finish_after_deadline_is_infeasible():
    # travel 10 s + service 10 s = finish 20
    assert make_problem([(100, 0, 0, 20, 10, 1)], [(0, 0, 0, 1e5, 10, 0)]).route_eval(0, [0])[0]
    assert not make_problem([(100, 0, 0, 19.9, 10, 1)], [(0, 0, 0, 1e5, 10, 0)]).route_eval(0, [0])[0]


def test_release_time_causes_wait_not_violation():
    P = make_problem([(100, 0, 500, 520, 10, 1)], [(0, 0, 0, 1e5, 10, 0)])
    ok, _ = P.route_eval(0, [0])
    assert ok
    assert P.schedule(0, [0])[0][0][3] == 500


def test_ready_time_shifts_route():
    P = make_problem([(100, 0, 0, 100, 10, 1)], [(0, 0, 85, 1e5, 10, 0)])  # ready at 85 -> finish 105
    assert not P.route_eval(0, [0])[0]


def test_deadline_tightening_is_respected_in_execution(cfg):
    sc = generate_scenario(cfg, "small", "deadlines", 2)
    ex = MissionExecutor(sc, cfg)
    j = sc.tasks[0].id
    ex.apply_event(Event(10.0, "deadline", {"task_id": j, "new_deadline": 11.0}))
    assert ex.tasks[j].deadline == 11.0
    P, _, _ = ex.snapshot(12.0)
    assert j not in P.task_ids          # expired tasks are not offered to the planner


def test_closed_loop_mission_metrics_are_consistent(cfg):
    sc = generate_scenario(cfg, "small", "arrivals", 5)
    m = run_mission(sc, cfg, "regret_repair", 50, kappa=1.0)
    assert 0 <= m["completion_rate"] <= 1 and 0 <= m["utility_rate"] <= 1
    assert m["served"] + round(m["deadline_miss_rate"] * m["n_tasks"]) == m["n_tasks"]
    assert m["n_replans"] == 1 + len(sc.events)
