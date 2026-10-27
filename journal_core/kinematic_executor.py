"""Tier B closed-loop execution: the conference MissionExecutor with an actual-execution model and plan latency.

Semantics kept from the conference executor (anytimeswarm/simulator/executor.py): events arriving while the planner
is busy are queued, commit horizon = 1 task, idle UAVs wait for the published plan, tasks that the PLANNER's model
finds infeasible at publication are returned to the pool ("dropped by delay").

What changes:
  * publication time  t_pub = t_now + kappa * planning_ms / 1000 + latency   (latency from LatencyModel)
  * every published leg / service is executed with ExecutionModel durations; reward only if the ACTUAL finish
    meets the (possibly tightened) deadline. With skip_late, a UAV skips a task at departure when the nominal
    estimate from its actual state already misses the deadline ("dropped in execution").
  * the planner sees telemetry, not the future: a UAV flying its committed task is reported with the planner's
    nominal estimate of the remaining flight and service from its actual position.
With ExecutionModel nominal and zero latency the class falls back to the conference code path, so results are
identical to anytimeswarm.simulator.executor.run_mission (tests/test_kinematic.py checks this).
"""
from __future__ import annotations

import math

import numpy as np

from . import ORIGINAL  # noqa: F401  (puts the frozen conference package on sys.path)
from anytimeswarm.algorithms.methods import solve
from anytimeswarm.simulator.executor import MissionExecutor
from anytimeswarm.simulator.problem import Problem

from .execution import ExecutionModel, LatencyModel


class KinematicExecutor(MissionExecutor):
    def __init__(self, scenario, cfg: dict, xm: ExecutionModel):
        super().__init__(scenario, cfg)
        self.xm = xm.for_mission(scenario.seed)
        self.dropped_in_exec = 0
        self.planned_fin: dict[int, float] = {}       # task -> planner's finish estimate at its last publication

    # ------------------------------------------------------------------ planner's view (telemetry)
    def _estimate_locked(self, uid, e, t):
        """Planner estimate of (finish time, energy after) for the committed entry e at time t."""
        j, dep, arr, start, fin, leg, e_after = e
        if self.xm.nominal:
            return fin, e_after
        task, u = self.tasks[j], self.uav[uid]
        if t < arr:                                    # still flying: remaining distance from actual progress
            frac = (arr - t) / (arr - dep) if arr > dep else 0.0
            est_arr = t + frac * leg / u["speed"]
            est_fin = max(est_arr, task.release) + task.service
        else:                                          # serving (or waiting for the release time)
            est_fin = max(max(start, task.release) + task.service, t)
        return est_fin, e_after

    def snapshot(self, t: float):
        P, old_routes, locked = super().snapshot(t)
        if self.xm.nominal:
            return P, old_routes, locked
        for k, uid in enumerate(P.uav_ids):
            if locked[uid]:
                P.ready[k], P.energy[k] = self._estimate_locked(uid, locked[uid], t)
        P.hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
        return P, old_routes, locked

    # ------------------------------------------------------------------ actual execution
    def publish(self, P: Problem, routes, locked, t_pub: float) -> None:
        if self.xm.nominal:
            super().publish(P, routes, locked, t_pub)
            for uid in P.uav_ids:
                for e in self.uav[uid]["sched"][1 if locked[uid] else 0:]:
                    self.planned_fin[e[0]] = e[4]
            return
        for k, uid in enumerate(P.uav_ids):
            u = self.uav[uid]
            entries, skipped, _, _ = P.schedule(k, routes[k], start_time=t_pub, skip_infeasible=True)
            self.dropped_by_delay += len(skipped)
            if locked[uid]:
                lk = locked[uid]
                lt = self.tasks[lk[0]]
                x, y, t, e_now = lt.x, lt.y, lk[4], lk[6]
                new = [lk]
            else:
                x, y, t, e_now = u["x"], u["y"], max(u["ready"], t_pub), u["energy"]
                new = []
            for j, _dep, _arr, _start, fin_plan in entries:
                gid = P.task_ids[j]
                task = self.tasks[gid]
                dx, dy = task.x - x, task.y - y
                L = math.hypot(dx, dy)
                if self.xm.skip_late:
                    est = max(t + L / u["speed"], task.release) + task.service
                    if est > task.deadline:
                        self.dropped_in_exec += 1
                        continue
                t_leg, air = self.xm.leg(uid, gid, dx, dy, u["speed"])
                arr = t + t_leg
                start = max(arr, task.release)
                s_act = self.xm.service(gid, task.service)
                fin = start + s_act
                e_now -= air + self.hover * s_act
                new.append((gid, t, arr, start, fin, L, e_now))
                if gid in self.assigned_to and self.assigned_to[gid] != uid:
                    self.reassign += 1
                self.assigned_to[gid] = uid
                self.promised.add(gid)
                self.planned_fin[gid] = fin_plan
                x, y, t = task.x, task.y, fin
            u["sched"] = new
            if not locked[uid]:
                u["ready"] = max(u["ready"], t_pub)

    def finish(self) -> dict:
        m = super().finish()
        err = np.array([fin - self.planned_fin[j] for (_u, j, _d, _s, fin) in self.executed if j in self.planned_fin])
        depot = self.sc.depot
        stranded = sum(1 for u in self.uav.values() if u["alive"]
                       and u["energy"] - math.hypot(u["x"] - depot[0], u["y"] - depot[1]) < 0.0)
        m.update({
            "dropped_in_exec": self.dropped_in_exec,
            "energy_violations": stranded,
            "finish_err_mean_s": float(err.mean()) if err.size else 0.0,
            "finish_err_p95_s": float(np.percentile(err, 95)) if err.size else 0.0,
            "exec_level": self.xm.name,
        })
        return m


