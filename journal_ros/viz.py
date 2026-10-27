#!/usr/bin/env python3
"""Visualisation of a tier C mission: RViz2 markers and task pillars inside the Gazebo 3D scene.

    python journal_ros/viz.py --ros-args -p use_sim_time:=true

RViz2 (/atswarm/markers, frame "world" = Gazebo ENU, depot at the origin)
  task cylinders, colour = status: orange open, yellow assigned, blue in service, green served on time,
  red served late, grey missed; height grows with the reward
  UAV spheres (one colour per UAV), current route as a line from the UAV through its planned tasks
  text: mission time, reward collected, last replanning call (trigger, CPU ms, stop reason)
Gazebo GUI: the same task pillars are drawn with the gz marker service (only when the Gazebo GUI is running; the
call fails silently in headless runs). Colour updates are sent only when a task changes status.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import map_to_gz  # noqa: E402

import rclpy  # noqa: E402
from geometry_msgs.msg import Point  # noqa: E402
from rclpy.executors import ExternalShutdownException  # noqa: E402
from rclpy.node import Node  # noqa: E402
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy  # noqa: E402
from std_msgs.msg import ColorRGBA  # noqa: E402
from visualization_msgs.msg import Marker, MarkerArray  # noqa: E402

from atswarm_interfaces.msg import FleetState, Plan, Task, TaskArray  # noqa: E402

REL_QOS = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     history=HistoryPolicy.KEEP_LAST, depth=10)
STATUS_RGB = {Task.OPEN: (1.0, 0.55, 0.0), Task.ASSIGNED: (1.0, 0.85, 0.1), Task.IN_SERVICE: (0.2, 0.45, 1.0),
              Task.SERVED: (0.15, 0.8, 0.2), Task.LATE: (0.9, 0.1, 0.1), Task.MISSED: (0.5, 0.5, 0.5)}
UAV_RGB = [(0.12, 0.47, 0.71), (1.0, 0.5, 0.05), (0.17, 0.63, 0.17), (0.84, 0.15, 0.16), (0.58, 0.4, 0.74)]
STATUS_NAME = {Task.OPEN: "open", Task.ASSIGNED: "assigned", Task.IN_SERVICE: "in service", Task.SERVED: "served",
               Task.LATE: "late", Task.MISSED: "missed"}


def rgba(c, a=1.0):
    return ColorRGBA(r=float(c[0]), g=float(c[1]), b=float(c[2]), a=float(a))


class Viz(Node):
    def __init__(self, depot):
        super().__init__("atswarm_viz")
        self.depot = depot
        self.tasks, self.fleet, self.plan, self.t = {}, None, None, 0.0
        self.gz_sent = {}
        self.pub = self.create_publisher(MarkerArray, "/atswarm/markers", 10)
        self.create_subscription(TaskArray, "/atswarm/tasks", self.on_tasks, 10)
        self.create_subscription(FleetState, "/atswarm/fleet_state", self.on_fleet, 10)
        self.create_subscription(Plan, "/atswarm/plan", self.on_plan, REL_QOS)
        self.create_timer(0.25, self.draw)

    def on_tasks(self, m):
        self.tasks = {t.id: t for t in m.tasks}
        self.t = m.mission_time
        for t in m.tasks:
            if self.gz_sent.get(t.id) != t.status:
                self.gz_marker(t)
                self.gz_sent[t.id] = t.status

    def on_fleet(self, m):
        self.fleet = m

    def on_plan(self, m):
        self.plan = m

    def gz_marker(self, t):
        x, y = map_to_gz(t.x, t.y, self.depot)
        r, g, b = STATUS_RGB.get(t.status, (1, 1, 1))
        h = 3.0 + 2.0 * t.reward
        req = (f'action: ADD_MODIFY, ns: "tasks", id: {t.id + 1}, type: CYLINDER, '
               f'pose: {{position: {{x: {x:.2f}, y: {y:.2f}, z: {h / 2:.2f}}}}}, scale: {{x: 4, y: 4, z: {h:.2f}}}, '
               f'material: {{ambient: {{r: {r}, g: {g}, b: {b}, a: 1}}, diffuse: {{r: {r}, g: {g}, b: {b}, a: 1}}}}')
        try:
            subprocess.Popen(["gz", "service", "-s", "/marker", "--reqtype", "gz.msgs.Marker", "--reptype",
                              "gz.msgs.Empty", "--timeout", "300", "--req", req],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

    def mk(self, ns, i, typ, frame="world"):
        m = Marker()
        m.header.frame_id, m.header.stamp = frame, self.get_clock().now().to_msg()
        m.ns, m.id, m.type, m.action = ns, i, typ, Marker.ADD
        m.pose.orientation.w = 1.0
        return m

    def draw(self):
        arr = MarkerArray()
        d = self.mk("depot", 0, Marker.CUBE)
        d.scale.x = d.scale.y = d.scale.z = 6.0
        d.color = rgba((0.1, 0.1, 0.1))
        arr.markers.append(d)
        reward = total = 0.0
        for t in self.tasks.values():
            x, y = map_to_gz(t.x, t.y, self.depot)
            h = 3.0 + 2.0 * t.reward
            c = self.mk("tasks", t.id, Marker.CYLINDER)
            c.pose.position.x, c.pose.position.y, c.pose.position.z = x, y, h / 2
            c.scale.x, c.scale.y, c.scale.z = 8.0, 8.0, h
            c.color = rgba(STATUS_RGB.get(t.status, (1, 1, 1)), 0.9)
            arr.markers.append(c)
            total += t.reward
            if t.status == Task.SERVED:
                reward += t.reward
        uav_pos = {}
        if self.fleet is not None:
            for u in self.fleet.uavs:
                x, y = map_to_gz(u.x, u.y, self.depot)
                uav_pos[u.id] = (x, y, u.z)
                s = self.mk("uavs", u.id, Marker.SPHERE)
                s.pose.position.x, s.pose.position.y, s.pose.position.z = x, y, u.z
                s.scale.x = s.scale.y = s.scale.z = 10.0
                s.color = rgba(UAV_RGB[u.id % len(UAV_RGB)] if u.alive else (0, 0, 0))
                arr.markers.append(s)
                lab = self.mk("uav_labels", u.id, Marker.TEXT_VIEW_FACING)
                lab.pose.position.x, lab.pose.position.y, lab.pose.position.z = x, y, u.z + 14.0
                lab.scale.z = 9.0
                lab.color = rgba((0, 0, 0))
                lab.text = f"UAV {u.id}" + ("" if u.alive else " (failed)")
                arr.markers.append(lab)
        if self.plan is not None:
            for r in self.plan.routes:
                line = self.mk("routes", r.uav_id, Marker.LINE_STRIP)
                line.scale.x = 2.0
                line.color = rgba(UAV_RGB[r.uav_id % len(UAV_RGB)], 0.8)
                pts = [uav_pos.get(r.uav_id)] if r.uav_id in uav_pos else []
                for j in r.task_ids:
                    t = self.tasks.get(j)
                    if t is not None and t.status in (Task.ASSIGNED, Task.OPEN, Task.IN_SERVICE):
                        x, y = map_to_gz(t.x, t.y, self.depot)
                        pts.append((x, y, 3.0))
                line.points = [Point(x=float(p[0]), y=float(p[1]), z=float(p[2])) for p in pts if p is not None]
                if len(line.points) < 2:
                    line.action = Marker.DELETE
                arr.markers.append(line)
        hud = self.mk("hud", 0, Marker.TEXT_VIEW_FACING)
        hud.pose.position.x, hud.pose.position.y, hud.pose.position.z = 0.0, 560.0, 60.0
        hud.scale.z = 22.0
        hud.color = rgba((0, 0, 0))
        lines = [f"t = {self.t:6.1f} s   reward {reward:.0f}/{total:.0f}"]
        if self.plan is not None:
            p = self.plan
            lines.append(f"plan v{p.version} ({p.trigger}) {p.method}: {p.planning_ms:.1f} ms, "
                         f"{p.iterations} it, stop={p.stop_reason}")
        hud.text = "\n".join(lines)
        arr.markers.append(hud)
        self.pub.publish(arr)


def main():
    import argparse
    from common import gz_scenario
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="arrivals")
    ap.add_argument("--seed", type=int, default=0)
    args, ros_args = ap.parse_known_args()
    rclpy.init(args=[sys.argv[0]] + ros_args)
    node = Viz(gz_scenario(args.profile, args.seed).depot)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
