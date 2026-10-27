#!/usr/bin/env python3
"""Route executor for every PX4 SITL vehicle of a tier C mission (one ROS 2 node, one state machine per UAV).

    python journal_ros/uav_executor.py --profile arrivals --seed 0 --ros-args -p use_sim_time:=true

Per UAV, at 10 Hz of simulation time: stream OffboardControlMode + TrajectorySetpoint (PX4 leaves Offboard below
about 2 Hz), arm and take off, then fly the task queue received in /atswarm/plan:
    TRANSIT  a carrot moves along the straight leg at the UAV's scenario cruise speed (velocity feed-forward);
             the task is reached when the measured position is within ACCEPT_RADIUS_M of it
    SERVICE  hover at the task until max(arrival, release) + nominal service time
Execution semantics are those of tier B: the committed task (being flown to or served) is never changed by a new
plan; while the planner works (UavCommand HOLD) a UAV finishes its current task and then waits; at departure a task
whose nominal finish estimate already misses its deadline is skipped (TaskReport SKIP).
Publishes /atswarm/fleet_state (5 Hz) with measured state and the planner's nominal estimate of when / where / with
which energy each UAV becomes free, and /atswarm/task_report (service start / finish / skip).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ACCEPT_RADIUS_M, altitude, gz_scenario, spawn_xy  # noqa: E402

import rclpy  # noqa: E402
from rclpy.executors import ExternalShutdownException  # noqa: E402
from rclpy.node import Node  # noqa: E402
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy  # noqa: E402

from atswarm_interfaces.msg import FleetState, Plan, TaskArray, TaskReport, UavCommand, UavState  # noqa: E402
from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint, VehicleCommand,  # noqa: E402
                          VehicleLocalPosition, VehicleStatus)

PX4_QOS = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     history=HistoryPolicy.KEEP_LAST, depth=1)
REL_QOS = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     history=HistoryPolicy.KEEP_LAST, depth=10)


class Vehicle:
    def __init__(self, node, k, n, uav, depot, hover):
        self.k, self.uav, self.node = k, uav, node
        self.depot, self.hover = depot, hover
        ns = f"/px4_{k + 1}"
        self.pub_mode = node.create_publisher(OffboardControlMode, f"{ns}/fmu/in/offboard_control_mode", PX4_QOS)
        self.pub_sp = node.create_publisher(TrajectorySetpoint, f"{ns}/fmu/in/trajectory_setpoint", PX4_QOS)
        self.pub_cmd = node.create_publisher(VehicleCommand, f"{ns}/fmu/in/vehicle_command", PX4_QOS)
        node.create_subscription(VehicleLocalPosition, f"{ns}/fmu/out/vehicle_local_position_v1", self.on_pos, PX4_QOS)
        node.create_subscription(VehicleStatus, f"{ns}/fmu/out/vehicle_status_v1", self.on_status, PX4_QOS)
        self.spawn_e, self.spawn_n = spawn_xy(k, n)
        self.alt = altitude(k)
        self.speed = uav.speed
        self.energy = uav.capacity
        self.pos = self.status = None
        self.phase, self.alive, self.ticks = UavState.INIT, True, 0
        self.queue, self.task = [], None          # remaining task ids, current task id
        self.carrot = None                         # NED (north, east)
        self.svc_start = None
        self.plan_version = 0
        self.last_xy = None
        self.landing = False

    # ------------------------------------------------------------------ frames
    def ned_of_map(self, x, y):
        return y - self.depot[1] - self.spawn_n, x - self.depot[0] - self.spawn_e

    def map_xy(self):
        if self.pos is None:
            return self.depot[0] + self.spawn_e, self.depot[1] + self.spawn_n
        return self.depot[0] + self.spawn_e + self.pos.y, self.depot[1] + self.spawn_n + self.pos.x

    def on_pos(self, m):
        self.pos = m

    def on_status(self, m):
        self.status = m

    # ------------------------------------------------------------------ PX4 commands
    def command(self, cmd, p1=0.0, p2=0.0):
        m = VehicleCommand()
        m.command, m.param1, m.param2 = cmd, float(p1), float(p2)
        m.target_system = self.status.system_id if self.status else self.k + 2
        m.target_component, m.source_system, m.source_component, m.from_external = 1, 1, 1, True
        m.timestamp = self.node.px4_time()
        self.pub_cmd.publish(m)

    def setpoint(self, n, e, vn=float("nan"), ve=float("nan")):
        mode = OffboardControlMode()
        mode.position, mode.timestamp = True, self.node.px4_time()
        self.pub_mode.publish(mode)
        sp = TrajectorySetpoint()
        sp.position = [float(n), float(e), -float(self.alt)]
        sp.velocity = [float(vn), float(ve), float("nan")]
        sp.yaw = float("nan")
        sp.timestamp = self.node.px4_time()
        self.pub_sp.publish(sp)

    # ------------------------------------------------------------------ estimates for the planner
    def estimate(self, now):
        """(ready time, ready x, ready y, ready energy) as the planner's nominal model sees this UAV at `now`."""
        x, y = self.map_xy()
        if self.task is None or self.phase not in (UavState.TRANSIT, UavState.SERVICE):
            return now, x, y, self.energy
        t = self.node.tasks[self.task]
        if self.phase == UavState.TRANSIT:
            rem = math.hypot(t.x - x, t.y - y)
            fin = max(now + rem / self.speed, t.release) + t.service
            return fin, t.x, t.y, self.energy - rem - self.hover * t.service
        fin = max(self.svc_start + t.service, now)
        return fin, t.x, t.y, self.energy - self.hover * max(0.0, fin - max(now, self.svc_start))

    # ------------------------------------------------------------------ state machine
    def tick(self, now, dt):
        if self.landing:
            return
        if self.pos is not None:
            xy = self.map_xy()
            if self.last_xy is not None and self.phase in (UavState.TRANSIT, UavState.IDLE, UavState.SERVICE):
                self.energy -= math.hypot(xy[0] - self.last_xy[0], xy[1] - self.last_xy[1])
            self.last_xy = xy
        self.ticks += 1
        if self.phase == UavState.INIT:
            self.setpoint(0.0, 0.0)
            if self.ticks >= 10 and self.ticks % 20 == 10 and (self.status is None or
                                                               self.status.arming_state != VehicleStatus.ARMING_STATE_ARMED):
                self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1, 6)
                self.command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1)
            if self.status is not None and self.status.arming_state == VehicleStatus.ARMING_STATE_ARMED:
                self.phase = UavState.TAKEOFF
            return
        if self.phase == UavState.TAKEOFF:
            self.setpoint(0.0, 0.0)
            if self.pos is not None and abs(-self.pos.z - self.alt) < 0.7:
                self.phase = UavState.IDLE
                self.carrot = (self.pos.x, self.pos.y)
            return
        if self.phase == UavState.IDLE:
            if self.node.started and not self.node.hold:
                self.next_task(now)
            if self.phase == UavState.IDLE:
                self.setpoint(*self.carrot)
                return
        if self.phase == UavState.TRANSIT:
            t = self.node.tasks[self.task]
            tn, te = self.ned_of_map(t.x, t.y)
            cn, ce = self.carrot
            dn, de = tn - cn, te - ce
            d = math.hypot(dn, de)
            step = self.speed * dt
            if d <= step:
                self.carrot, vn, ve = (tn, te), 0.0, 0.0
            else:
                self.carrot = (cn + dn / d * step, ce + de / d * step)
                vn, ve = dn / d * self.speed, de / d * self.speed
            self.setpoint(*self.carrot, vn, ve)
            if self.pos is not None and self.carrot == (tn, te) and \
                    math.hypot(self.pos.x - tn, self.pos.y - te) < ACCEPT_RADIUS_M:
                self.phase = UavState.SERVICE
                self.svc_start = max(now, t.release)
                self.started_report = False
            return
        if self.phase == UavState.SERVICE:
            t = self.node.tasks[self.task]
            self.setpoint(*self.carrot)
            if not self.started_report and now >= self.svc_start:
                self.node.report(self.task, self.k, TaskReport.START, self.svc_start)
                self.started_report = True
            if self.started_report:
                self.energy -= self.hover * dt
            if now >= self.svc_start + t.service:
                self.node.report(self.task, self.k, TaskReport.FINISH, now)
                self.task, self.phase = None, UavState.IDLE
                if not self.node.hold:
                    self.next_task(now)
                if self.phase == UavState.IDLE:
                    self.carrot = (self.pos.x, self.pos.y) if self.pos is not None else self.carrot
            return

    def next_task(self, now):
        x, y = self.map_xy()
        while self.queue:
            j = self.queue.pop(0)
            t = self.node.tasks.get(j)
            if t is None or j in self.node.done:
                continue
            est = max(now + math.hypot(t.x - x, t.y - y) / self.speed, t.release) + t.service
            if est > t.deadline:
                self.node.report(j, self.k, TaskReport.SKIP, now)
                continue
            self.task, self.phase = j, UavState.TRANSIT
            if self.pos is not None:
                self.carrot = (self.pos.x, self.pos.y)
            return

    def accept(self, route, version):
        if not self.alive:
            return
        self.queue = [j for j in route if j != self.task]
        self.plan_version = version

    def fail(self):
        self.alive, self.phase, self.queue, self.task = False, UavState.FAILED, [], None
        self.command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.landing = True

    def land(self):
        if self.alive and not self.landing:
            self.command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            self.landing = True

    def state(self, now):
        s = UavState()
        s.id, s.phase, s.alive = self.uav.id, self.phase, self.alive
        s.x, s.y = self.map_xy()
        s.z = -self.pos.z if self.pos is not None else 0.0
        s.speed = math.hypot(self.pos.vx, self.pos.vy) if self.pos is not None else 0.0
        s.energy = self.energy
        s.current_task = self.task if self.task is not None else -1
        s.ready_time, s.ready_x, s.ready_y, s.ready_energy = self.estimate(now)
        s.plan_version = self.plan_version
        return s


