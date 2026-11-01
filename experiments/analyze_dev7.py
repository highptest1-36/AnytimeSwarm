"""Study 7 development analysis (dev seeds 0-9 only, before the freeze of docs/16_PROTOCOL_V7.md).

7a: selects the tuned competitors for every late cost lam in {0.5, 1, 2}, disturbance level and score, by the rule of
study 5 (the member of the family with the best mean score over the development missions and configurations):
    Prop  proportional buffer c in {0.1, ..., 1.2}, with the nominal fallback or without fallback
    CCnf  proposed model without fallback, z in {-0.5, 0, 0.5, 1, 1.5}
    scores: fee  u_lam   = U - lam n_late / n            (fixed cost lam w_bar per late arrival, studies 5-6)
            w    u^w_lam = U - lam R_late / R_total      (cost lam w_j, proportional to the reward)
and prints the development differences of the cost-aware fallback with both cost models (for the sample size only;
nothing of the fallback is tuned). The selection is copied into journal_core/study7.TUNED7 before the freeze.
7b: prints the size of the shifted execution errors (finish-time error, share on time, ECE) per level.

    python experiments/analyze_dev7.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_study4 import paired

ROOT = Path(__file__).resolve().parents[1]
TB = ROOT / "results" / "tier_b"
T, A = "+periodic:60", "alns_fixed@40~"
LAMS = (0.5, 1.0, 2.0)


def score(df, lam, kind):
    if kind == "fee":
        return df.utility_rate - lam * df.late_served / df.n_tasks
    return df.utility_rate - lam * df.reward_late / df.reward_total


def family(fam):
    if fam == "Prop":
        return [f"prop={c};fb={fb}" for c in ("0.1", "0.2", "0.3", "0.45", "0.6", "0.75", "0.9", "1.2")
                for fb in ("nominal", "none")]
    return [f"z={z}" for z in ("-0.5", "0", "0.5", "1", "1.5")]


def main():
    df = pd.read_csv(TB / "dev7a.csv")
    print(f"dev7a: {len(df)} runs, {df.scenario.nunique()} missions, {df.method.nunique()} methods")
    sel = {}
    for kind in ("fee", "w"):
        sel[kind] = {}
        for lam in LAMS:
            sel[kind][lam] = {}
            x = df.assign(u=score(df, lam, kind))
            for fam in ("Prop", "CCnf"):
                sel[kind][lam][fam] = {}
                for lvl in ("mid", "high"):
                    g = x[x.exec_level == lvl].groupby("method").u.mean()
                    cand = {o: g.get(A + o + T, np.nan) for o in family(fam)}
                    best = max(cand, key=lambda o: -np.inf if np.isnan(cand[o]) else cand[o])
                    top = sorted(cand.items(), key=lambda kv: -kv[1])[:3]
                    print(f"{kind:3s} lam={lam:<3g} {fam:4s} {lvl:4s} -> {best:18s} "
                          + "  ".join(f"{o}:{v * 100:.2f}" for o, v in top))
                    sel[kind][lam][fam][lvl] = best
    print("\nTUNED7 =", sel)

    print("\n# cost-aware fallback, development differences (pp, mean over missions)")
    for lam in LAMS:
        fee, prop = A + f"z=auto4;lam={lam:g};cost=fee" + T, A + f"z=auto4;lam={lam:g}" + T
        for kind in ("fee", "w"):
            x = df.assign(u=score(df, lam, kind))
            d = paired(x, fee, prop, "u")
            tf = [o for o in (sel[kind][lam]["Prop"][lv] for lv in ("mid", "high"))]
            parts = [x[(x.exec_level == lv) & (x.method == A + sel[kind][lam]["Prop"][lv] + T)]
                     for lv in ("mid", "high")]
            tuned = pd.concat(parts).assign(method="Prop*")
            y = pd.concat([x, tuned])
            dpf, dpp = paired(y, fee, "Prop*", "u"), paired(y, prop, "Prop*", "u")
            print(f"lam={lam:<3g} score={kind:3s}: fee-prop {d.mean() * 100:+.2f} (sd {d.std() * 100:.2f}); "
                  f"fee-tunedProp {dpf.mean() * 100:+.2f}; prop-tunedProp {dpp.mean() * 100:+.2f}  [{tf}]")

    for f in ("dev7b.csv", "dev7b_lat.csv"):
        p = TB / f
        if not p.exists():
            continue
        d7 = pd.read_csv(p)
        print(f"\n# {f}: {len(d7)} runs")
        g = d7.groupby(["exec_level", "latency_level", "method"]).agg(
            U=("utility_rate", "mean"), late=("late_served", "mean"), err=("finish_err_mean_s", "mean"),
            err95=("finish_err_p95_s", "mean"))
        print(g.to_string())


if __name__ == "__main__":
    main()
