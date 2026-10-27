#!/usr/bin/env python3
"""Watch a tier B mission: UAVs, tasks, deadlines and every replanning call, for one or several planners side by side.

    python3 demo/live_mission.py                                         # medium-arrivals-1, anytime vs alns_fixed
    python3 demo/live_mission.py --scenario large-failures-3 --exec mid --kappa 50
    python3 demo/live_mission.py --methods anytime --exec nominal --speed 60
    python3 demo/live_mission.py --save /tmp/mission.gif                 # write a GIF instead of opening a window

Each planner runs the SAME mission (same tasks, events, wind, gusts and service times: common random numbers) through
journal_core.kinematic_executor, then the run is replayed. The mission takes a few seconds to compute; the replay
runs at --speed mission seconds per real second.

Legend
  orange circle  announced task, not served yet (size = reward)      green  served before its deadline
  red cross      served after its (tightened) deadline: no reward     grey   deadline passed, never served
  coloured triangle = UAV (trail = flown legs), black cross = failed UAV, black square = depot
Text box: mission time, reward collected so far, the last replanning call (trigger, CPU ms, stop reason).
"""
import argparse
import copy
import sys
from pathlib import Path

import matplotlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
PRED = LearnedPredictor.load(ORIGINAL / "models" / "improvement_model.json")
LABEL = {"anytime": "AnytimeSwarm", "alns_fixed": "ALNS fixed 250 ms", "alns_stagnation": "ALNS stagnation",
         "anytime_nodelay": "AnytimeSwarm w/o delay cost", "regret_repair": "Regret-2 repair only"}


def run(sc, method, args):
    base, _, b = method.partition("@")
    budget = float(b) if b else float(CFG["closed_loop_budget_ms"])
    m = run_mission_kin(copy.deepcopy(sc), CFG, base, budget, kappa=args.kappa, xm=EXEC_LEVELS[args.exec],
                        lat=LATENCY_LEVELS[args.lat], predictor=PRED, seed=sc.seed, keep_log=True)
    print(f"{method:18s} utility={m['utility_rate']:.3f} served={m['served']}/{m['n_tasks']} late={m['late_served']} "
          f"replans={m['n_replans']} plan_ms_mean={m['plan_ms_mean']:.1f} finish_err_p95={m['finish_err_p95_s']:.0f}s")
    return m


