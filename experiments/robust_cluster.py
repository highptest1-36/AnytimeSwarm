"""Robustness of the tier B hypothesis tests to the resampling unit (reviewer audit, docs/15_PLAN_REVIEW_RESPONSE.md).

The primary analyses resample missions. The nine missions of one seed (three fleet scales x three event profiles) have
independent scenarios, but the execution disturbances are keyed to the seed, the UAV and the task
(journal_core/execution.py), so they share the wind direction and the per-leg error streams. This script repeats every
tier B primary test of studies 2-7 with a paired cluster bootstrap that resamples seeds (30 clusters of nine missions,
the paired difference of a mission averaged over the configurations as in the primary analyses), and compares the
intervals, p-values and Holm-adjusted outcomes with the mission bootstrap. Tier C hypotheses (H4, H14, H15) have one
mission per seed and are not affected. Exploratory; no new runs.

    python experiments/robust_cluster.py   ->  paper_journal/tables/tab_cluster.tex, tables/numbers_robust.tex
                                                (macros \\val{V...}), results/robust/report_cluster.md
"""
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_study2 import holm
from analyze_study4 import NI_MARGIN, paired, regime
import analyze_study5 as a5

ROOT = Path(__file__).resolve().parents[1]
TB, P, OUT = ROOT / "results" / "tier_b", ROOT / "paper_journal", ROOT / "results" / "robust"
T, A = "+periodic:60", "alns_fixed@40~"
N_BOOT = 10_000


def seed_of(scenario: str) -> int:
    return int(scenario.split("-")[2])


def boots(d: pd.Series, level=95, n=N_BOOT, seed=0):
    """Mission bootstrap and seed-cluster bootstrap of the mean of d (index: scenario) -> two arrays of means."""
    x = d.values
    rng = np.random.default_rng(seed)
    mb = x[rng.integers(0, x.size, size=(n, x.size))].mean(axis=1)
    g = pd.DataFrame({"x": x, "s": [seed_of(s) for s in d.index]}).groupby("s").x.agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    idx = np.random.default_rng(seed).integers(0, len(s), size=(n, len(s)))
    cb = s[idx].sum(axis=1) / c[idx].sum(axis=1)
    return float(x.mean()), mb, cb, len(s)


def summarise(m, b, kind, level=95):
    a = (100 - level) / 2
    lo, hi = np.percentile(b, [a, 100 - a])
    if kind == "ni":
        p = float(np.mean(b <= -NI_MARGIN))
    else:
        p = float(min(2 * min(np.mean(b <= 0), np.mean(b >= 0)), 1.0))
    return lo, hi, p


