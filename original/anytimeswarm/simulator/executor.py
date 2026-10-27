"""Closed-loop mission execution (discrete-event).

Semantics (state them in the paper):
  * Event at time t_e -> the planner is called on a snapshot at t_now = max(t_e, last publish time)
    (events arriving while the planner is busy are queued).
  * Commit horizon = 1 task: a UAV that is travelling to / serving a task keeps it ("locked").
  * Planning takes Delta ms of wall-clock time; the plan is published at t_pub = t_now + kappa*Delta.
    Until then UAVs only finish their locked task and then wait - this is where slow planning costs.
  * At publication every route is re-timed from the real state; tasks that became infeasible
    (deadline or energy) are skipped and return to the open pool ("dropped by delay").
  * A UAV failure removes the UAV; its locked and planned tasks return to the open pool.
  * A deadline change tightens d_j; serving after the new deadline earns nothing (= deadline miss).
"""
from __future__ import annotations

import copy

import numpy as np

from ..algorithms.methods import solve
from .problem import Problem


class MissionExecutor:
    def __init__(self, scenario, cfg: dict):
        self.sc, self.cfg = scenario, cfg
        w = scenario.world
        self.hover, self.reserve_frac = w["hover_m_per_s"], w["reserve_frac"]
        self.tasks = {t.id: copy.copy(t) for t in scenario.tasks}
        self.announced = {t.id for t in scenario.tasks if t.announce <= 0}
        self.served: dict[int, float] = {}         # task -> finish time
        self.late: set[int] = set()                 # served after (tightened) deadline
        self.uav = {}
        for u in scenario.uavs:
            self.uav[u.id] = {"x": u.x, "y": u.y, "speed": u.speed, "cap": u.capacity, "energy": u.capacity,
                              "ready": 0.0, "alive": True, "sched": [], "dist": 0.0}
        self.assigned_to: dict[int, int] = {}
        self.promised: set[int] = set()
        self.reassign = 0
        self.dropped_by_delay = 0
        self.executed = []                          # (uav, task, depart, start, finish)
        self.replans = []

    # ------------------------------------------------------------------ state evolution
    def advance(self, t: float) -> None:
        for uid, u in self.uav.items():
            if not u["alive"]:
                continue
            keep = []
            for e in u["sched"]:
                j, dep, arr, start, fin, leg, e_after = e
                if fin <= t:
                    task = self.tasks[j]
                    u["x"], u["y"], u["energy"], u["ready"] = task.x, task.y, e_after, fin
                    u["dist"] += leg
                    if fin <= task.deadline + 1e-9:
                        self.served[j] = fin
                    else:
                        self.late.add(j)
                    self.executed.append((uid, j, dep, start, fin))
                else:
                    keep.append(e)
            u["sched"] = keep

    def _locked(self, u, t):
        return u["sched"][0] if u["sched"] and u["sched"][0][1] <= t else None

    def apply_event(self, ev) -> None:
        if ev.kind == "arrival":
            self.announced.update(ev.data["task_ids"])
        elif ev.kind == "failure":
            u = self.uav[ev.data["uav_id"]]
            if u["alive"]:
                u["alive"] = False
                u["sched"] = []
        elif ev.kind == "deadline":
            j = ev.data["task_id"]
            self.tasks[j].deadline = min(self.tasks[j].deadline, ev.data["new_deadline"])

    # ------------------------------------------------------------------ planning interface
    def snapshot(self, t: float):
        uids = [uid for uid, u in self.uav.items() if u["alive"]]
        locked = {uid: self._locked(self.uav[uid], t) for uid in uids}
        locked_tasks = {e[0] for e in locked.values() if e}
        open_ids = sorted(j for j in self.announced if j not in self.served and j not in self.late
                          and j not in locked_tasks and self.tasks[j].deadline > t)
        start_xy, ready, energy, speed, reserve = [], [], [], [], []
        for uid in uids:
            u, e = self.uav[uid], locked[uid]
            if e:
                task = self.tasks[e[0]]
                start_xy.append((task.x, task.y))
                ready.append(e[4])
                energy.append(e[6])
            else:
                start_xy.append((u["x"], u["y"]))
                ready.append(max(t, u["ready"]))
                energy.append(u["energy"])
            speed.append(u["speed"])
            reserve.append(self.reserve_frac * u["cap"])
        lidx = {j: i for i, j in enumerate(open_ids)}
        uloc = {uid: k for k, uid in enumerate(uids)}
        prev = [uloc.get(self.assigned_to.get(j, -1), -1) for j in open_ids]
        T = [self.tasks[j] for j in open_ids]
        P = Problem(t, self.sc.depot, uids, start_xy, ready, energy, speed, reserve, open_ids,
                    [(x.x, x.y) for x in T], [x.release for x in T], [x.deadline for x in T],
                    [x.service for x in T], [x.reward for x in T], prev, self.sc.objective, self.hover)
        old_routes = []
        for uid in uids:
            sched = self.uav[uid]["sched"]
            rest = sched[1:] if locked[uid] else sched
            old_routes.append([lidx[e[0]] for e in rest if e[0] in lidx])
        return P, old_routes, locked

    def publish(self, P: Problem, routes, locked, t_pub: float) -> None:
        for k, uid in enumerate(P.uav_ids):
            u = self.uav[uid]
            entries, skipped, _, _ = P.schedule(k, routes[k], start_time=t_pub, skip_infeasible=True)
            self.dropped_by_delay += len(skipped)
            prev_xy = tuple(P.start_xy[k])
            e_now = P.energy[k]
            new = [locked[uid]] if locked[uid] else []
            for j, dep, arr, start, fin in entries:
                task_xy = tuple(P.task_xy[j])
                leg = float(np.hypot(task_xy[0] - prev_xy[0], task_xy[1] - prev_xy[1]))
                e_now -= leg + P.hover * P.sv[j]
                gid = P.task_ids[j]
                new.append((gid, dep, arr, start, fin, leg, e_now))
                if gid in self.assigned_to and self.assigned_to[gid] != uid:
                    self.reassign += 1
                self.assigned_to[gid] = uid
                self.promised.add(gid)
                prev_xy = task_xy
            u["sched"] = new
            if not locked[uid]:
                u["ready"] = max(u["ready"], t_pub)

    # ------------------------------------------------------------------ metrics
    def finish(self) -> dict:
        self.advance(float("inf"))
        # return-to-depot distance for reporting
        for u in self.uav.values():
            if u["alive"]:
                u["dist"] += float(np.hypot(u["x"] - self.sc.depot[0], u["y"] - self.sc.depot[1]))
        all_ids = [t.id for t in self.sc.tasks]
        R_tot = sum(self.tasks[j].reward for j in all_ids)
        R_srv = sum(self.tasks[j].reward for j in self.served)
        dist_km = sum(u["dist"] for u in self.uav.values()) / 1000.0
        missed = [j for j in all_ids if j not in self.served]
        o = self.sc.objective
        plan_ms = np.array([r["elapsed_ms"] for r in self.replans]) if self.replans else np.zeros(1)
        return {
            "n_tasks": len(all_ids), "served": len(self.served),
            "completion_rate": len(self.served) / len(all_ids),
            "utility_rate": R_srv / R_tot,
            "deadline_miss_rate": len(missed) / len(all_ids),
            "promised_missed": len([j for j in missed if j in self.promised]),
            "late_served": len(self.late),
            "dropped_by_delay": self.dropped_by_delay,
            "reassignments": self.reassign,
            "distance_km": dist_km,
            "mission_J": o["alpha"] * R_srv - o["gamma"] * dist_km - o["delta"] * self.reassign,
            "n_replans": len(self.replans),
            "plan_ms_mean": float(plan_ms.mean()), "plan_ms_p95": float(np.percentile(plan_ms, 95)),
            "plan_ms_total": float(plan_ms.sum()),
            "response_s_mean": float(np.mean([r["t_pub"] - r["t_event"] for r in self.replans])) if self.replans else 0.0,
        }