class Executor(Node):
    def __init__(self, profile, seed):
        super().__init__("atswarm_uav_executor")
        self.sc = gz_scenario(profile, seed)
        n = len(self.sc.uavs)
        self.tasks, self.done = {}, set()
        self.started, self.hold, self.t0 = False, False, None
        hover = self.sc.world["hover_m_per_s"]
        self.v = [Vehicle(self, k, n, u, self.sc.depot, hover) for k, u in enumerate(self.sc.uavs)]
        self.pub_state = self.create_publisher(FleetState, "/atswarm/fleet_state", 10)
        self.pub_report = self.create_publisher(TaskReport, "/atswarm/task_report", REL_QOS)
        self.create_subscription(TaskArray, "/atswarm/tasks", self.on_tasks, 10)
        self.create_subscription(Plan, "/atswarm/plan", self.on_plan, REL_QOS)
        self.create_subscription(UavCommand, "/atswarm/command", self.on_command, REL_QOS)
        self.last = None
        self.create_timer(0.1, self.tick)
        self.create_timer(0.2, self.publish_state)
        self.get_logger().info(f"{self.sc.name}: {n} UAVs, executor ready")

    def px4_time(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def now(self):
        t = self.get_clock().now().nanoseconds * 1e-9
        return t - self.t0 if self.t0 is not None else 0.0

    def on_tasks(self, m):
        for t in m.tasks:
            self.tasks[t.id] = t

    def on_plan(self, m):
        self.hold = False
        for r in m.routes:
            if r.uav_id < len(self.v):
                self.v[r.uav_id].accept(list(r.task_ids), m.version)

    def on_command(self, m):
        if m.kind == UavCommand.START:
            self.t0, self.started = m.mission_time, True
            self.get_logger().info("mission clock started")
        elif m.kind == UavCommand.HOLD:
            self.hold = True
        elif m.kind == UavCommand.FAIL and m.uav_id < len(self.v):
            self.v[m.uav_id].fail()
            self.get_logger().info(f"UAV {m.uav_id} failed (injected)")
        elif m.kind == UavCommand.END:
            for v in self.v:
                v.land()
            self.get_logger().info("mission over: landing")

    def report(self, task, uav, kind, t):
        r = TaskReport()
        r.task_id, r.uav_id, r.kind, r.mission_time = int(task), int(uav), kind, float(t)
        self.pub_report.publish(r)
        if kind in (TaskReport.FINISH, TaskReport.SKIP):
            if kind == TaskReport.FINISH:
                self.done.add(task)

    def tick(self):
        t = self.get_clock().now().nanoseconds * 1e-9
        dt = 0.1 if self.last is None else max(0.0, min(t - self.last, 0.5))
        self.last = t
        now = self.now()
        for v in self.v:
            v.tick(now, dt)

    def publish_state(self):
        m = FleetState()
        m.stamp = self.get_clock().now().to_msg()
        m.mission_time, m.mission_started = self.now(), self.started
        m.uavs = [v.state(self.now()) for v in self.v]
        self.pub_state.publish(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="arrivals")
    ap.add_argument("--seed", type=int, default=0)
    args, ros_args = ap.parse_known_args()
    rclpy.init(args=[sys.argv[0]] + ros_args)
    node = Executor(args.profile, args.seed)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
