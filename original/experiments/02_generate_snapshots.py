"""Step 2 - generate scenarios and the static replanning-snapshot benchmark.

    python experiments/02_generate_snapshots.py --split dev
    python experiments/02_generate_snapshots.py --split test

For every (scale, profile, seed) the mission is simulated with a DETERMINISTIC reference planner
(ALNS with a fixed number of iterations, kappa = 0) and each replanning call is stored as a
snapshot (Problem + previous plan). Every method is later evaluated on exactly the same snapshots.
Outputs: data/scenarios_<split>.pkl, data/snapshots_<split>.pkl, data/snapshots_<split>_summary.csv
"""
import argparse
import pickle
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.simulator.executor import run_mission  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import append_registry, load_config, rpath  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--ref-iters", type=int, default=100)
    args = ap.parse_args()
    cfg = load_config(args.config)
    s = cfg["seeds"][args.split]
    scenarios, snapshots, rows = [], [], []
    for scale in cfg["scales"]:
        for profile in cfg["profiles"]:
            for seed in range(s["start"], s["start"] + s["n"]):
                sc = generate_scenario(cfg, scale, profile, seed)
                scenarios.append(sc)

                def hook(P, old, call, t_now, sc=sc):
                    if call == 0:
                        return  # mission start (no previous plan) is not a REplanning call
                    snapshots.append({"scenario": sc.name, "scale": scale, "profile": profile, "seed": seed,
                                      "call": call, "t_now": t_now, "P": P, "old": old})
                    rows.append({"scenario": sc.name, "scale": scale, "profile": profile, "seed": seed,
                                 "call": call, "N": P.N, "M": P.M, "hopeless": len(P.hopeless)})
                run_mission(sc, cfg, "alns_fixed", 1e9, kappa=0.0, seed=seed, snapshot_hook=hook,
                            solve_kwargs={"max_iters": args.ref_iters})
        print(f"  {scale}: {sum(1 for r in rows if r['scale'] == scale)} snapshots", flush=True)
    d = rpath(cfg["paths"]["data_dir"])
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"scenarios_{args.split}.pkl", "wb") as f:
        pickle.dump(scenarios, f)
    with open(d / f"snapshots_{args.split}.pkl", "wb") as f:
        pickle.dump(snapshots, f)
    df = pd.DataFrame(rows)
    df.to_csv(d / f"snapshots_{args.split}_summary.csv", index=False)
    print(df.groupby(["scale", "profile"]).agg(n=("N", "size"), N_mean=("N", "mean"), M_mean=("M", "mean")).round(1))
    append_registry(cfg, {"run": f"snapshots_{args.split}", "script": "02_generate_snapshots", "split": args.split,
                          "notes": f"{len(scenarios)} scenarios, {len(snapshots)} snapshots"})
    print(f"[ok] {len(scenarios)} scenarios, {len(snapshots)} snapshots -> {d}")


if __name__ == "__main__":
    main()
