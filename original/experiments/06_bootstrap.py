"""Step 6 - paired bootstrap at SCENARIO level (static) and MISSION level (closed loop).

    python experiments/06_bootstrap.py --split test

Static: snapshot results are first averaged per (scenario, budget[, kappa]) so the resampled unit is
an independent scenario, not correlated snapshots of one mission.
A claim "AnytimeSwarm is better" needs the 95% CI of (ours - baseline) to exclude 0 in the good
direction (lower regret / lower time / higher utility).
Output: results/bootstrap/static_<split>.csv, results/bootstrap/closed_loop_<split>.csv
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.analysis import at_kappa, load_static, paired_bootstrap  # noqa: E402
from anytimeswarm.utils import load_config, rpath  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--ours", default="anytime")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    cfg = load_config(args.config)
    res = rpath(cfg["paths"]["results_dir"])
    out_dir = res / "bootstrap"
    out_dir.mkdir(parents=True, exist_ok=True)

    static_p = res / "static" / f"static_{args.split}{args.tag}.csv"
    if static_p.exists():
        df = load_static(cfg, args.split, args.tag)
        rows = []
        for k in cfg["kappas"]:
            dk = at_kappa(df, k)
            metrics = ["regret_pct", "elapsed_ms", f"net_regret_k{k}"]
            agg = dk.groupby(["scenario", "scale", "budget_ms", "method"])[metrics].mean().reset_index()
            for (scale, B), g in agg.groupby(["scale", "budget_ms"]):
                piv = {m: g.pivot_table(index="scenario", columns="method", values=m) for m in metrics}
                for base in [m for m in piv["regret_pct"].columns if m != args.ours]:
                    for m in metrics:
                        p = piv[m][[args.ours, base]].dropna()
                        if len(p) < 3:
                            continue
                        r = paired_bootstrap(p[args.ours], p[base], seed=cfg["seed"])
                        rows.append({"kappa": k, "scale": scale, "budget_ms": B, "baseline": base,
                                     "metric": m.replace(f"_k{k}", ""), **r,
                                     "significant": r["ci_hi"] < 0 or r["ci_lo"] > 0})
        out = pd.DataFrame(rows).drop_duplicates(subset=["kappa", "scale", "budget_ms", "baseline", "metric"])
        out.to_csv(out_dir / f"static_{args.split}{args.tag}.csv", index=False)
        s = out[(out.metric == "net_regret") & (out.baseline == "alns_fixed")]
        print("AnytimeSwarm - ALNS(fixed B), net regret (negative = ours better):")
        print(s[["kappa", "scale", "budget_ms", "diff", "ci_lo", "ci_hi"]].round(3).to_string(index=False))

    cl_p = res / "closed_loop" / f"closed_loop_{args.split}{args.tag}.csv"
    if cl_p.exists():
        cl = pd.read_csv(cl_p)
        rows = []
        for (k, scale), g in cl.groupby(["kappa", "scale"]):
            for m in ["utility_rate", "completion_rate", "mission_J", "plan_ms_total", "dropped_by_delay"]:
                piv = g.pivot_table(index="scenario", columns="method", values=m)
                if args.ours not in piv:
                    continue
                for base in [c for c in piv.columns if c != args.ours]:
                    p = piv[[args.ours, base]].dropna()
                    r = paired_bootstrap(p[args.ours], p[base], seed=cfg["seed"])
                    rows.append({"kappa": k, "scale": scale, "baseline": base, "metric": m, **r,
                                 "significant": r["ci_hi"] < 0 or r["ci_lo"] > 0})
        pd.DataFrame(rows).to_csv(out_dir / f"closed_loop_{args.split}{args.tag}.csv", index=False)
        print(f"[ok] closed-loop bootstrap: {len(rows)} comparisons")
    print(f"[ok] -> {out_dir}")


if __name__ == "__main__":
    main()
