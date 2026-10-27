"""Step 9 - qualitative mission figures: UAV trajectories on the map + Gantt chart of executed tasks.

    python experiments/09_visualize_mission.py                      # first saved log
    python experiments/09_visualize_mission.py --log results/missions/medium-failures-1000_anytime_k10.pkl

Logs are written by 05_run_closed_loop.py (--keep-logs). Output: results/figures/fig_mission_<name>.pdf
"""
import argparse
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm import plotting as PL  # noqa: E402
from anytimeswarm.utils import load_config, rpath  # noqa: E402

plt = PL.plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    logs = sorted((rpath(cfg["paths"]["results_dir"]) / "missions").glob("*.pkl"))
    path = Path(args.log) if args.log else (logs[0] if logs else None)
    if path is None:
        print("no mission logs - run 05_run_closed_loop.py first")
        return
    with open(path, "rb") as f:
        d = pickle.load(f)
    sc, m = d["scenario"], d["metrics"]
    ex = m["_executed"]
    served = {j for _, j, *_ in ex}
    PL.setup()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 2.3), gridspec_kw={"width_ratios": [1, 1.4]})
    tasks = {t.id: t for t in sc.tasks}
    xs = np.array([[t.x, t.y] for t in sc.tasks]) / 1000
    ok = np.array([t.id in served for t in sc.tasks])
    a1.scatter(xs[ok, 0], xs[ok, 1], s=9, color=PL.PALETTE[2], label="served", zorder=3)
    a1.scatter(xs[~ok, 0], xs[~ok, 1], s=12, marker="x", color=PL.PALETTE[7], label="missed", zorder=3)
    a1.scatter([sc.depot[0] / 1000], [sc.depot[1] / 1000], marker="s", s=25, color=PL.INK, label="depot", zorder=4)
    failed = {e.data["uav_id"] for e in sc.events if e.kind == "failure"}
    for uid in sorted({u for u, *_ in ex}):
        pts = [(sc.depot[0], sc.depot[1])] + [(tasks[j].x, tasks[j].y) for u, j, *_ in sorted(ex, key=lambda r: r[3]) if u == uid]
        p = np.array(pts) / 1000
        a1.plot(p[:, 0], p[:, 1], lw=0.7, color=PL.PALETTE[uid % 8], alpha=0.8, ls=":" if uid in failed else "-")
    a1.set_aspect("equal")
    a1.set_xlabel("x (km)")
    a1.set_ylabel("y (km)")
    a1.legend(fontsize=5.5, loc="upper right")
    for u, j, dep, start, fin in ex:
        a2.barh(u, fin - start, left=start, color=PL.PALETTE[u % 8], height=0.6)
        a2.barh(u, start - dep, left=dep, color=PL.GRID, height=0.25)
    for e in sc.events:
        a2.axvline(e.time, color={"arrival": PL.PALETTE[0], "failure": PL.PALETTE[7], "deadline": PL.PALETTE[3]}[e.kind],
                   lw=0.6, ls="--")
    a2.set_xlabel("mission time (s)")
    a2.set_ylabel("UAV")
    a2.set_title(f"{sc.name} | {m['method']} | utility {m['utility_rate'] * 100:.0f}%", fontsize=7)
    fig.tight_layout()
    PL.save(fig, rpath(cfg["paths"]["results_dir"]) / "figures" / f"fig_mission_{path.stem}")
    print(f"[ok] -> results/figures/fig_mission_{path.stem}.pdf (dashed lines: arrival=blue, failure=red, deadline=yellow)")


if __name__ == "__main__":
    main()
