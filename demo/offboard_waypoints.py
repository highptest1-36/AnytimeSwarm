#!/usr/bin/env python3
"""Fly one PX4 SITL vehicle through a list of waypoints with ROS 2 Offboard control.

This is the hand-run demo for gate G2 and the seed of atswarm_px4_adapter. It shows the three things every
AnytimeSwarm executor must do:
  1. stream OffboardControlMode + TrajectorySetpoint at 10 Hz (PX4 drops Offboard below ~2 Hz),
  2. switch to Offboard and arm with VehicleCommand (target_system = the vehicle's MAVLink system id),
  3. read VehicleLocalPosition to decide when a waypoint (task) is reached, hold for the service time, go on.

Frames: PX4 works in local NED (x = North, y = East, z = Down, origin = the vehicle's spawn point).
Gazebo/ROS use ENU (x = East, y = North, z = Up). Waypoints here are given in a shared WORLD frame
"North,East,Up" in metres; --spawn gives the vehicle's Gazebo spawn pose "x_east,y_north" (PX4_GZ_MODEL_POSE),
so that several vehicles can fly to the same world coordinates.

Examples
  python3 offboard_waypoints.py                                  # instance 0, topics /fmu/...
  python3 offboard_waypoints.py --ns /px4_1 --spawn 0,0
  python3 offboard_waypoints.py --ns /px4_2 --spawn 0,5 --wps "20,0,8;20,20,8;0,20,8"
"""
import argparse
import math
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition,
                          VehicleStatus)


class WaypointFlyer(Node):
    def __init__(self, ns, waypoints, spawn, hold_s, accept_m):
        super().__init__("offboard_waypoints" + ns.replace("/", "_"))
        # PX4 publishes with best-effort QoS; a reliable subscriber would never receive anything
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        self.pub_mode = self.create_publisher(OffboardControlMode, f"{ns}/fmu/in/offboard_control_mode", qos)
        self.pub_sp = self.create_publisher(TrajectorySetpoint, f"{ns}/fmu/in/trajectory_setpoint", qos)
        self.pub_cmd = self.create_publisher(VehicleCommand, f"{ns}/fmu/in/vehicle_command", qos)
        # PX4 1.17 appends the message version to some topic names (_v1)
        self.create_subscription(VehicleLocalPosition, f"{ns}/fmu/out/vehicle_local_position_v1", self.on_pos, qos)
        self.create_subscription(VehicleStatus, f"{ns}/fmu/out/vehicle_status_v1", self.on_status, qos)

        # world (North, East, Up) -> this vehicle's local NED
        spawn_east, spawn_north = spawn
        self.wps = [(n - spawn_north, e - spawn_east, -u) for n, e, u in waypoints]
        self.hold_s, self.accept_m = hold_s, accept_m
        self.pos, self.status = None, None
        self.k, self.ticks, self.hold_until, self.landing, self.done = 0, 0, None, False, False
        self.t0 = time.monotonic()
        self.create_timer(0.1, self.tick)                      # 10 Hz control loop

    def on_pos(self, msg):
        self.pos = msg

    def on_status(self, msg):
        self.status = msg

    def now_us(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def command(self, cmd, p1=0.0, p2=0.0):
        m = VehicleCommand()
        m.command, m.param1, m.param2 = cmd, float(p1), float(p2)
        sysid = self.status.system_id if self.status else 1    # instance N has MAVLink system id N + 1
        m.target_system, m.target_component = sysid, 1
        m.source_system, m.source_component, m.from_external = 1, 1, True
        m.timestamp = self.now_us()
        self.pub_cmd.publish(m)

    def log(self, text):
        self.get_logger().info(f"[t={time.monotonic() - self.t0:6.1f}s] {text}")

    def tick(self):
        mode = OffboardControlMode()
        mode.position, mode.timestamp = True, self.now_us()
        self.pub_mode.publish(mode)                            # heartbeat: must never stop while in Offboard
        if self.landing:
            if self.status and self.status.arming_state != VehicleStatus.ARMING_STATE_ARMED and not self.done:
                self.done = True
                self.log("landed and disarmed")
            return

        target = self.wps[self.k]
        sp = TrajectorySetpoint()
        sp.position = [float(v) for v in target]
        sp.yaw = float("nan")                                  # keep current heading
        sp.timestamp = self.now_us()
        self.pub_sp.publish(sp)

        self.ticks += 1
        if self.ticks == 10:                                   # PX4 needs setpoints BEFORE accepting Offboard
            self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1, 6)   # custom mode 6 = Offboard
            self.command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1)
            self.log("Offboard + arm requested")
        if self.status and self.ticks % 50 == 0 and self.status.arming_state != VehicleStatus.ARMING_STATE_ARMED:
            self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1, 6)   # retry until EKF is ready
            self.command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1)
            self.log("not armed yet, retrying")
        if self.pos is None or not self.pos.xy_valid:
            return

        d = math.dist((self.pos.x, self.pos.y, self.pos.z), target)
        if self.hold_until is None and d < self.accept_m:
            self.hold_until = time.monotonic() + self.hold_s
            self.log(f"reached waypoint {self.k} NED=({target[0]:.1f},{target[1]:.1f},{target[2]:.1f}), "
                     f"holding {self.hold_s:.0f}s (service)")
        if self.hold_until is not None and time.monotonic() >= self.hold_until:
            self.hold_until = None
            self.k += 1
            if self.k == len(self.wps):
                self.command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
                self.landing = True
                self.log("route finished -> LAND")
                return
            self.log(f"-> waypoint {self.k}")


def parse_wps(text):
    return [tuple(float(v) for v in p.split(",")) for p in text.split(";") if p.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ns", default="", help="topic namespace, '' for instance 0, '/px4_1' for instance 1 ...")
    ap.add_argument("--wps", default="0,0,5;15,0,5;15,15,5;0,15,5;0,0,5",
                    help="world waypoints 'north,east,up;...' in metres (first one = take-off point)")
    ap.add_argument("--spawn", default="0,0", help="Gazebo spawn pose 'x_east,y_north' (PX4_GZ_MODEL_POSE)")
    ap.add_argument("--hold", type=float, default=3.0, help="hold time at each waypoint (service), s")
    ap.add_argument("--accept", type=float, default=0.8, help="acceptance radius, m")
    a = ap.parse_args()
    rclpy.init()
    node = WaypointFlyer(a.ns, parse_wps(a.wps), parse_wps(a.spawn)[0], a.hold, a.accept)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
