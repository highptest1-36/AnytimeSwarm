#!/usr/bin/env python3
"""Mission manager + planner of a tier C mission (scenario timeline, replanning, metrics).

    python journal_ros/mission_manager.py --profile arrivals --seed 0 --method anytime --kappa-b 10 \
        --trigger event --out results/tier_c/run.json --ros-args -p use_sim_time:=true

Timeline (mission time = simulation time since every UAV hovers at its take-off point):
  * tasks are announced, UAVs fail and deadlines tighten exactly as in the scenario (tier B generator, rescaled)
  * a replanning call is triggered by an event, by a deviation of more than theta from the planned finish times,
    or periodically (trigger "event" | "deviation:<s>" | "periodic:<s>", <s> given in TIER B seconds and scaled)
  * the planner works on a snapshot built from /atswarm/fleet_state with the same semantics as the tier B executor
    (committed task folded into ready time / position / energy). During planning UAVs are told to HOLD.
  * the plan is released at  t_publish = t_snapshot + kappa_C * planning_ms / 1000, kappa_C = kappa_B * S_T
    (emulated on-board computer kappa_C times slower than this laptop; ROS 2 / DDS latency comes on top and is
    measured: plan release -> every UAV reports the new plan version)
  * service start / finish / skip come from the executor; reward only if the measured finish meets the deadline
Writes one JSON file with the tier B metric set plus timing, latency and calibration data, then exits.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import JOURNAL, S_T, gz_scenario, tier_c_config  # noqa: E402

import numpy as np  # noqa: E402
import rclpy  # noqa: E402
from rclpy.executors import ExternalShutdownException  # noqa: E402
from rclpy.node import Node  # noqa: E402
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy  # noqa: E402

from atswarm_interfaces.msg import FleetState, Plan, Route, Task, TaskArray, TaskReport, UavCommand, UavState  # noqa: E402
from journal_core.methods import solve  # noqa: E402
from journal_core.risk import ErrorModel  # noqa: E402

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.problem import Problem  # noqa: E402
from journal_core import ORIGINAL  # noqa: E402

REL_QOS = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     history=HistoryPolicy.KEEP_LAST, depth=10)


class Mission(Node):
    def __init__(self, a):
        super().__init__("atswarm_mission_manager")
        self.a = a
        self.cfg = tier_c_config()
        self.sc = gz_scenario(a.profile, a.seed)
        self.pred = LearnedPredictor.load(ORIGINAL / "models" / "improvement_model.json")
        self.kappa_c = a.kappa_b * S_T
        kind, _, par = a.trigger.partition(":")
        self.trig_kind, self.trig_par = kind, float(par) * S_T if par else 0.0
        self.err = ErrorModel()
        if a.error_model and Path(a.error_model).exists():
            self.err = ErrorModel.load_all(a.error_model).get(a.error_level, ErrorModel())
        self.tasks = {t.id: t for t in self.sc.tasks}
        self.deadline = {t.id: t.deadline for t in self.sc.tasks}
        self.announced = {t.id for t in self.sc.tasks if t.announce <= 0}
        self.events = sorted(self.sc.events, key=lambda e: e.time)
        self.ev_i = 0
        self.status = {j: Task.HIDDEN for j in self.tasks}
        self.served, self.late, self.finish_t = {}, set(), {}
        self.failed = set()
        self.assigned_to, self.reassign, self.dropped_by_delay, self.skips = {}, 0, 0, 0
        self.fleet = None
        self.t0 = None
        self.pending = None                          # (t_publish, Plan msg, publication bookkeeping)
        self.version, self.t_last_plan = 0, -1e9
        self.uav_plan, self.plan_lead = {}, {}        # deviation tracking, calibration
        self.replans, self.calib, self.accept_lat = [], [], []
        self.dist, self.last_xy = 0.0, {}
        self.queued_why, self.queued_t = None, None
        self.ended = False
        self.wall0 = self.sim0 = None
        self.pub_tasks = self.create_publisher(TaskArray, "/atswarm/tasks", 10)
        self.pub_plan = self.create_publisher(Plan, "/atswarm/plan", REL_QOS)
        self.pub_cmd = self.create_publisher(UavCommand, "/atswarm/command", REL_QOS)
        self.create_subscription(FleetState, "/atswarm/fleet_state", self.on_fleet, 10)
        self.create_subscription(TaskReport, "/atswarm/task_report", self.on_report, REL_QOS)
        self.create_timer(0.1, self.loop)
        self.create_timer(0.5, self.publish_tasks)
        self.get_logger().info(f"{self.sc.name}: method={a.method} budget={a.budget_ms:g} ms kappa_B={a.kappa_b:g} "
                               f"(kappa_C={self.kappa_c:g}) trigger={a.trigger}")

    # ------------------------------------------------------------------ time
    def sim(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def now(self):
        return self.sim() - self.t0 if self.t0 is not None else 0.0

    # ------------------------------------------------------------------ inputs
    def on_fleet(self, m):
        self.fleet = m
        if self.t0 is None:
            return
        for u in m.uavs:
            if u.alive and u.phase in (UavState.TRANSIT, UavState.SERVICE, UavState.IDLE):
                p = self.last_xy.get(u.id)
                if p is not None:
                    self.dist += math.hypot(u.x - p[0], u.y - p[1])
                self.last_xy[u.id] = (u.x, u.y)
        if self.accept_wait:
            ver, t_pub = self.accept_wait
            alive = [u for u in m.uavs if u.alive and u.id not in self.failed]
            if alive and all(u.plan_version >= ver for u in alive):
                self.accept_lat.append(self.now() - t_pub)
                self.accept_wait = None

    accept_wait = None

    def on_report(self, r):
        j, t = r.task_id, r.mission_time
        if r.kind == TaskReport.START:
            self.status[j] = Task.IN_SERVICE
        elif r.kind == TaskReport.FINISH:
            self.finish_t[j] = t
            if t <= self.deadline[j] + 1e-9:
                self.served[j] = t
                self.status[j] = Task.SERVED
            else:
                self.late.add(j)
                self.status[j] = Task.LATE
            if j in self.plan_lead:
                t_pub, p = self.plan_lead[j]
                self.calib.append((p - t_pub, t - p))
        elif r.kind == TaskReport.SKIP:
            self.skips += 1
            self.status[j] = Task.OPEN

    # ------------------------------------------------------------------ outputs
    def publish_tasks(self):
        m = TaskArray()
        m.stamp, m.mission_time = self.get_clock().now().to_msg(), self.now()
        for j in sorted(self.announced):
            t, s = self.tasks[j], self.status[j]
            if s in (Task.OPEN, Task.ASSIGNED) and self.t0 is not None and self.deadline[j] < self.now():
                s = self.status[j] = Task.MISSED
            m.tasks.append(Task(id=j, x=t.x, y=t.y, release=t.release, deadline=self.deadline[j], service=t.service,
                                reward=t.reward, status=s, uav=self.assigned_to.get(j, -1)))
        self.pub_tasks.publish(m)

    def command(self, kind, uav=0, t=0.0):
        c = UavCommand()
        c.kind, c.uav_id, c.mission_time = kind, int(uav), float(t)
        self.pub_cmd.publish(c)

    # ------------------------------------------------------------------ planning
    def snapshot(self, t):
        f = self.fleet
        uavs = [u for u in f.uavs if u.alive and u.id not in self.failed]
        locked = {u.id: (u.current_task if u.phase in (UavState.TRANSIT, UavState.SERVICE) and u.current_task >= 0
                         else None) for u in uavs}
        lk = {v for v in locked.values() if v is not None}
        open_ids = sorted(j for j in self.announced if j not in self.served and j not in self.late
                          and j not in lk and self.deadline[j] > t)
        start, ready, energy, speed, reserve = [], [], [], [], []
        su = {u.id: u for u in self.sc.uavs}
        for u in uavs:
            if locked[u.id] is not None:
                start.append((u.ready_x, u.ready_y))
                ready.append(max(u.ready_time, t))
                energy.append(u.ready_energy)
            else:
                start.append((u.x, u.y))
                ready.append(t)
                energy.append(u.energy)
            speed.append(su[u.id].speed)
            reserve.append(self.sc.world["reserve_frac"] * su[u.id].capacity)
        uloc = {u.id: k for k, u in enumerate(uavs)}
        lidx = {j: i for i, j in enumerate(open_ids)}
        prev = [uloc.get(self.assigned_to.get(j, -1), -1) for j in open_ids]
        T = [self.tasks[j] for j in open_ids]
        P = Problem(t, self.sc.depot, [u.id for u in uavs], start, ready, energy, speed, reserve, open_ids,
                    [(x.x, x.y) for x in T], [x.release for x in T], [self.deadline[x.id] for x in T],
                    [x.service for x in T], [x.reward for x in T], prev, self.cfg["objective"],
                    self.sc.world["hover_m_per_s"])
        old = [[lidx[j] for j, _p in self.uav_plan.get(u.id, []) if j in lidx] for u in uavs]
        return P, old, locked, uavs

    def plan(self, why, t_trig):
        t = self.now()
        P, old, locked, uavs = self.snapshot(t)
        if why in ("deviation", "periodic") and P.N == 0:
            self.t_last_plan = t
            # nothing to reassign: acknowledge the deviation (finished -> actual time, running -> now)
            self.uav_plan = {u: [(j, self.finish_t[j] if j in self.finish_t else max(p, t)) for j, p in pl]
                             for u, pl in self.uav_plan.items()}
            return
        self.command(UavCommand.HOLD, 0, t)
        a = self.a
        kw = {"err": self.err, "latency_mean_s": a.latency_mean_s} if a.method == "anytime_risk" else {}
        base, _, b = a.method.partition("@")
        budget = float(b) if b else a.budget_ms
        res = solve(base, P, old, budget, self.cfg, seed=a.seed * 1000 + len(self.replans), predictor=self.pred,
                    kappa=self.kappa_c, **kw)
        ms = res["elapsed_ms"]
        t_pub = t + self.kappa_c * ms / 1000.0
        self.version += 1
        msg = Plan()
        msg.version, msg.trigger, msg.method = self.version, why, a.method
        msg.t_trigger, msg.t_snapshot, msg.t_publish = float(t_trig), float(t), float(t_pub)
        msg.planning_ms, msg.iterations, msg.stop_reason = float(ms), int(res["iters"]), str(res["stop_reason"])
        msg.objective = float(res["J"])
        plan, lead = {}, {}
        for k, u in enumerate(uavs):
            entries, skipped, _, _ = P.schedule(k, res["solution"].routes[k], start_time=t_pub, skip_infeasible=True)
            self.dropped_by_delay += len(skipped)
            r = Route(uav_id=u.id, task_ids=[P.task_ids[j] for j, *_ in entries],
                      planned_finish=[float(e[4]) for e in entries])
            msg.routes.append(r)
            pl = [(locked[u.id], P.ready[k])] if locked[u.id] is not None else []
            for gid, fin in zip(r.task_ids, r.planned_finish):
                pl.append((gid, fin))
                lead[gid] = (t_pub, fin)
                if gid in self.assigned_to and self.assigned_to[gid] != u.id:
                    self.reassign += 1
                self.assigned_to[gid] = u.id
                if self.status[gid] == Task.OPEN:
                    self.status[gid] = Task.ASSIGNED
            plan[u.id] = pl
        self.pending = (t_pub, msg, plan, lead)
        self.replans.append({"call": len(self.replans), "why": why, "t_trigger": t_trig, "t_snapshot": t,
                             "t_publish": t_pub, "planning_ms": ms, "iters": res["iters"], "stop": res["stop_reason"],
                             "J": res["J"], "n_open": P.N, "n_uav": P.M})
        self.get_logger().info(f"replan #{len(self.replans) - 1} ({why}) t={t:.1f}s: {ms:.1f} ms, {res['iters']} it, "
                               f"stop={res['stop_reason']}, release at {t_pub:.2f}s, open={P.N}")

    def release(self):
        t_pub, msg, plan, lead = self.pending
        msg.stamp = self.get_clock().now().to_msg()
        self.pub_plan.publish(msg)
        self.uav_plan = plan
        self.plan_lead.update(lead)
        self.t_last_plan = msg.t_snapshot
        self.accept_wait = (msg.version, self.now())
        self.pending = None

    def deviation(self, t):
        th = self.trig_par
        for _u, pl in self.uav_plan.items():
            for j, p in pl:
                a = self.finish_t.get(j)
                if a is not None:
                    if p - a > th:
                        return True
                    if a - p > th:
                        continue                     # lateness already detected while it was in progress
                    continue
                if t > p + th:
                    return True
                break
        return False

    # ------------------------------------------------------------------ main loop
    def loop(self):
        if self.ended:
            return
        if self.t0 is None:
            f = self.fleet
            if f is not None and f.uavs and all(u.phase == UavState.IDLE for u in f.uavs):
                self.t0 = self.sim()
                self.wall0, self.sim0 = time.monotonic(), self.t0
                self.command(UavCommand.START, 0, self.t0)
                for j in self.announced:
                    self.status[j] = Task.OPEN
                self.get_logger().info("all UAVs airborne: mission starts")
                self.plan("start", 0.0)
            return
        t = self.now()
        if self.pending is not None:
            if t >= self.pending[0]:
                self.release()
            else:
                return
        why = None
        while self.ev_i < len(self.events) and self.events[self.ev_i].time <= t:
            e = self.events[self.ev_i]
            self.ev_i += 1
            why, t_trig = "event", e.time
            if e.kind == "arrival":
                for j in e.data["task_ids"]:
                    self.announced.add(j)
                    self.status[j] = Task.OPEN
            elif e.kind == "failure":
                u = e.data["uav_id"]
                self.failed.add(u)
                self.command(UavCommand.FAIL, u, t)
                for j, p in self.uav_plan.pop(u, []):
                    if self.status[j] in (Task.ASSIGNED, Task.IN_SERVICE):
                        self.status[j] = Task.OPEN
            elif e.kind == "deadline":
                j = e.data["task_id"]
                self.deadline[j] = min(self.deadline[j], e.data["new_deadline"])
        t_stop = max(self.deadline.values())
        if why is None and t < t_stop:
            if self.trig_kind == "deviation" and self.deviation(t):
                why, t_trig = "deviation", t
            elif self.trig_kind == "periodic" and t >= self.t_last_plan + self.trig_par:
                why, t_trig = "periodic", t
        if why is not None:
            self.plan(why, t_trig)
            return
        if self.done(t, t_stop):
            self.end(t)

    def done(self, t, t_stop):
        if t >= t_stop:
            return True
        if self.ev_i < len(self.events):
            return False
        live = [j for j in self.announced if j not in self.served and j not in self.late and self.deadline[j] > t]
        busy = self.fleet is not None and any(u.alive and u.phase in (UavState.TRANSIT, UavState.SERVICE)
                                              for u in self.fleet.uavs)
        return not live and not busy

    def end(self, t):
        self.ended = True
        self.command(UavCommand.END, 0, t)
        o = self.cfg["objective"]
        R_tot = sum(x.reward for x in self.sc.tasks)
        R = sum(self.tasks[j].reward for j in self.served)
        n = len(self.tasks)
        pm = np.array([r["planning_ms"] for r in self.replans]) if self.replans else np.zeros(1)
        wall = time.monotonic() - self.wall0
        m = {"scenario": self.sc.name, "profile": self.a.profile, "seed": self.a.seed, "method": self.a.method,
             "budget_ms": self.a.budget_ms, "kappa_b": self.a.kappa_b, "kappa_c": self.kappa_c,
             "trigger": self.a.trigger, "n_tasks": n, "served": len(self.served), "completion_rate": len(self.served) / n,
             "utility_rate": R / R_tot, "late_served": len(self.late), "dropped_by_delay": self.dropped_by_delay,
             "dropped_in_exec": self.skips, "reassignments": self.reassign, "distance_km": self.dist / 1000.0,
             "mission_J": o["alpha"] * R - o["gamma"] * self.dist / 1000.0 - o["delta"] * self.reassign,
             "n_replans": len(self.replans), "n_extra_replans": sum(r["why"] in ("deviation", "periodic")
                                                                     for r in self.replans),
             "plan_ms_mean": float(pm.mean()), "plan_ms_p95": float(np.percentile(pm, 95)),
             "accept_latency_s_mean": float(np.mean(self.accept_lat)) if self.accept_lat else float("nan"),
             "accept_latency_s_p95": float(np.percentile(self.accept_lat, 95)) if self.accept_lat else float("nan"),
             "mission_time_s": t, "wall_s": wall, "rtf": t / wall if wall > 0 else float("nan"),
             "finish_err_mean_s": float(np.mean([e for _h, e in self.calib])) if self.calib else 0.0,
             "finish_err_p95_s": float(np.percentile([e for _h, e in self.calib], 95)) if self.calib else 0.0,
             "_replans": self.replans, "_calib": self.calib, "_accept_latency_s": self.accept_lat,
             "_served": self.served, "_late": sorted(self.late)}
        out = Path(self.a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(m, indent=1, default=float))
        self.get_logger().info(f"MISSION END t={t:.1f}s utility={m['utility_rate']:.3f} served={m['served']}/{n} "
                               f"late={m['late_served']} replans={m['n_replans']} plan_ms={m['plan_ms_mean']:.1f} "
                               f"RTF={m['rtf']:.2f} -> {out}")
        self.create_timer(3.0, lambda: rclpy.try_shutdown())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="arrivals")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--method", default="anytime")
    ap.add_argument("--budget-ms", type=float, default=250.0)
    ap.add_argument("--kappa-b", type=float, default=10.0, help="tier B equivalent kappa (kappa_C = kappa_B * S_T)")
    ap.add_argument("--trigger", default="event", help="event | deviation:<tier B s> | periodic:<tier B s>")
    ap.add_argument("--error-model", default=str(JOURNAL / "models" / "error_model_tierc_dev.json"))
    ap.add_argument("--error-level", default="gz")
    ap.add_argument("--latency-mean-s", type=float, default=0.0)
    ap.add_argument("--out", default=str(JOURNAL / "results" / "tier_c" / "run.json"))
    args, ros_args = ap.parse_known_args()
    rclpy.init(args=[sys.argv[0]] + ros_args)
    node = Mission(args)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