def main():
    s2, s3, s4 = (pd.read_csv(TB / f) for f in ("s2_heldout_B.csv", "s3_heldout_B.csv", "s4_heldout_B.csv"))
    s5, s6 = pd.read_csv(TB / "s5_heldout_B.csv"), pd.read_csv(TB / "s6_heldout_B.csv")
    s5 = pd.concat([s5, a5.tuned(s5, "Prop", 1.0), a5.tuned(s5, "CCnf", 1.0)], ignore_index=True)
    s5 = s5.assign(u1=s5.utility_rate - s5.late_served / s5.n_tasks)
    s6 = s6.assign(u1=s6.utility_rate - s6.late_served / s6.n_tasks)
    prop2, fb3 = "proposed+periodic:60", "proposed~z=auto;fb=nominal+periodic:60"
    import yaml
    fb3 = yaml.safe_load((ROOT / "experiments" / "configs" / "S3_B.yaml").read_text())["grid"]["methods"][0]
    cc4, ca = A + "z=auto4;fb=nominal" + T, A + "z=auto4;lam=1" + T
    # (family, H, label, data, a, b, metric, kind)
    H = [("2a", "H1", "vs. ALNS 40 ms", s2, prop2, "alns_fixed@40" + T, "utility_rate", "sup"),
         ("2a", "H1", "vs. size-scaled budget", s2, prop2, "alns_scaled~ms=1" + T, "utility_rate", "sup"),
         ("2a", "H1", "vs. online prediction", s2, prop2, "online_curve" + T, "utility_rate", "sup"),
         ("2a", "H1", "vs. performance profile", s2, prop2, "profile" + T, "utility_rate", "sup"),
         ("2a", "H1", "vs. AnytimeSwarm-R", s2, prop2, "anytime_risk" + T, "utility_rate", "sup"),
         ("2a", "H1", "vs. constant buffer", s2, prop2, A + "buf=60" + T, "utility_rate", "sup"),
         ("2b", "H2", "vs. conventional", s2, prop2, "alns_fixed@40+event", "utility_rate", "sup"),
         ("2c", "H3", "stopping rule vs. fixed 40 ms", s2, prop2, "alns_fixed@40~z=auto" + T, "utility_rate", "tost"),
         ("3", "H5", "fallback vs. no fallback", s3, fb3, prop2, "utility_rate", "sup"),
         ("3", "H6", "vs. buffer, high, $\\times0.5$", regime(s3, "high", 0.5), fb3, A + "buf=60" + T,
          "utility_rate", "sup"),
         ("3", "H7", "vs. ALNS 40 ms", s3, fb3, "alns_fixed@40" + T, "utility_rate", "sup"),
         ("3", "H8", "vs. constant buffer", s3, fb3, A + "buf=60" + T, "utility_rate", "sup"),
         ("4", "H9", "vs. proportional buffer", s4, cc4, A + "prop=auto;fb=nominal" + T, "utility_rate", "sup"),
         ("4", "H10", "vs. moment propagation (NI)", s4, cc4, A + "mp=auto;fb=nominal" + T, "utility_rate", "ni"),
         ("4", "H11", "MP: fallback vs. none", s4, A + "mp=auto;fb=nominal" + T, A + "mp=auto" + T, "utility_rate",
          "sup"),
         ("4", "H12", "vs. constant buffer", s4, cc4, A + "buf=60" + T, "utility_rate", "sup"),
         ("4", "H13", "vs. nominal model", s4, cc4, "alns_fixed@40" + T, "utility_rate", "sup"),
         ("5", "H16", "vs. nominal fallback", s5, ca, cc4, "u1", "sup"),
         ("5", "H17", "vs. tuned prop. buffer (NI)", s5, ca, "Prop@1", "u1", "ni"),
         ("5", "H18", "vs. tuned $z$, no fallback (NI)", s5, ca, "CCnf@1", "u1", "ni"),
         ("5", "H19", "vs. nominal model", s5, ca, "alns_fixed@40" + T, "u1", "sup"),
         ("6", "H20", "vs. CBBA", s6, ca, "cbba" + T, "u1", "sup"),
         ("6", "H21", "CBBA on proposed model vs. CBBA", s6, "cbba~z=auto4;lam=1" + T, "cbba" + T, "u1", "sup"),
         ("6", "H22", "MP: cost-aware vs. nominal fb", s6, A + "mp=auto;lam=1" + T, A + "mp=auto;fb=nominal" + T,
          "u1", "sup"),
         ("6", "H23", "MP: cost-aware vs. no fallback", s6, A + "mp=auto;lam=1" + T, A + "mp=auto" + T, "u1", "sup")]
    f7a, f7b = TB / "s7a_heldout_B.csv", [TB / "s7b_heldout_B.csv", TB / "s7b_lat_heldout_B.csv"]
    if f7a.exists() and all(f.exists() for f in f7b):
        import analyze_study7 as a7
        s7 = pd.read_csv(f7a)
        xf = a7.score(s7, 1.0, "fee")
        xf = pd.concat([xf, a7.tuned(xf, "fee", 1.0, "Prop")], ignore_index=True).assign(u1=lambda d: d.u)
        xw = a7.score(s7, 1.0, "w")
        xw = pd.concat([xw, a7.tuned(xw, "w", 1.0, "Prop")], ignore_index=True).assign(u1=lambda d: d.u)
        fee = A + "z=auto4;lam=1;cost=fee" + T
        H += [("7a", "H24", "fixed-cost vs. proportional rule", xf, fee, ca, "u1", "sup"),
              ("7a", "H25", "fixed-cost rule vs. tuned buffer (NI)", xf, fee, "Prop@fee1", "u1", "ni"),
              ("7a", "H26", "prop. rule vs. buffer tuned for $u^w_1$ (NI)", xw, ca, "Prop@w1", "u1", "ni")]
        b = pd.concat([pd.read_csv(f) for f in f7b], ignore_index=True)
        b = b.assign(u1=b.utility_rate - b.late_served / b.n_tasks)
        for xl, ll, key, lab in a7.SHIFTS:
            sub = b[(b.exec_level == xl) & (b.latency_level == ll)]
            H += [("7b", "H27", f"{lab}: nominal fb vs. nominal", sub, cc4, "alns_fixed@40" + T, "utility_rate",
                   "sup"),
                  ("7b", "H28", f"{lab}: cost-aware vs. nominal fb", sub, ca, cc4, "u1", "sup")]
    rows = []
    for fam, h, lab, df, a, b, metric, kind in H:
        d = paired(df, a, b, metric)
        lvl = 90 if kind == "tost" else 95
        m, mb, cb, ncl = boots(d, lvl)
        r1, r2 = summarise(m, mb, kind, lvl), summarise(m, cb, kind, lvl)
        rows.append(dict(fam=fam, h=h, lab=lab, kind=kind, m=m, n=d.size, ncl=ncl, lo1=r1[0], hi1=r1[1], p1=r1[2],
                         lo2=r2[0], hi2=r2[1], p2=r2[2]))
    R = pd.DataFrame(rows)
    for col in ("1", "2"):
        R["pa" + col] = np.nan
        for fam, g in R[R.kind != "tost"].groupby("fam"):
            R.loc[g.index, "pa" + col] = holm(g["p" + col].values)

    def outcome(r, c):
        if r.kind == "tost":
            return "equivalent" if r["lo" + c] > -NI_MARGIN and r["hi" + c] < NI_MARGIN else "not shown"
        ok = r["pa" + c] < 0.05
        if r.kind == "ni":
            return "NI shown" if ok else "NI not shown"
        return ("supported" if r.m > 0 else "reversed") if ok else "not supported"

    R["out1"] = [outcome(r, "1") for _, r in R.iterrows()]
    R["out2"] = [outcome(r, "2") for _, r in R.iterrows()]
    R["ratio"] = (R.hi2 - R.lo2) / (R.hi1 - R.lo1)
    OUT.mkdir(parents=True, exist_ok=True)
    rep = ["# Seed-cluster bootstrap vs mission bootstrap, tier B primary hypotheses", "",
           "| H | comparison | diff pp | mission CI | p Holm | seed-cluster CI | p Holm | width ratio | outcome |",
           "|---|---|---|---|---|---|---|---|---|"]
    f = lambda v: f"{v * 100:+.2f}"
    for _, r in R.iterrows():
        rep.append(f"| {r.h} | {r.lab} | {f(r.m)} | [{f(r.lo1)}, {f(r.hi1)}] | {r.pa1:.4f} | [{f(r.lo2)}, {f(r.hi2)}] | "
                   f"{r.pa2:.4f} | {r.ratio:.2f} | {r.out1} -> {r.out2} |")
    changed = int((R.out1 != R.out2).sum())
    rep += ["", f"outcomes changed: {changed} of {len(R)}; width ratio min {R.ratio.min():.2f}, median "
                f"{R.ratio.median():.2f}, max {R.ratio.max():.2f}"]
    (OUT / "report_cluster.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))

    mac = {"VClNTests": str(len(R)), "VClNChanged": str(changed), "VClNClusters": str(int(R.ncl.min())),
           "VClRatioMin": f"{R.ratio.min():.2f}", "VClRatioMax": f"{R.ratio.max():.2f}",
           "VClRatioMed": f"{R.ratio.median():.2f}"}
    h9 = R[R.h == "H9"].iloc[0]
    mac["VClHNineCI"] = f"{h9.lo2 * 100:.2f} to {h9.hi2 * 100:.2f}".replace("-", "$-$")
    mac["VClHNineP"] = f"{h9.pa2:.3f}"
    with open(P / "tables" / "numbers_robust.tex", "w", encoding="utf-8") as fh:
        fh.write("% generated by experiments/robust_cluster.py -- do not edit\n")
        for k, v in sorted(mac.items()):
            fh.write(f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}\n")

    s = lambda v: f"{v * 100:+.2f}".replace("-", "$-$")
    pv = lambda p: "$<$0.001" if p < 0.001 else f"{p:.3f}"
    lines = ["% generated by experiments/robust_cluster.py -- do not edit",
             "\\begin{table*}[t]",
             "\\caption{Sensitivity of the tier B primary tests to the resampling unit. Mission: paired bootstrap over "
             "270 missions, as in the primary analyses. Seed cluster: paired bootstrap over the 30 seeds, each with "
             "its nine missions, which share the execution disturbances. Differences in pp, 95\\% intervals (90\\% for "
             "the equivalence test H3), Holm-adjusted $p$ within each primary family; for NI tests, $p$ is the "
             "one-sided $p$ of non-inferiority with a margin of $-0.5$\\,pp.}\\label{tab:Scluster}",
             "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{@{}llrlrlrl@{}}", "\\toprule",
             "H & Comparison & Diff. & Mission interval & $p$ & Seed-cluster interval & $p$ & Outcome (both) \\\\",
             "\\midrule"]
    for _, r in R.iterrows():
        both = r.out1 if r.out1 == r.out2 else f"{r.out1} / {r.out2}"
        pa1 = "--" if r.kind == "tost" else pv(r.pa1)
        pa2 = "--" if r.kind == "tost" else pv(r.pa2)
        lines.append(f"{r.h} & {r.lab} & {s(r.m)} & [{s(r.lo1)}, {s(r.hi1)}] & {pa1} & [{s(r.lo2)}, {s(r.hi2)}] & "
                     f"{pa2} & {both} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (P / "tables" / "tab_cluster.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