def run_mission_kin(scenario, cfg: dict, method: str, budget_ms: float, kappa: float = 1.0,
                    xm: ExecutionModel | None = None, lat: LatencyModel | None = None,
                    predictor=None, seed: int = 0, keep_log: bool = False, solve_kwargs: dict | None = None) -> dict:
    """Same loop as anytimeswarm.simulator.executor.run_mission, plus execution and latency models."""
    xm = xm or ExecutionModel()
    lat = lat or LatencyModel()
    ex = KinematicExecutor(scenario, cfg, xm)
    events = sorted(scenario.events, key=lambda e: e.time)
    t_pub, i, call = 0.0, 0, 0
    while True:
        if call == 0:
            t_event = 0.0
        else:
            if i >= len(events):
                break
            t_event = events[i].time
        t_now = max(t_event, t_pub)
        ex.advance(t_now)
        first_event = i
        if call > 0:
            while i < len(events) and events[i].time <= t_now:
                ex.apply_event(events[i])
                i += 1
        P, old, locked = ex.snapshot(t_now)
        res = solve(method, P, old, budget_ms, cfg, seed=seed * 1000 + call, predictor=predictor, kappa=kappa,
                    **(solve_kwargs or {}))
        latency = lat.sample(scenario.seed, first_event if call > 0 else -1)
        t_pub = t_now + kappa * res["elapsed_ms"] / 1000.0 + latency
        ex.publish(P, res["solution"].routes, locked, t_pub)
        ex.replans.append({"call": call, "t_event": t_event, "t_now": t_now, "t_pub": t_pub, "latency_s": latency,
                           "elapsed_ms": res["elapsed_ms"], "iters": res["iters"], "stop": res["stop_reason"],
                           "J": res["J"], "n_open": P.N, "n_uav": P.M})
        call += 1
    m = ex.finish()
    lat_s = [r["latency_s"] for r in ex.replans]
    m.update({"scenario": scenario.name, "scale": scenario.scale, "profile": scenario.profile,
              "seed": scenario.seed, "method": method, "budget_ms": budget_ms, "kappa": kappa,
              "latency_level": lat.name, "latency_s_mean": float(np.mean(lat_s)) if lat_s else 0.0})
    if keep_log:
        m["_replans"] = ex.replans
        m["_executed"] = ex.executed
    return m
