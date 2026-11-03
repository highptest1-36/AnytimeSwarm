"""Study 8: timing of the whole planning call, explicit-option planner of tier C, emergency-response scenario family."""
import time

import numpy as np
import pytest

from journal_core import ORIGINAL
from journal_core import study8
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS
from journal_core.kinematic_executor import run_mission_kin
from journal_core.risk import ErrorModel
from journal_core.study7 import solve7
from journal_core.study8 import (PROFILES8, SCALES8, WORLD8, generate_scenario8, is_urgent, n_tasks8, solve8,
                                 solve8_kwargs, timed, timing_columns, w_bar)

from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
HIGH = ErrorModel("high", 20.79, 0.292, 0.0, 0.639)


# ---------------------------------------------------------------------------------------------- timing
def test_timed_charges_the_whole_call():
    def slow(*a, **kw):
        time.sleep(0.02)                               # model construction before the search clock starts
        return {"elapsed_ms": 5.0, "iters": 7, "t_first_feasible_ms": 1.0}
    log = []
    out = timed(slow, log)()
    assert out["search_ms"] == 5.0
    assert out["elapsed_ms"] >= 20.0
    assert len(log) == 1 and log[0][1] == 5.0 and log[0][3] == 7
    c = timing_columns(log, 10.0)
    assert c["n_calls"] == 1 and c["over_ms_mean"] == pytest.approx(out["elapsed_ms"] - 10.0)
    assert c["model_ms_mean"] == pytest.approx(out["elapsed_ms"] - 5.0)
    assert c["iters_per_search_ms"] == pytest.approx(7 / 5.0)


def test_w_bar_is_the_generator_mean_reward():
    assert w_bar(CFG) == pytest.approx(2.1)


# ---------------------------------------------------------------------------------------------- explicit options
def test_option_routing():
    assert solve8_kwargs({"z": "0.5", "lam": "1", "cost": "fee"}, HIGH, 2.1) == \
        {"err": HIGH, "z": 0.5, "lam": 1.0, "cost": "fee", "w_bar": 2.1}
    assert solve8_kwargs({"z": "0.5", "lam": "1"}, HIGH, 2.1)["cost"] == "prop"
    assert solve8_kwargs({"z": "0.5", "fb": "nominal"}, HIGH, 2.1) == {"err": HIGH, "z": 0.5, "fb": "nominal"}
    assert solve8_kwargs({"prop": "0.45", "fb": "none"}, HIGH, 2.1) == {"err": HIGH, "z": None, "prop_nofb": 0.45}
    assert solve8_kwargs({}, HIGH, 2.1) == {"err": HIGH, "z": None}
    with pytest.raises(ValueError):
        solve8_kwargs({"lam": "1"}, HIGH, 2.1)          # cost-aware fallback without z
    with pytest.raises(ValueError):
        solve8_kwargs({"prop": "0.45"}, HIGH, 2.1)      # buffer with fallback is not part of study 8
    with pytest.raises(ValueError):
        solve8_kwargs({"z": "0.5", "mp": "auto"}, HIGH, 2.1)


def test_solve8_calls_solve7_with_the_routed_arguments(monkeypatch):
    seen = {}

    def fake(base, P, old, budget, cfg, **kw):
        seen.update(base=base, budget=budget, **kw)
        return {"elapsed_ms": 1.0, "iters": 3}
    monkeypatch.setattr(study8, "solve7", fake)
    log = []
    out = solve8("alns_fixed", None, None, 40.0, CFG, {"z": "0.5", "lam": "1", "cost": "fee"}, HIGH, 2.1, seed=9,
                 kappa=12.5, log=log)
    assert seen["base"] == "alns_fixed" and seen["budget"] == 40.0 and seen["seed"] == 9 and seen["kappa"] == 12.5
    assert seen["z"] == 0.5 and seen["lam"] == 1.0 and seen["cost"] == "fee" and seen["w_bar"] == 2.1
    assert seen["err"] is HIGH and out["search_ms"] == 1.0 and len(log) == 1


# ---------------------------------------------------------------------------------------------- scenario family
def test_family_is_seeded_and_disjoint_from_the_conference_generator():
    a = generate_scenario8(CFG, "medium8", "incidents", 3, load=1.0)
    b = generate_scenario8(CFG, "medium8", "incidents", 3, load=1.0)
    c = generate_scenario8(CFG, "medium8", "incidents", 4, load=1.0)
    assert [(t.x, t.deadline) for t in a.tasks] == [(t.x, t.deadline) for t in b.tasks]
    assert [(t.x, t.deadline) for t in a.tasks] != [(t.x, t.deadline) for t in c.tasks]
    conf = generate_scenario(CFG, "medium", "arrivals", 3)
    assert {(t.x, t.y) for t in a.tasks}.isdisjoint({(t.x, t.y) for t in conf.tasks})


