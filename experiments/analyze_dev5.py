"""Study 5 development analysis (dev seeds 0-9 only; results/tier_b/dev5_tune.csv).

Selection rule, as in studies 2 and 4: per disturbance level and late cost lam, the value with the highest mean
development score u_lam = utility_rate - lam * late_served / n_tasks over both window factors and kappa_B 10/50/200.
Selected per (level, lam):
    PropBest  the proportional buffer c in {0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1.2}, with or without the nominal
              fallback
    CCnf      the safety factor z in {-0.5, 0, 0.5, 1, 1.5} of the chance-constrained model without fallback
The first grid (dev5_tune.csv) selected values on its edge; the second (dev5_tune2.csv) extends it downwards.
The cost-aware fallback is not tuned (z of study 4, lam = late cost).

    python experiments/analyze_dev5.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAMS = [0.0, 0.5, 1.0, 2.0]


def family(m: str):
    o = m.split("~", 1)[1].split("+")[0] if "~" in m else ""
    if "lam=" in o:
        return "CA" + o.split("lam=")[1]
    if o.startswith("prop="):
        return "Prop"
    if o.startswith("z=") and ";" not in o and o != "z=auto4":
        return "CCnf"
    return {"z=auto4;fb=nominal": "CCfb", "mp=auto;fb=nominal": "MP", "mp=auto": "MPnf", "": "Forty",
            "buf=60": "Buf"}.get(o, m)


def main():
    tb = ROOT / "results" / "tier_b"
    d = pd.concat([pd.read_csv(f) for f in (tb / "dev5_tune.csv", tb / "dev5_tune2.csv") if f.exists()])
    d["fam"] = d.method.map(family)
    print(f"{len(d)} runs, {d.scenario.nunique()} missions, {d.method.nunique()} methods")
    for lam in LAMS:
        d[f"u{lam:g}"] = 100 * (d.utility_rate - lam * d.late_served / d.n_tasks)
    g = d.groupby(["exec_level", "method", "fam"])[[f"u{l:g}" for l in LAMS] + ["late_served"]].mean().reset_index()
    for lvl in ("mid", "high"):
        print(f"\n=== {lvl} ===")
        print(g[g.exec_level == lvl].sort_values("fam").drop(columns="exec_level").round(2).to_string(index=False))
    print("\nselection per (level, lam): best member of each tuned family, and the cost-aware fallback")
    for lvl in ("mid", "high"):
        s = g[g.exec_level == lvl]
        for lam in LAMS:
            col = f"u{lam:g}"
            row = [f"{lvl:4s} lam={lam:g}"]
            for fam in ("Prop", "CCnf"):
                b = s[s.fam == fam].sort_values(col).iloc[-1]
                row.append(f"{fam}: {b.method.split('~')[1].split('+')[0]} {b[col]:.2f}")
            ca = s[s.fam == f"CA{lam:g}"]
            if len(ca):
                row.append(f"CA: {ca[col].iloc[0]:.2f}")
            row.append(f"CCfb: {s[s.fam == 'CCfb'][col].iloc[0]:.2f}")
            print(" | ".join(row))


if __name__ == "__main__":
    main()
