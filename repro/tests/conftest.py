import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.simulator.problem import Problem  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return load_config()


def make_problem(tasks, uavs, t0=0.0, depot=(0.0, 0.0), objective=None, hover=0.0, prev=None):
    """tasks: list of (x, y, release, deadline, service, reward); uavs: list of (x, y, ready, energy, speed, reserve)"""
    objective = objective or {"alpha": 1.0, "gamma": 0.0, "delta": 0.0}
    return Problem(
        t0, depot, list(range(len(uavs))), [(u[0], u[1]) for u in uavs], [u[2] for u in uavs],
        [u[3] for u in uavs], [u[4] for u in uavs], [u[5] for u in uavs], list(range(len(tasks))),
        [(t[0], t[1]) for t in tasks], [t[2] for t in tasks], [t[3] for t in tasks], [t[4] for t in tasks],
        [t[5] for t in tasks], prev or [-1] * len(tasks), objective, hover)
