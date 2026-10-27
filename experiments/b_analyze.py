#!/usr/bin/env python3
"""Analyse a tier B grid: mean metric per configuration and paired mission-level bootstrap comparisons.

    python experiments/b_analyze.py --csv results/tier_b/explore_dev.csv [--ours anytime_risk] [--metric utility_rate]

Comparisons (95% percentile CI, 10 000 resamples over missions, missions paired by scenario):
  1. methods: --ours against every other method, within (exec, latency, kappa, trigger)
  2. triggers: every non-event trigger against "event", for each method, within (exec, latency, kappa)
Output: results/tier_b/<stem>_summary.md
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

KEY = ["exec_level", "latency_level", "kappa", "trigger"]


def paired(a, b, n_boot=10_000, seed=0):
    d = np.asarray(a) - np.asarray(b)
    idx = np.random.default_rng(seed).integers(0, d.size, size=(n_boot, d.size))
    lo, hi = np.percentile(d[idx].mean(axis=1), [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float(np.mean(d > 0)), float(np.mean(d < 0))


def compare(df, by, col, ours, metric):
    rows = []
    for k, g in df.groupby(by):
        w = g.pivot_table(index="scenario", columns=col, values=metric)
        if ours not in w:
            continue
        for other in [c for c in w.columns if c != ours]:
            p = w[[ours, other]].dropna()
            mean, lo, hi, win, loss = paired(p[ours], p[other])
            rows.append(dict(zip(by, k if isinstance(k, tuple) else (k,))) |
                        {col: other, "diff": mean, "ci_lo": lo, "ci_hi": hi, "win": win, "loss": loss,
                         "sig": "+" if lo > 0 else ("-" if hi < 0 else "0")})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--ours", default="anytime")
    ap.add_argument("--metric", default="utility_rate")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    if "trigger" not in df:
        df["trigger"] = "event"
    L = [f"# {Path(a.csv).stem}: {a.metric}", "",
         f"{df.scenario.nunique()} missions per configuration; paired bootstrap over missions (95% CI).", ""]
    piv = df.pivot_table(index=KEY, columns="method", values=a.metric, aggfunc="mean")
    L += ["## Mean " + a.metric, "", piv.round(4).to_markdown(), ""]
    ms = df.pivot_table(index=KEY, columns="method", values="plan_ms_mean", aggfunc="mean")
    L += ["## Planning time per call (ms)", "", ms.round(1).to_markdown(), ""]
    rp = df.pivot_table(index=KEY, columns="method", values="n_replans", aggfunc="mean")
    L += ["## Replanning calls per mission", "", rp.round(1).to_markdown(), ""]
    c1 = compare(df, KEY, "method", a.ours, a.metric)
    L += [f"## {a.ours} minus other methods", "", c1.round(4).to_markdown(index=False), ""]
    if c1.size:
        s = c1.groupby("method").sig.value_counts().unstack(fill_value=0)
        L += ["Count of significant wins (+), ties (0), losses (-):", "", s.to_markdown(), ""]
    trig = df.trigger.unique()
    if len(trig) > 1 and "event" in trig:
        rows = []
        for t in [x for x in trig if x != "event"]:
            sub = df[df.trigger.isin(["event", t])]
            c = compare(sub, ["exec_level", "latency_level", "kappa", "method"], "trigger", t, a.metric)
            rows.append(c)
        c2 = pd.concat(rows).rename(columns={"trigger": "vs"})
        c2.insert(4, "trigger", [t for t, n in zip([x for x in trig if x != "event"], [len(r) for r in rows])
                                 for _ in range(n)])
        L += ["## Trigger minus event-only replanning (same method)", "", c2.round(4).to_markdown(index=False), ""]
    out = Path(a.csv).with_name(Path(a.csv).stem + f"_summary_{a.ours}.md")
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))
    print(f"[ok] -> {out}")


if __name__ == "__main__":
    main()
