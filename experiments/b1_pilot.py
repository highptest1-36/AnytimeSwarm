#!/usr/bin/env python3
"""Tier B pilot (DEV seeds only): closed-loop missions with execution disturbances and plan latency.

    python experiments/b1_pilot.py                       # full pilot grid on the 90 DEV missions
    python experiments/b1_pilot.py --quick               # first 2 seeds per scale x profile (debugging)
    python experiments/b1_pilot.py --resume              # continue after an interruption

Grid: execution level x latency level x kappa x method. Everything else is the frozen conference configuration
(original/configs/frozen_2026-10-24.yaml) and the frozen predictor (original/models/improvement_model.json): this is
the zero-shot transfer setting. The planner always uses the conference (nominal) model; only execution changes.
Seeds are DEV seeds 0-9: the pilot chooses levels and the Go/No-Go, it is not evidence for the paper.
Timing run: missions run one at a time under the machine-idle guard (RAVEN on Windows, PX4/Gazebo in WSL).
Output: results/tier_b/pilot_dev[_quick][tag].csv (checkpoint after every configuration).
"""
import argparse
import copy
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402
from run_guarded import _busy  # noqa: E402

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import env_info, load_config  # noqa: E402

FROZEN_CFG = ORIGINAL / "configs" / "frozen_2026-10-24.yaml"
FROZEN_MODEL = ORIGINAL / "models" / "improvement_model.json"


def wait_idle(poll_s=30.0):
    waited = 0.0
    while _busy():
        if waited == 0.0:
            print(f"[guard] machine busy, waiting: {_busy()[0][:100]}", flush=True)
        time.sleep(poll_s)
        waited += poll_s
    return waited


def parse_spec(spec: str, B: float):
    """'alns_fixed@40' -> ('alns_fixed', 40.0); plain names use the closed-loop budget B."""
    base, _, opt = spec.partition("@")
    return base, (float(opt) if opt else B)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", default="regret_repair,alns_fixed,alns_fixed@40,alns_stagnation,anytime,anytime_nodelay")
    ap.add_argument("--kappas", default="1,10,50")
    ap.add_argument("--exec", default="nominal,low,mid")
    ap.add_argument("--lat", default="none,high")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    cfg = load_config(FROZEN_CFG)
    predictor = LearnedPredictor.load(FROZEN_MODEL)
    B = float(cfg["closed_loop_budget_ms"])
    s = cfg["seeds"]["dev"]
    seeds = range(s["start"], s["start"] + (2 if args.quick else s["n"]))
    scenarios = [generate_scenario(cfg, scale, profile, seed)
                 for scale in cfg["scales"] for profile in cfg["profiles"] for seed in seeds]
    methods = args.methods.split(",")
    kappas = [float(k) for k in args.kappas.split(",")]

    out = ROOT / "results" / "tier_b" / f"pilot_dev{'_quick' if args.quick else ''}{args.tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, done = [], set()
    if args.resume and out.exists():
        rows = pd.read_csv(out).to_dict("records")
        done = {(r["exec_level"], r["latency_level"], float(r["kappa"]), r["method"]) for r in rows}
    print(f"[pilot] {len(scenarios)} missions, methods={methods}, kappas={kappas}, exec={args.exec}, lat={args.lat}")
    print(f"[pilot] env {env_info()}", flush=True)
    t0, waited = time.time(), 0.0
    for xl in args.exec.split(","):
        for ll in args.lat.split(","):
            for kappa in kappas:
                for m in methods:
                    if (xl, ll, kappa, m) in done:
                        continue
                    base, Bm = parse_spec(m, B)
                    batch = []
                    for sc in scenarios:
                        waited += wait_idle()
                        r = run_mission_kin(copy.deepcopy(sc), cfg, base, Bm, kappa=kappa, xm=EXEC_LEVELS[xl],
                                            lat=LATENCY_LEVELS[ll], predictor=predictor, seed=sc.seed)
                        r["method"] = m
                        batch.append(r)
                    rows += batch
                    d = pd.DataFrame(batch)
                    print(f"  exec={xl:7s} lat={ll:4s} kappa={kappa:>4g} {m:16s} utility={d.utility_rate.mean():.3f} "
                          f"late={d.late_served.mean():.2f} drop_delay={d.dropped_by_delay.mean():.2f} "
                          f"drop_exec={d.dropped_in_exec.mean():.2f} plan_ms={d.plan_ms_mean.mean():.1f} "
                          f"({time.time() - t0:.0f}s)", flush=True)
                    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[ok] {len(rows)} rows -> {out}  (guard waited {waited:.0f}s)")


if __name__ == "__main__":
    main()
