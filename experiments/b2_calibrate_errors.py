#!/usr/bin/env python3
"""Fit the finish-time error model of the risk-aware delay cost on DEVELOPMENT missions only.

    python experiments/b2_calibrate_errors.py [--levels low,mid,high]

For each execution level, the 90 DEV missions are flown once with a neutral planner (ALNS, fixed 40 ms, event
trigger, kappa = 1, no latency). Every executed task gives a pair (lead time h = planned finish - publication time,
error e = actual finish - planned finish). ErrorModel.fit estimates m(h) = b0 + b1 h and sd(h) = s0 + s1 h.
In tier C the same script is fed by PX4/Gazebo development flights instead.
Outputs: models/error_model_dev.json, results/tier_b/calibration_dev.csv (binned check of the fit)
"""
import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402
from journal_core.risk import ErrorModel  # noqa: E402

from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="low,mid,high")
    args = ap.parse_args()
    s = CFG["seeds"]["dev"]
    scen = [generate_scenario(CFG, sc, pr, seed) for sc in CFG["scales"] for pr in CFG["profiles"]
            for seed in range(s["start"], s["start"] + s["n"])]
    models, rows = {"nominal": ErrorModel("nominal")}, []
    for lv in args.levels.split(","):
        H, E = [], []
        for sc in scen:
            m = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 40.0, kappa=1.0, xm=EXEC_LEVELS[lv],
                                seed=sc.seed, keep_log=True)
            for h, e in m["_calib"]:
                H.append(h)
                E.append(e)
        H, E = np.array(H), np.array(E)
        em = ErrorModel.fit(lv, H, E)
        models[lv] = em
        bins = np.quantile(H, np.linspace(0, 1, 9))
        for a, b in zip(bins[:-1], bins[1:]):
            sel = (H >= a) & (H <= b)
            hm = H[sel].mean()
            z = (E[sel] - em.mean(H[sel])) / np.maximum(em.sd(H[sel]), 1e-9)
            rows.append({"level": lv, "h_lo": a, "h_hi": b, "n": int(sel.sum()), "h_mean": hm,
                         "e_mean": E[sel].mean(), "e_mean_fit": float(em.mean(hm)), "e_sd": E[sel].std(),
                         "e_sd_fit": float(em.sd(hm)), "z_sd": z.std(), "p_e_gt_q90_fit": float(np.mean(z > 1.2816))})
        print(f"{lv:5s} n={em.n:6d}  mean = {em.b0:.2f} + {em.b1:.4f} h   sd = {em.s0:.2f} + {em.s1:.4f} h  "
              f"(at h=300 s: mean {em.mean(300.0):.1f} s, sd {float(em.sd(300.0)):.1f} s)", flush=True)
    out = ROOT / "models" / "error_model_dev.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({k: v.__dict__ for k, v in models.items()}, indent=2))
    df = pd.DataFrame(rows)
    (ROOT / "results" / "tier_b").mkdir(parents=True, exist_ok=True)
    df.to_csv(ROOT / "results" / "tier_b" / "calibration_dev.csv", index=False)
    print(df.round(3).to_string(index=False))
    print(f"[ok] -> {out}")


if __name__ == "__main__":
    main()
