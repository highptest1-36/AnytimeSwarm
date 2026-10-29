"""Study 4C analysis (docs/12_PROTOCOL_V4.md section 7): PX4/Gazebo flights under high disturbances with halved windows.

    python experiments/analyze_study4c.py --stage interim     # seeds 9000-9005 (18 missions): stop or continue
    python experiments/analyze_study4c.py --stage final       # all missions; writes numbers_s4c.tex, report
    python experiments/analyze_study4c.py --stage interim --write   # after an early stop at the interim bound

Primary family (Holm over two tests), proposed with fallback minus
    H14: the same search on the nominal model (alns_fixed@40, periodic),
    H15: proposed without the fallback (study 2 model with the study 4 safety factor).
Group-sequential design with one interim analysis at half the missions and O'Brien-Fleming bounds for two looks
(two-sided alpha 0.05): interim nominal level 0.0052, final 0.048. Statistics: paired bootstrap over missions
(10 000 resamples, 95% percentile CI, two-sided p), Holm within each look. Valid real-time factor [1.6, 2.2]; a run
outside is repeated once with the same seed, and the repeat replaces it (sensitivity analysis with the originals).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_study2 import ci, holm, pp, pval

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "results" / "tier_c" / "s4_heldout_C"
BGZ = ROOT / "results" / "tier_b" / "s4c_heldout_B_gz.csv"
P = ROOT / "paper_journal"
OUT = ROOT / "results" / "study4"
FB, NOFB, NOM = "proposed~z=0.5,fb=nominal", "proposed~z=0.5", "alns_fixed@40"
B_OF = {FB: "proposed~z=0.5;fb=nominal+periodic:60", NOFB: "proposed~z=0.5+periodic:60",
        NOM: "alns_fixed@40+periodic:60"}
BOUND = {"interim": 0.0052, "final": 0.048}
INTERIM_SEEDS = range(9000, 9006)
MAC, REPORT = {}, []


def put(k, v):
    MAC["G" + k] = v


def boot(d, n=10_000, seed=0):
    d = np.asarray(d, float)
    m = d[np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))].mean(axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float(min(2 * min(np.mean(m <= 0), np.mean(m >= 0)), 1.0))


def load(d: Path, originals=False):
    rows = []
    for f in sorted(d.glob("gz-*.json")):
        m = json.loads(f.read_text())
        rows.append({"scenario": m["scenario"], "seed": int(m["seed"]), "method": m["method"],
                     "u": m["utility_rate"], "late": m["late_served"], "rtf": m["rtf"],
                     "ms": m["plan_ms_mean"], "skip": m.get("skipped", np.nan)})
    df = pd.DataFrame(rows)
    if originals and (d / "invalid_rtf").exists():
        orig = load(d / "invalid_rtf")
        df = pd.concat([df.set_index(["scenario", "method"]).drop(orig.set_index(["scenario", "method"]).index,
                                                                  errors="ignore").reset_index(), orig])
    return df


def paired(df, a, b, col="u"):
    w = df.pivot_table(index="scenario", columns="method", values=col).dropna(subset=[a, b])
    return (w[a] - w[b]) if a in w and b in w else pd.Series(dtype=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["interim", "final"], default="final")
    ap.add_argument("--write", action="store_true", help="write outputs (final stage, or interim after an early stop)")
    a = ap.parse_args()
    df = load(C)
    if a.stage == "interim":
        df = df[df.seed.isin(INTERIM_SEEDS)]
    complete = df.groupby("scenario").method.nunique()
    df = df[df.scenario.isin(complete[complete == 3].index)]
    n = df.scenario.nunique()
    tests = [("Nom", NOM), ("NoFb", NOFB)]
    res = [(k,) + boot(paired(df, FB, b)) for k, b in tests]
    adj = holm(np.array([r[4] for r in res]))
    lvl = BOUND[a.stage]
    stop = all(p < lvl and r[1] > 0 for r, p in zip(res, adj))
    REPORT.append(f"# Study 4C, {a.stage} analysis: {n} missions, {len(df)} flights, bound {lvl}")
    REPORT.append(f"RTF mean {df.rtf.mean():.2f}, min {df.rtf.min():.2f}, valid {(df.rtf.between(1.6, 2.2)).mean():.2%}")
    for (k, m, lo, hi, p), pa in zip(res, adj):
        REPORT.append(f"FB minus {k}: {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] p {p:.4f} p_Holm {pa:.4f} "
                      f"{'reject' if pa < lvl else 'not rejected'}")
        put(f"D{k}", ci(m, lo, hi))
        put(f"P{k}", pval(pa))
        put(f"Sig{k}", "yes" if (pa < lvl and m > 0) else "no")
    REPORT.append(f"decision: {'STOP (all primary hypotheses rejected at the interim bound)' if stop else 'continue'}"
                  if a.stage == "interim" else "final analysis")
    g = df.groupby("method").agg(u=("u", "mean"), late=("late", "mean"), ms=("ms", "mean"), rtf=("rtf", "mean"))
    REPORT.append(g.round(4).to_string())
    for k, s in [("FB", FB), ("NoFb", NOFB), ("Nom", NOM)]:
        if s in g.index:
            put(f"U{k}", pp(g.loc[s, "u"]))
            put(f"Late{k}", f"{g.loc[s, 'late']:.2f}")
            put(f"Ms{k}", f"{g.loc[s, 'ms']:.1f}")
    put("N", str(n))
    put("NFlights", str(len(df)))
    put("RTF", f"{df.rtf.mean():.2f}")
    put("Valid", f"{100 * df.rtf.between(1.6, 2.2).mean():.0f}")
    put("Stage", a.stage)
    if a.stage == "final" or a.write:
        # sensitivity: original runs instead of the repeats
        if (C / "invalid_rtf").exists():
            do = load(C, originals=True)
            do = do[do.scenario.isin(df.scenario.unique())]
            for k, b in tests:
                m, lo, hi, p = boot(paired(do, FB, b))
                put(f"D{k}Orig", ci(m, lo, hi))
                REPORT.append(f"sensitivity (original runs) FB minus {k}: {ci(m, lo, hi)} p {p:.4f}")
        if BGZ.exists():
            b = pd.read_csv(BGZ)
            b["method_c"] = b.method.map({v: k for k, v in B_OF.items()})
            for k, s in tests:
                bb = b.pivot_table(index="scenario", columns="method_c", values="utility_rate")
                m, lo, hi, _ = boot(bb[FB] - bb[s])
                put(f"B{k}", ci(m, lo, hi))
                REPORT.append(f"tier B prediction FB minus {k}: {ci(m, lo, hi)}")
            mrg = df.merge(b.rename(columns={"method_c": "mc"})[["scenario", "mc", "utility_rate"]],
                           left_on=["scenario", "method"], right_on=["scenario", "mc"])
            r = np.corrcoef(mrg.u, mrg.utility_rate)[0, 1]
            put("BCr", f"{r:.2f}")
            REPORT.append(f"tier B vs tier C per run: r = {r:.2f} (n={len(mrg)})")
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "report_4c.md").write_text("\n".join(REPORT) + "\n")
        lines = ["% generated by experiments/analyze_study4c.py -- do not edit"]
        lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
        (P / "tables" / "numbers_s4c.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(REPORT))
    return 0 if (a.stage == "final" or not stop) else 3


if __name__ == "__main__":
    raise SystemExit(main())
