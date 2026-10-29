#!/usr/bin/env python3
"""Study 4C: tier C error model of the high disturbance level from DEVELOPMENT flights (seeds 0-2).

    python experiments/c4_calibrate_high.py [--runs results/tier_c/calib_dev_high]

Same fit as experiments/c_calibrate_errors.py (ErrorModel.fit on the pairs of every finished task), but the frozen
models/error_model_tierc_dev.json is left untouched: its levels and latency are copied into
models/error_model_tierc_dev4.json and the high level is added.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core.risk import ErrorModel  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(ROOT / "results/tier_c/calib_dev_high"))
    a = ap.parse_args()
    H, E, n, rtf = [], [], 0, []
    for f in sorted(Path(a.runs).glob("gz-*.json")):
        m = json.loads(f.read_text())
        n += 1
        rtf.append(m["rtf"])
        for h, e in m["_calib"]:
            H.append(h)
            E.append(e)
    em = ErrorModel.fit("high", H, E)
    out = json.loads((ROOT / "models" / "error_model_tierc_dev.json").read_text())
    out["high"] = em.__dict__
    (ROOT / "models" / "error_model_tierc_dev4.json").write_text(json.dumps(out, indent=2))
    print(f"high missions={n} tasks={em.n}  mean = {em.b0:.2f} + {em.b1:.4f} h  sd = {em.s0:.2f} + {em.s1:.4f} h  "
          f"RTF mean {np.mean(rtf):.2f} min {np.min(rtf):.2f}")


if __name__ == "__main__":
    main()
