"""Plain data classes of the mission world."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    id: int
    x: float
    y: float
    announce: float      # time the task becomes known to the planner
    release: float       # r_j: earliest service start
    deadline: float      # d_j: service must FINISH by d_j
    service: float       # s_j
    reward: float        # w_j


@dataclass
class UAV:
    id: int
    x: float
    y: float
    speed: float         # m/s
    capacity: float      # energy capacity in metres of flight


@dataclass
class Event:
    time: float
    kind: str            # "arrival" | "failure" | "deadline"
    data: dict = field(default_factory=dict)


@dataclass
class Scenario:
    name: str
    seed: int
    scale: str
    profile: str
    depot: tuple
    uavs: list
    tasks: list          # every task of the mission (initial + future arrivals)
    events: list         # dynamic events after t = 0, sorted by time
    world: dict
    objective: dict
