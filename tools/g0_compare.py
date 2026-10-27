#!/usr/bin/env python3
"""G0: compare the Linux re-run of the conference DEV pipeline (repro/results) with the conference results
(D:/paper/TAIMMA_2027/AnytimeSwarm/results). Writes results/g0/compare.md.

What must match and why
  * reference solutions: ALNS 3 s is time-limited, OR-Tools 5 s too -> close, not identical
  * predictor re-trained on Linux traces: traces are wall-clock timed -> close coefficients / AUC, same mu rule
  * static + closed loop with the FROZEN predictor: same algorithm, different CPU/OS speed -> the conclusions
    (sign and significance of AnytimeSwarm vs baselines) must hold; absolute ms and iteration counts may differ
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

J = Path(__file__).resolve().parents[1]
ORIG = J.parent / "AnytimeSwarm"
REPRO = J / "repro"
sys.path.insert(0, str(REPRO))
from anytimeswarm.analysis import at_kappa, load_static  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

cfg = load_config(REPRO / "configs" / "frozen_2026-10-24.yaml")


def cfg_for(root: Path) -> dict:
    c = json.loads(json.dumps(cfg))
    c["paths"]["results_dir"] = str(root / "results")
    return c


def md(df: pd.DataFrame, digits=4) -> str:
    return df.round(digits).to_markdown()


L = ["# G0 — conference DEV pipeline re-run on Linux vs conference results", "",
     "Windows = conference run (24/10/2026, Python 3.11.9, Windows 11). Linux = this re-run (WSL2 Ubuntu 24.04, "
     "Python 3.11.9, identical package versions, frozen config and frozen predictor).", ""]

# ---------------------------------------------------------------- reference solutions
ro = pd.read_csv(ORIG / "results/static/reference_dev.csv").set_index("snap")
rr = pd.read_csv(REPRO / "results/static/reference_dev.csv").set_index("snap")
rows = []
for c in ["J_alns_ref", "J_ortools"]:
    a, b = ro[c].dropna(), rr[c].dropna()
    idx = a.index.intersection(b.index)
    rel = (b[idx] - a[idx]) / a[idx].abs().clip(lower=1e-9)
    rows.append({"solver": c, "n": len(idx), "identical": float(np.mean(a[idx] == b[idx])),
                 "mean_rel_diff": rel.mean(), "max_abs_rel_diff": rel.abs().max()})
bko, bkr = ro[["J_alns_ref", "J_ortools"]].max(axis=1), rr[["J_alns_ref", "J_ortools"]].max(axis=1)
rows.append({"solver": "best of both", "n": len(bko), "identical": float(np.mean(bko == bkr)),
             "mean_rel_diff": ((bkr - bko) / bko.abs()).mean(), "max_abs_rel_diff": ((bkr - bko) / bko.abs()).abs().max()})
L += ["## 1. Reference solutions (time-limited solvers)", "", pd.DataFrame(rows).round(6).to_markdown(index=False), ""]

# ---------------------------------------------------------------- predictor
po = json.loads((ORIG / "results/predictor_eval.json").read_text())
pr = json.loads((REPRO / "results/predictor_eval.json").read_text())
mo = json.loads((ORIG / "results/mu_suggested.json").read_text())
mr = json.loads((REPRO / "results/mu_suggested.json").read_text())
ev = pd.DataFrame({"Windows": po["learned_oof"], "Linux": pr["learned_oof"]})
co = pd.DataFrame({"Windows": po["coef_standardised"], "Linux": pr["coef_standardised"]})
ca, cb = co.Windows.to_numpy(), co.Linux.to_numpy()
cos = float(ca @ cb / np.linalg.norm(ca) / np.linalg.norm(cb))
L += ["## 2. Improvement predictor re-trained on Linux traces", "",
      f"Training samples: Windows {po['n_samples']}, Linux {pr['n_samples']}. "
      f"mu rule: Windows mu={mo['mu']:g} (mean stop {mo['mean_t_stop_ms_kappa1']:.1f} ms), "
      f"Linux mu={mr['mu']:g} (mean stop {mr['mean_t_stop_ms_kappa1']:.1f} ms).", "",
      "Out-of-fold evaluation:", "", md(ev), "",
      f"Standardised coefficients (cosine similarity {cos:.3f}):", "", md(co), ""]

# ---------------------------------------------------------------- static benchmark
so, sr = load_static(cfg_for(ORIG), "dev"), load_static(cfg_for(REPRO), "dev")
rows = []
for name, df in [("Windows", so), ("Linux", sr)]:
    k1 = at_kappa(df, 1)
    g = k1.groupby(["method", "budget_ms"]).agg(regret_pct=("regret_pct", "mean"), elapsed_ms=("elapsed_ms", "mean"),
                                                iters=("iters", "mean")).reset_index()
    g["run"] = name
    rows.append(g)
st = pd.concat(rows).pivot_table(index=["method", "budget_ms"], columns="run",
                                 values=["regret_pct", "elapsed_ms", "iters"])
st = st[[("regret_pct", "Windows"), ("regret_pct", "Linux"), ("elapsed_ms", "Windows"), ("elapsed_ms", "Linux"),
         ("iters", "Windows"), ("iters", "Linux")]]
af = lambda df: df[(df.method == "alns_fixed") & (df.budget_ms == 500)]  # noqa: E731
speed_o = (af(so).iters / af(so).elapsed_ms).mean()
speed_r = (af(sr).iters / af(sr).elapsed_ms).mean()
L += ["## 3. Static snapshot benchmark (kappa = 1, mean over 531 snapshots)", "",
      f"Search speed (ALNS iterations per ms, alns_fixed at 500 ms): Windows {speed_o:.3f}, Linux {speed_r:.3f} "
      f"(ratio Linux/Windows {speed_r / speed_o:.3f}).", "", md(st), ""]

# ---------------------------------------------------------------- bootstrap conclusions
for f, cols in [("static_dev.csv", ["kappa", "scale", "budget_ms", "baseline", "metric"]),
                ("closed_loop_dev.csv", ["kappa", "scale", "baseline", "metric"])]:
    bo = pd.read_csv(ORIG / "results/bootstrap" / f)
    br = pd.read_csv(REPRO / "results/bootstrap" / f)
    m = bo.merge(br, on=cols, suffixes=("_win", "_lin"))
    m["sign_agrees"] = np.sign(m.diff_win) == np.sign(m.diff_lin)
    m["signif_agrees"] = m.significant_win == m.significant_lin
    main = m[m.metric.isin(["regret_pct", "utility_rate"])]
    L += [f"## 4. Bootstrap conclusions — {f}", "",
          f"{len(main)} AnytimeSwarm-vs-baseline comparisons on the main metric: sign agrees in "
          f"{main.sign_agrees.mean() * 100:.1f}%, significance verdict agrees in {main.signif_agrees.mean() * 100:.1f}%.", ""]
    dis = main[~main.signif_agrees]
    if len(dis):
        L += ["Comparisons whose significance verdict changed:", "",
              dis[cols + ["diff_win", "ci_lo_win", "ci_hi_win", "diff_lin", "ci_lo_lin", "ci_hi_lin"]]
              .round(4).to_markdown(index=False), ""]

# ---------------------------------------------------------------- closed loop
co_ = pd.read_csv(ORIG / "results/closed_loop/closed_loop_dev.csv")
cr_ = pd.read_csv(REPRO / "results/closed_loop/closed_loop_dev.csv")
cl = pd.concat([co_.assign(run="Windows"), cr_.assign(run="Linux")]).pivot_table(
    index=["kappa", "method"], columns="run", values=["utility_rate", "plan_ms_mean"])
cl = cl[[("utility_rate", "Windows"), ("utility_rate", "Linux"), ("plan_ms_mean", "Windows"), ("plan_ms_mean", "Linux")]]
L += ["## 5. Closed-loop missions (90 DEV missions)", "", md(cl), ""]

# ---------------------------------------------------------------- offline matched-compute test
mo_ = pd.read_csv(ORIG / "results/offline/matched_dev.csv")
mr_ = pd.read_csv(REPRO / "results/offline/matched_dev.csv")
k = ["kappa", "scale", "metric", "baseline"]
mm = mo_.merge(mr_, on=k, suffixes=("_win", "_lin"))
mm = mm[mm.scale == "all"]
L += ["## 6. Offline matched-compute test (scale = all)", "",
      mm[k + ["t_ours_win", "t_ours_lin", "diff_win", "diff_lin", "significant_better_win", "significant_better_lin"]]
      .round(4).to_markdown(index=False), ""]

out = J / "results" / "g0" / "compare.md"
out.write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"[ok] -> {out}")