def test_family_world_and_task_ranges():
    Lx, Ly = WORLD8["map_xy_m"]
    tasks, urgent = [], 0
    for p in PROFILES8:
        for s in range(20):
            sc = generate_scenario8(CFG, "large8", p, s, load=1.0)
            assert sc.depot == (Lx / 2, Ly / 2)
            assert len(sc.tasks) == n_tasks8(CFG, "large8", 1.0)
            assert all(WORLD8["speed_mps"][0] <= u.speed <= WORLD8["speed_mps"][1] for u in sc.uavs)
            for t in sc.tasks:
                assert 0 <= t.x <= Lx and 0 <= t.y <= Ly
                assert WORLD8["service_s"][0] <= t.service <= WORLD8["service_s"][1]
                assert 0 <= t.release - t.announce <= WORLD8["announce_lead_s"][1]
                win = t.deadline - t.release - t.service
                assert WORLD8["urgent_window_s"][0] <= win <= WORLD8["window_s"][1]
                urgent += is_urgent(t)
            tasks += sc.tasks
            assert sc.world["hover_m_per_s"] == CFG["world"]["hover_m_per_s"]
            assert sc.world["reward_levels"] == CFG["world"]["reward_levels"]
    assert abs(urgent / len(tasks) - WORLD8["urgent_frac"]) < 0.03
    assert sum(t.announce == 0 for t in tasks) / len(tasks) == pytest.approx(WORLD8["initial_frac"], abs=0.02)


def test_profiles():
    for s in range(10):
        inc = generate_scenario8(CFG, "medium8", "incidents", s, load=1.0)
        arr = [e for e in inc.events if e.kind == "arrival"]
        assert 1 <= len(arr) <= PROFILES8["incidents"]["bursts"] and all(e.kind == "arrival" for e in inc.events)
        for scale in SCALES8:
            att = generate_scenario8(CFG, scale, "attrition", s, load=1.0)
            f = [e.data["uav_id"] for e in att.events if e.kind == "failure"]
            assert len(f) == PROFILES8["attrition"]["failures"][scale] and len(set(f)) == len(f)
        pri = generate_scenario8(CFG, "medium8", "priorities", s, load=1.0)
        cuts = [e for e in pri.events if e.kind == "deadline"]
        assert 1 <= len(cuts) <= PROFILES8["priorities"]["deadline_cuts"]
        by_id = {t.id: t for t in pri.tasks}
        assert all(e.data["new_deadline"] <= by_id[e.data["task_id"]].deadline for e in cuts)
        assert [e.time for e in pri.events] == sorted(e.time for e in pri.events)
    # bursts are uneven: the largest burst carries well above an even share on average
    share = np.mean([max(len(e.data["task_ids"]) for e in generate_scenario8(CFG, "large8", "incidents", s, 1.0).events)
                     / sum(len(e.data["task_ids"]) for e in generate_scenario8(CFG, "large8", "incidents", s, 1.0).events)
                     for s in range(20)])
    assert share > 2.0 / PROFILES8["incidents"]["bursts"]


def test_load_scales_the_number_of_tasks(monkeypatch):
    assert n_tasks8(CFG, "small8", 0.8) == 20 and n_tasks8(CFG, "large8", 1.25) == 175
    monkeypatch.setattr(study8, "LOAD8", None)
    with pytest.raises(RuntimeError):
        generate_scenario8(CFG, "small8", "incidents", 0)


def test_is_urgent_with_tightened_windows():
    sc = generate_scenario8(CFG, "small8", "incidents", 1, load=1.0)
    from journal_core.study2 import tighten_windows
    half = tighten_windows(sc, 0.5)
    assert [is_urgent(t) for t in sc.tasks] == [is_urgent(t, 0.5) for t in half.tasks]


def test_family_mission_runs_with_the_timed_planner():
    sc = generate_scenario8(CFG, "small8", "priorities", 2, load=1.0)
    log = []
    r = run_mission_kin(sc, CFG, "alns_fixed", 5.0, kappa=10.0, xm=EXEC_LEVELS["high"], lat=LATENCY_LEVELS["high"],
                        seed=2, trigger="periodic:60", solver=timed(solve7, log),
                        solve_kwargs={"err": HIGH, "z": 0.5, "lam": 1.0, "cost": "fee", "w_bar": 2.1})
    assert r["n_replans"] == len(log) > 0
    assert 0.0 <= r["utility_rate"] <= 1.0
    assert r["plan_ms_mean"] == pytest.approx(np.mean([x[0] for x in log]))
