#!/usr/bin/env python3
"""Illustrative tier C figure from the demonstration flights of tools/demo_fly.sh (development seed 1; no statistics).

Top view of the flown PX4 trajectories (ULog vehicle_local_position, NED of each UAV converted to the Gazebo ENU frame
through its spawn point, journal_ros/common.py) with the tasks of the mission coloured by their outcome (served on
time, served late, not served), for the proposed model with fallback and for the nominal model.

    ~/venvs/atswarm/bin/python experiments/paper_demo.py  ->  paper_journal/figures/fig_demo_tracks.pdf
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from pyulog import ULog  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "journal_ros"))
sys.path.insert(0, str(ROOT))
from common import gz_scenario, map_to_gz, spawn_xy  # noqa: E402
from journal_core.study2 import tighten_windows  # noqa: E402

D = ROOT / "results" / "tier_c" / "demo"
RUNS = [("proposed", "Proposed model with fallback"), ("nominal", "Nominal model")]
UAV_COL = ["#1F6FC5", "#E07B00", "#178A5E"]
STATUS = {"on time": "#2E7D32", "late": "#C62828", "not served": "#9E9E9E"}


def tracks(tag):
    out = {}
    for f in sorted((D / "ulog" / tag).glob("uav*_*.ulg")):
        k = int(f.name[3:f.name.index("_")]) - 1
        lp = ULog(str(f), ["vehicle_local_position"]).get_dataset("vehicle_local_position").data
        sx, sy = spawn_xy(k, 3)
        xy = np.c_[sx + lp["y"], sy + lp["x"]]          # NED (north, east) -> ENU (east, north)
        out.setdefault(k, []).append(xy)
    return {k: np.vstack(v) for k, v in out.items()}


def main():
    sc = tighten_windows(gz_scenario("arrivals", 1), 0.5)
    task_xy = {t.id: map_to_gz(t.x, t.y, sc.depot) for t in sc.tasks}
    fig, axes = plt.subplots(1, len(RUNS), figsize=(7.0, 3.5), sharex=True, sharey=True)
    for ax, (tag, title) in zip(axes, RUNS):
        res = json.loads((D / f"{tag}.json").read_text())
        served = {int(j) for j in res["_served"]}
        late = {int(j) for j in res["_late"]}
        for k, xy in tracks(tag).items():
            ax.plot(xy[:, 0], xy[:, 1], color=UAV_COL[k], lw=1.1, alpha=0.9, label=f"UAV {k + 1}")
        for j, (x, y) in task_xy.items():
            st = "on time" if j in served else "late" if j in late else "not served"
            ax.scatter(x, y, s=46, marker="o", facecolor=STATUS[st], edgecolor="white", lw=0.8, zorder=3)
        ax.scatter(0, 0, s=60, marker="s", color="black", zorder=4)
        ax.set_title(f"{title}\nutility {100 * res['utility_rate']:.1f}%, {res['late_served']} late", fontsize=8.5)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
        ax.set_xlabel("east (m)")
    axes[0].set_ylabel("north (m)")
    h = [plt.Line2D([], [], color=c, lw=1.4) for c in UAV_COL]
    h += [plt.Line2D([], [], marker="o", ls="", markerfacecolor=c, markeredgecolor="white", markersize=7)
          for c in STATUS.values()]
    h += [plt.Line2D([], [], marker="s", ls="", color="black", markersize=6)]
    fig.legend(h, ["UAV 1", "UAV 2", "UAV 3"] + [f"task {s}" for s in STATUS] + ["depot"], loc="lower center",
               ncol=7, frameon=False, fontsize=7, handletextpad=0.3, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(ROOT / "paper_journal" / "figures" / "fig_demo_tracks.pdf", bbox_inches="tight")
    fig.savefig(D / "fig_demo_tracks.png", dpi=160, bbox_inches="tight")
    screenshots()
    numbers()
    print("ok")


def screenshots():
    """Two Gazebo GUI captures of the same flights (results/tier_c/demo/selected): a close-up of a PX4 x500 above a task
    served on time (proposed model) and an oblique view of all task pillars near the end of the mission (nominal
    model). Pillar colours as in journal_ros/viz.py."""
    a = plt.imread(D / "selected" / "closeup_proposed.png")
    b = plt.imread(D / "selected" / "overview_nominal.png")
    ha, wa = a.shape[:2]
    hb, wb = b.shape[:2]
    a = a[int(0.12 * ha):int(0.80 * ha), int(0.22 * wa):int(0.82 * wa)]
    b = b[int(0.20 * hb):int(0.75 * hb), :]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.5), gridspec_kw={"width_ratios": [a.shape[1] / a.shape[0],
                                                                                    b.shape[1] / b.shape[0]]})
    for x, img, lab in [(ax[0], a, "(a) PX4 x500 above a task served on time"),
                        (ax[1], b, "(b) task pillars near the end of a mission")]:
        x.imshow(img)
        x.set_xticks([])
        x.set_yticks([])
        x.set_xlabel(lab, fontsize=8)
    h = [plt.Line2D([], [], marker="s", ls="", color=c, markersize=6) for c in ("#5CC566", "#D9403F", "#8C8C8C")]
    fig.legend(h, ["served on time", "served late", "not served"], loc="lower center", ncol=3, frameon=False,
               fontsize=7.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(ROOT / "paper_journal" / "figures" / "fig_demo_gazebo.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(D / "fig_demo_gazebo.png", dpi=160, bbox_inches="tight")


def numbers():
    """Macros \\val{Z...} for the text: outcome of the two illustrative flights."""
    mac = {}
    for tag, key in (("proposed", "Prop"), ("nominal", "Nom")):
        r = json.loads((D / f"{tag}.json").read_text())
        mac[f"ZDemoU{key}"] = f"{100 * r['utility_rate']:.1f}"
        mac[f"ZDemoServed{key}"] = str(r["served"])
        mac[f"ZDemoLate{key}"] = str(r["late_served"])
        mac[f"ZDemoRTF{key}"] = f"{r['rtf']:.2f}"
        mac["ZDemoNTasks"] = str(r["n_tasks"])
    lines = ["% generated by experiments/paper_demo.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(mac.items())]
    (ROOT / "paper_journal" / "tables" / "numbers_demo.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 8.5, "font.family": "serif", "mathtext.fontset": "stix",
                         "font.serif": ["STIXGeneral", "DejaVu Serif"]})
    main()
