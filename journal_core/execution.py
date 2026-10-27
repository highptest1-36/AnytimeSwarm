"""Execution and communication models of tier B.

The planner keeps the conference model (straight legs at constant cruise speed, nominal service time). The executor
draws the ACTUAL leg and service durations from an ExecutionModel and the plan-dissemination delay from a
LatencyModel. Disturbances use common random numbers: every draw is keyed by (mission seed, model seed, uav, task)
or (mission seed, model seed, event index), so all methods face the same wind, gusts and service times for the same
assignment, independently of how many legs or replanning calls a method produces.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np


def _rng(*key) -> np.random.Generator:
    return np.random.default_rng([int(k) & 0xFFFFFFFF for k in key])


@dataclass
class ExecutionModel:
    """Actual flight of one leg: trapezoidal speed profile, constant wind, per-(uav, task) cruise-speed error.

    accel_mps2   : horizontal acceleration limit (inf = instantaneous, the conference model)
    speed_cv     : std of the multiplicative cruise-speed error (gusts, controller tracking), per (uav, task) leg
    wind_mps     : constant wind magnitude for the whole mission; direction drawn per mission
    service_cv   : std of the multiplicative service-time error, per task
    skip_late    : at departure the executor skips a task whose NOMINAL finish estimate already misses the deadline
    """
    name: str = "nominal"
    accel_mps2: float = math.inf
    speed_cv: float = 0.0
    wind_mps: float = 0.0
    service_cv: float = 0.0
    skip_late: bool = True
    seed: int = 0
    mission_seed: int = 0

    @property
    def nominal(self) -> bool:
        return (math.isinf(self.accel_mps2) and self.speed_cv == 0.0 and self.wind_mps == 0.0
                and self.service_cv == 0.0)

    def for_mission(self, mission_seed: int) -> "ExecutionModel":
        m = replace(self, mission_seed=int(mission_seed))
        ang = _rng(mission_seed, self.seed, 7).uniform(0.0, 2.0 * math.pi)
        m._wind = (self.wind_mps * math.cos(ang), self.wind_mps * math.sin(ang))
        return m

    def leg(self, uav_id: int, task_id: int, dx: float, dy: float, airspeed: float) -> tuple[float, float]:
        """(duration s, air distance m) of the leg (dx, dy) flown by uav_id towards task_id."""
        L = math.hypot(dx, dy)
        if L == 0.0:
            return 0.0, 0.0
        eps = _rng(self.mission_seed, self.seed, 1, uav_id, task_id).normal(0.0, self.speed_cv) if self.speed_cv else 0.0
        v = airspeed * (1.0 + float(np.clip(eps, -0.3, 0.3)))
        wx, wy = getattr(self, "_wind", (0.0, 0.0))
        ux, uy = dx / L, dy / L
        w_par = wx * ux + wy * uy
        w_perp = abs(wx * uy - wy * ux)
        vg = math.sqrt(max(v * v - w_perp * w_perp, (0.2 * v) ** 2)) + w_par   # crab into the wind
        vg = max(vg, 0.2 * v)
        a = self.accel_mps2
        if math.isinf(a):
            t = L / vg
        elif L >= vg * vg / a:
            t = L / vg + vg / a                                                  # accelerate + cruise + brake
        else:
            t = 2.0 * math.sqrt(L / a)                                           # never reaches cruise speed
        return t, v * t                                                          # energy = metres flown through air

    def service(self, task_id: int, nominal_s: float) -> float:
        if not self.service_cv:
            return nominal_s
        eps = _rng(self.mission_seed, self.seed, 2, task_id).normal(0.0, self.service_cv)
        return nominal_s * float(np.clip(1.0 + eps, 0.5, 2.0))


@dataclass
class LatencyModel:
    """Delay between the end of planning and the moment every UAV has accepted the new plan (mission seconds).

    lognormal base delay (median_s, sigma); each message is lost with probability drop_p and re-sent after
    timeout_s (geometric number of losses, at most 5). median_s = 0 disables the model.
    """
    name: str = "none"
    median_s: float = 0.0
    sigma: float = 0.0
    drop_p: float = 0.0
    timeout_s: float = 0.0
    seed: int = 0

    def sample(self, mission_seed: int, event_index: int) -> float:
        if self.median_s <= 0.0 and self.drop_p <= 0.0:
            return 0.0
        r = _rng(mission_seed, self.seed, 3, event_index)
        d = self.median_s * math.exp(self.sigma * r.normal()) if self.median_s > 0 else 0.0
        losses = 0
        while losses < 5 and r.random() < self.drop_p:
            losses += 1
        return d + losses * self.timeout_s


# Starting levels for the pilot. They are placeholders until tier C (PX4/Gazebo) measures leg-time errors and
# ROS 2 / DDS delays; the final levels are frozen before the held-out runs (plan D3).
EXEC_LEVELS = {
    "nominal": ExecutionModel("nominal"),
    "low": ExecutionModel("low", accel_mps2=3.0, speed_cv=0.03, wind_mps=2.0, service_cv=0.05),
    "mid": ExecutionModel("mid", accel_mps2=2.0, speed_cv=0.07, wind_mps=5.0, service_cv=0.15),
    "high": ExecutionModel("high", accel_mps2=1.5, speed_cv=0.12, wind_mps=8.0, service_cv=0.25),
}
LATENCY_LEVELS = {
    "none": LatencyModel("none"),
    "low": LatencyModel("low", median_s=0.2, sigma=0.5),
    "high": LatencyModel("high", median_s=2.0, sigma=0.8, drop_p=0.05, timeout_s=5.0),
}