def run_mission(scenario, cfg: dict, method: str, budget_ms: float, kappa: float = 1.0,
                predictor=None, seed: int = 0, keep_log: bool = False, snapshot_hook=None,
                solve_kwargs: dict | None = None) -> dict:
    """snapshot_hook(P, old_routes, call, t_now) is called before each planning call (used to build
    the static snapshot benchmark)."""
    ex = MissionExecutor(scenario, cfg)
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
        if call > 0:
            while i < len(events) and events[i].time <= t_now:
                ex.apply_event(events[i])
                i += 1
        P, old, locked = ex.snapshot(t_now)
        if snapshot_hook is not None:
            snapshot_hook(P, old, call, t_now)
        res = solve(method, P, old, budget_ms, cfg, seed=seed * 1000 + call, predictor=predictor, kappa=kappa,
                    **(solve_kwargs or {}))
        t_pub = t_now + kappa * res["elapsed_ms"] / 1000.0
        ex.publish(P, res["solution"].routes, locked, t_pub)
        ex.replans.append({"call": call, "t_event": t_event, "t_now": t_now, "t_pub": t_pub,
                           "elapsed_ms": res["elapsed_ms"], "iters": res["iters"], "stop": res["stop_reason"],
                           "J": res["J"], "n_open": P.N, "n_uav": P.M})
        call += 1
    m = ex.finish()
    m.update({"scenario": scenario.name, "scale": scenario.scale, "profile": scenario.profile,
              "seed": scenario.seed, "method": method, "budget_ms": budget_ms, "kappa": kappa})
    if keep_log:
        m["_replans"] = ex.replans
        m["_executed"] = ex.executed
    return m
