#!/usr/bin/env python3
"""Analyse the tier B pilot: utility per configuration and paired mission-level bootstrap of AnytimeSwarm
against every baseline (10 000 resamples, 95% percentile CI). Missions are the resampling unit because the
replanning calls of one mission are not independent.

    python experiments/b1_analyze.py [--csv results/tier_b/pilot_dev.csv] [--metric utility_rate]

Output: results/tier_b/<csv stem>_summary.md (+ printed)
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OURS = "anytime"


def paired_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 10_000, seed: int = 0):
    d = a - b
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    boots = d[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float(np.mean(d >= 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "results" / "tier_b" / "pilot_dev.csv"))
    ap.add_argument("--metric", default="utility_rate")
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    key = ["exec_level", "latency_level", "kappa"]
    lines = [f"# Tier B pilot summary ({Path(args.csv).name}, metric = {args.metric})", "",
             f"{df.scenario.nunique()} missions; resampling unit = mission; 95% percentile CI, 10 000 resamples.", ""]

    piv = df.pivot_table(index=key, columns="method", values=args.metric, aggfunc="mean").round(4)
    ms = df.pivot_table(index=key, columns="method", values="plan_ms_mean", aggfunc="mean").round(1)
    lines += ["## Mean " + args.metric, "", piv.to_markdown(), "", "## Mean planning time per call (ms)", "",
              ms.to_markdown(), ""]

    rows = []
    for k, g in df.groupby(key):
        w = g.pivot_table(index="scenario", columns="method", values=args.metric)
        if OURS not in w:
            continue
        for base in [c for c in w.columns if c != OURS]:
            pair = w[[OURS, base]].dropna()
            mean, lo, hi, win = paired_ci(pair[OURS].to_numpy(), pair[base].to_numpy())
            rows.append(dict(zip(key, k)) | {"baseline": base, "diff": mean, "ci_lo": lo, "ci_hi": hi,
                                              "win_rate": win, "sig": "+" if lo > 0 else ("-" if hi < 0 else "0")})
    res = pd.DataFrame(rows)
    lines += [f"## AnytimeSwarm minus baseline ({args.metric}, paired by mission)", "",
              res.round(4).to_markdown(index=False), ""]

    # Go/No-Go (plan section 3b): AnytimeSwarm beats the compute-matched fixed budget (alns_fixed@40) with a CI
    # above 0 in at least one disturbed configuration (execution level != nominal).
    gate = res[(res.baseline == "alns_fixed@40") & (res.exec_level != "nominal")]
    passed = gate[gate.ci_lo > 0]
    lines += ["## Go/No-Go", "",
              f"Disturbed configurations where AnytimeSwarm > alns_fixed@40 with CI above 0: {len(passed)} / {len(gate)}.",
              ""]
    if len(passed):
        lines += [passed.round(4).to_markdown(index=False), ""]
    text = "\n".join(lines)
    out = Path(args.csv).with_name(Path(args.csv).stem + "_summary.md")
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"[ok] -> {out}")


if __name__ == "__main__":
    main()