class Replay:
    def __init__(self, ax, sc, m, title):
        self.ax, self.sc, self.m = ax, sc, m
        self.tasks = {t.id: t for t in sc.tasks}
        self.final_dl = {t.id: t.deadline for t in sc.tasks}
        for ev in sc.events:
            if ev.kind == "deadline":
                j = ev.data["task_id"]
                self.final_dl[j] = min(self.final_dl[j], ev.data["new_deadline"])
        self.fail_t = {ev.data["uav_id"]: ev.time for ev in sc.events if ev.kind == "failure"}
        self.legs = {}
        for leg in sorted(m["_trajectory"], key=lambda r: r[6]):
            self.legs.setdefault(leg[0], []).append(leg)
        self.R_total = sum(t.reward for t in sc.tasks)
        W = sc.world["map_m"]
        ax.set_xlim(-0.03 * W, 1.03 * W)
        ax.set_ylim(-0.03 * W, 1.03 * W)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=11)
        ax.plot(*sc.depot, "ks", ms=9, zorder=5)
        cmap = matplotlib.colormaps["tab10"]
        self.colors = {u.id: cmap(i % 10) for i, u in enumerate(sc.uavs)}
        self.sc_open = ax.scatter([], [], s=[], c="orange", edgecolors="k", linewidths=0.4, zorder=3)
        self.sc_ok = ax.scatter([], [], s=[], c="limegreen", edgecolors="k", linewidths=0.4, zorder=3)
        self.sc_late = ax.scatter([], [], c="red", marker="x", s=40, zorder=3)
        self.sc_miss = ax.scatter([], [], c="grey", marker="x", s=30, zorder=3)
        self.uav_pts = {u.id: ax.plot([], [], marker="^", ms=9, color=self.colors[u.id], mec="k", zorder=6)[0]
                        for u in sc.uavs}
        self.trails = {u.id: ax.plot([], [], "-", lw=1.0, color=self.colors[u.id], alpha=0.6, zorder=2)[0]
                       for u in sc.uavs}
        self.text = ax.text(0.01, 0.99, "", transform=ax.transAxes, va="top", ha="left", fontsize=8.5,
                            family="monospace", bbox=dict(boxstyle="round", fc="white", alpha=0.85))
        self.start = {u.id: (u.x, u.y) for u in sc.uavs}

    def position(self, uid, t):
        x, y = self.start[uid]
        trail = [(x, y)]
        for (_u, _j, x0, y0, x1, y1, dep, arr, _s, fin) in self.legs.get(uid, []):
            if t < dep:
                break
            if t < arr:
                f = (t - dep) / (arr - dep) if arr > dep else 1.0
                x, y = x0 + f * (x1 - x0), y0 + f * (y1 - y0)
                trail.append((x, y))
                return (x, y), trail
            x, y = x1, y1
            trail.append((x, y))
        return (x, y), trail

    def draw(self, t):
        served, late = self.m["_served"], set(self.m["_late"])
        fin = {j: f for (_u, j, *_r, f) in self.m["_trajectory"]}
        groups = {"open": [], "ok": [], "late": [], "miss": []}
        for j, task in self.tasks.items():
            if task.announce > t:
                continue
            if j in served and served[j] <= t:
                groups["ok"].append(task)
            elif j in late and fin.get(j, 1e18) <= t:
                groups["late"].append(task)
            elif self.final_dl[j] < t:
                groups["miss"].append(task)
            else:
                groups["open"].append(task)
        for key, art in [("open", self.sc_open), ("ok", self.sc_ok), ("late", self.sc_late), ("miss", self.sc_miss)]:
            ts = groups[key]
            art.set_offsets([(k.x, k.y) for k in ts] if ts else [[float("nan"), float("nan")]])
            if key in ("open", "ok"):
                art.set_sizes([18 + 14 * k.reward for k in ts] if ts else [0])
        for uid, pt in self.uav_pts.items():
            (x, y), trail = self.position(uid, t)
            dead = uid in self.fail_t and self.fail_t[uid] <= t
            pt.set_data([x], [y])
            pt.set_marker("X" if dead else "^")
            pt.set_color("k" if dead else self.colors[uid])
            self.trails[uid].set_data([p[0] for p in trail], [p[1] for p in trail])
        reward = sum(self.tasks[j].reward for j, f in served.items() if f <= t)
        last = [r for r in self.m["_replans"] if r["t_now"] <= t]
        r = last[-1] if last else None
        kinds = [ev.kind for ev in self.sc.events if r and abs(ev.time - r["t_event"]) < 1e-9]
        trig = {"arrival": "new tasks", "failure": "UAV failure", "deadline": "deadline tightened"}
        lines = [f"t = {t:6.0f} s   reward {reward:5.1f}/{self.R_total:.0f} ({reward / self.R_total:5.1%})",
                 f"served {len(groups['ok']):3d}  late {len(groups['late']):2d}  missed {len(groups['miss']):2d}  "
                 f"open {len(groups['open']):2d}"]
        if r:
            lines.append(f"replan #{r['call']} at {r['t_now']:.0f}s ({trig.get(kinds[0], 'mission start') if kinds else 'mission start'})")
            lines.append(f"  CPU {r['elapsed_ms']:6.1f} ms, {r['iters']} iters, stop: {r['stop']}")
            lines.append(f"  plan published at {r['t_pub']:.1f}s, open tasks {r['n_open']}")
        self.text.set_text("\n".join(lines))
        return [self.sc_open, self.sc_ok, self.sc_late, self.sc_miss, self.text, *self.uav_pts.values(),
                *self.trails.values()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", default="medium-arrivals-1", help="<scale>-<profile>-<seed>, DEV seeds 0-9")
    ap.add_argument("--methods", default="anytime,alns_fixed")
    ap.add_argument("--kappa", type=float, default=50.0)
    ap.add_argument("--exec", default="low", choices=sorted(EXEC_LEVELS))
    ap.add_argument("--lat", default="none", choices=sorted(LATENCY_LEVELS))
    ap.add_argument("--speed", type=float, default=40.0, help="mission seconds per real second")
    ap.add_argument("--save", default=None, help="write an animated GIF instead of opening a window")
    args = ap.parse_args()
    if args.save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    scale, profile, seed = args.scenario.split("-")
    if int(seed) >= CFG["seeds"]["dev"]["start"] + CFG["seeds"]["dev"]["n"]:
        sys.exit("only DEV seeds (0-9) may be visualised: test seeds stay untouched")
    sc = generate_scenario(CFG, scale, profile, int(seed))
    print(f"{sc.name}: {len(sc.uavs)} UAVs, {len(sc.tasks)} tasks, {len(sc.events)} events, "
          f"kappa={args.kappa:g}, exec={args.exec}, latency={args.lat}")
    methods = args.methods.split(",")
    runs = [run(sc, m, args) for m in methods]

    fig, axes = plt.subplots(1, len(methods), figsize=(6.2 * len(methods), 6.6), squeeze=False)
    fig.suptitle(f"{sc.name}   kappa={args.kappa:g}   execution={args.exec}   latency={args.lat}", fontsize=12)
    reps = [Replay(ax, sc, m, LABEL.get(meth, meth)) for ax, m, meth in zip(axes[0], runs, methods)]
    t_end = max([sc.world["horizon_s"]] + [leg[9] for m in runs for leg in m["_trajectory"]])
    fps = 20
    frames = int(t_end / args.speed * fps) + 1

    def update(k):
        t = min(k * args.speed / fps, t_end)
        return [a for rep in reps for a in rep.draw(t)]

    anim = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False, repeat=False)
    fig.tight_layout()
    if args.save:
        anim.save(args.save, writer=PillowWriter(fps=fps))
        print(f"[ok] -> {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
