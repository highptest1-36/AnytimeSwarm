"""Tier B executor checks.

    ~/venvs/atswarm/bin/python -m pytest -q tests

1. Equivalence: nominal execution + zero latency reproduces the conference executor exactly (deterministic planner:
   ALNS with a fixed iteration count, kappa = 0, the setting used to generate the snapshot benchmark).
2. Disturbances: realistic outputs (bounded rates, positive finish errors under head-wind / acceleration limits).
3. Common random numbers: the same (uav, task) leg gets the same duration whatever the method.
"""
import copy
import math

import pytest

from journal_core import ORIGINAL
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS, ExecutionModel, LatencyModel
from journal_core.kinematic_executor import run_mission_kin

from anytimeswarm.simulator.executor import run_mission
from anytimeswarm.simulator.scenario import generate_scenario
from anytimeswarm.utils import load_config

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
DET = {"max_iters": 60}
CASES = [("small", "arrivals", 0), ("small", "failures", 3), ("medium", "deadlines", 5), ("medium", "failures", 8)]


def _scenario(scale, profile, seed):
    return generate_scenario(CFG, scale, profile, seed)


@pytest.mark.parametrize("scale,profile,seed", CASES)
def test_nominal_equals_conference_executor(scale, profile, seed):
    sc = _scenario(scale, profile, seed)
    a = run_mission(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs=DET)
    b = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs=DET)
    for k in ["served", "completion_rate", "utility_rate", "late_served", "dropped_by_delay", "reassignments",
              "distance_km", "mission_J", "n_replans", "promised_missed"]:
        assert a[k] == b[k], (k, a[k], b[k])
    assert b["dropped_in_exec"] == 0 and b["finish_err_mean_s"] == 0.0


def test_leg_model():
    xm = ExecutionModel("t", accel_mps2=2.0).for_mission(1)
    t, air = xm.leg(0, 0, 1000.0, 0.0, 10.0)
    assert math.isclose(t, 100.0 + 5.0)                       # cruise 100 s + v/a = 5 s
    t, _ = xm.leg(0, 0, 10.0, 0.0, 10.0)                       # short leg: 2*sqrt(L/a)
    assert math.isclose(t, 2.0 * math.sqrt(5.0))
    xw = ExecutionModel("w", wind_mps=5.0).for_mission(3)
    t_out, _ = xw.leg(0, 0, *xw._wind, 10.0)                   # fly WITH the wind
    t_back, _ = xw.leg(0, 0, -xw._wind[0], -xw._wind[1], 10.0)  # fly against it
    assert t_out < t_back


def test_common_random_numbers():
    xm = EXEC_LEVELS["mid"].for_mission(42)
    assert xm.leg(1, 7, 300.0, 400.0, 12.0) == xm.leg(1, 7, 300.0, 400.0, 12.0)
    assert xm.service(7, 60.0) == EXEC_LEVELS["mid"].for_mission(42).service(7, 60.0)
    lat = LATENCY_LEVELS["high"]
    assert lat.sample(42, 3) == lat.sample(42, 3)
    assert LatencyModel().sample(42, 3) == 0.0


@pytest.mark.parametrize("level", ["low", "mid", "high"])
def test_disturbed_missions_are_sane(level):
    sc = _scenario("small", "arrivals", 2)
    m = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=2, solve_kwargs=DET,
                        xm=EXEC_LEVELS[level], lat=LATENCY_LEVELS["high"])
    assert 0.0 <= m["completion_rate"] <= 1.0 and 0.0 <= m["utility_rate"] <= 1.0
    assert m["finish_err_mean_s"] > 0.0                       # acceleration limits only ever add time
    assert m["latency_s_mean"] > 0.0
