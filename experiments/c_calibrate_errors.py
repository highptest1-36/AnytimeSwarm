#!/usr/bin/env python3
"""Fit the tier C error model and plan-acceptance latency from DEVELOPMENT flights (PX4 SITL + Gazebo).

    python experiments/c_calibrate_errors.py [--runs results/tier_c/calib_dev_low results/tier_c/calib_dev_mid]

Every finished task of every development mission gives (lead time h, finish error e) in tier C mission seconds;
ErrorModel.fit is applied per execution level (directory suffix). The measured acceptance latency (plan release ->
every UAV reports the new plan version, simulation seconds) gives the latency mean used by AnytimeSwarm-R in tier C.
Outputs: models/error_model_tierc_dev.json (+ "latency_mean_s"), results/tier_c/calibration_tierc_dev.csv
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core.risk import ErrorModel  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=[str(ROOT / "results/tier_c/calib_dev_low"),
                                                  str(ROOT / "results/tier_c/calib_dev_mid")])
    a = ap.parse_args()
    models, rows, lat = {"nominal": ErrorModel("nominal")}, [], []
    for d in map(Path, a.runs):
        level = d.name.rsplit("_", 1)[-1]
        H, E, n = [], [], 0
        for f in sorted(d.glob("gz-*.json")):
            m = json.loads(f.read_text())
            n += 1
            for h, e in m["_calib"]:
                H.append(h)
                E.append(e)
            lat += m["_accept_latency_s"]
            rows.append({"level": level, "run": f.stem, "utility": m["utility_rate"], "late": m["late_served"],
                         "rtf": m["rtf"], "err_mean": m["finish_err_mean_s"], "err_p95": m["finish_err_p95_s"]})
        em = ErrorModel.fit(level, H, E)
        models[level] = em
        z = (np.array(E) - em.mean(np.array(H))) / np.maximum(em.sd(np.array(H)), 1e-9)
        print(f"{level:5s} missions={n} tasks={em.n}  mean = {em.b0:.2f} + {em.b1:.4f} h  sd = {em.s0:.2f} + "
              f"{em.s1:.4f} h   z_sd={z.std():.2f}  P(z>1.28)={np.mean(z > 1.2816):.3f}")
    out = {k: v.__dict__ for k, v in models.items()}
    out["latency_mean_s"] = float(np.mean(lat)) if lat else 0.0
    out["latency_p95_s"] = float(np.percentile(lat, 95)) if lat else 0.0
    (ROOT / "models" / "error_model_tierc_dev.json").write_text(json.dumps(out, indent=2))
    pd.DataFrame(rows).to_csv(ROOT / "results" / "tier_c" / "calibration_tierc_dev.csv", index=False)
    print(f"acceptance latency: mean {out['latency_mean_s']:.3f} s, p95 {out['latency_p95_s']:.3f} s "
          f"(simulation seconds, n={len(lat)})")


if __name__ == "__main__":
    main()
