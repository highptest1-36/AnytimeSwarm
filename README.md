# AnytimeSwarm Journal

Journal extension of AnytimeSwarm (deadline-aware adaptive computation for dynamic multi-UAV task replanning):
execution-aware validation with a continuous-time kinematic simulator (tier B) and PX4 SITL + Gazebo Harmonic +
ROS 2 Jazzy (tier C). The conference code in `D:\paper\TAIMMA_2027\AnytimeSwarm` is never modified.

| Folder | Content |
|---|---|
| `docs/00_JOURNAL_PLAN.md` | plan, decisions D1–D7, gates G0–G6, risks |
| `docs/01_HUONG_DAN_THUC_HANH.md` | hands-on guide: run ROS 2 / PX4 / Gazebo by hand and watch UAVs fly |
| `docs/02_REPRODUCTION.md` | G0 report: conference results reproduced on Linux |
| `setup/` | install scripts 01–05 (WSL Ubuntu 24.04 on D:), smoke / demo tests, logs |
| `original/` | frozen copy of the conference code, configs and predictor + `MANIFEST.sha256` |
| `repro/` | working copy used to re-run the conference pipeline on Linux (G0) |
| `journal_core/` | journal extensions (kinematic executor, latency models, new baselines) |
| `demo/` | `offboard_waypoints.py`: ROS 2 Offboard waypoint flight for one PX4 vehicle |
| `tools/` | environment manifest, RAVEN watcher, comparison scripts |

Environment: WSL2 `Ubuntu-24.04` at `D:\WSL\Ubuntu-24.04`, ROS 2 Jazzy, Gazebo 8.15.0, PX4 v1.17.0,
px4_msgs release/1.17, Micro-XRCE-DDS-Agent v2.4.3, Python 3.11.9 venv `~/venvs/atswarm` (same interpreter and package
versions as the conference runs).
