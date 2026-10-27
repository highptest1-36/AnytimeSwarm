"""Step 1 - pilot: how long does a first feasible plan take, and how fast does ALNS iterate?
Use it to confirm the budget grid {20, 50, 100, 250, 500} ms is sensible on YOUR laptop
(Technical Go/No-Go 27/10). Dev seeds only.

    python experiments/01_pilot_timing.py
Output: results/pilot_timing.csv + printed summary.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.algorithms.methods import solve  # noqa: E402
from anytimeswarm.simulator.executor import run_mission  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import append_registry, load_config, rpath, wait_machine_idle  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    cfg = load_config(args.config)
    rows = []
    for scale in cfg["scales"]:
        for profile in cfg["profiles"]:
            for seed in range(cfg["seeds"]["dev"]["start"], cfg["seeds"]["dev"]["start"] + args.seeds):
                wait_machine_idle()  # timing run: never overlap RAVEN-UAV
                sc = generate_scenario(cfg, scale, profile, seed)
                snaps = []
                run_mission(sc, cfg, "regret_repair", 0, snapshot_hook=lambda P, o, c, t: snaps.append((P, o, c)))
                for P, old, call in snaps:
                    r = solve("alns_fixed", P, old, 200, cfg, seed=seed)
                    rows.append({"scale": scale, "profile": profile, "seed": seed, "call": call, "N": P.N, "M": P.M,
                                 "t_first_feasible_ms": r["t_first_feasible_ms"],
                                 "ms_per_iter": (r["elapsed_ms"] - r["t_first_feasible_ms"]) / max(r["iters"], 1),
                                 "gain_200ms_pct": (r["J"] - r["J_initial"]) / P.scale * 100})
    df = pd.DataFrame(rows)
    out = rpath(cfg["paths"]["results_dir"]) / "pilot_timing.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    s = df.groupby("scale").agg(N=("N", "mean"), tff_med=("t_first_feasible_ms", "median"),
                                tff_p95=("t_first_feasible_ms", lambda x: np.percentile(x, 95)),
                                ms_iter=("ms_per_iter", "median"), gain=("gain_200ms_pct", "mean"))
    print(s.round(2).to_string())
    print("\nRule: the smallest budget must exceed the P95 time-to-first-feasible of the largest scale;"
          " otherwise raise the budget grid in configs/default.yaml (do NOT force the method to fail).")
    append_registry(cfg, {"run": "pilot_timing", "script": "01_pilot_timing", "split": "dev",
                          "notes": "; ".join(f"{k}: tff_p95={v:.1f}ms" for k, v in s.tff_p95.items())})


if __name__ == "__main__":
    main()
