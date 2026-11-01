"""Study 7 analysis (docs/16_PROTOCOL_V7.md): late-cost model of the cost-aware fallback (7a) and execution errors
outside the calibrated model (7b).

    python experiments/analyze_study7.py                       # held-out (results/tier_b/s7a_heldout_B.csv, s7b_*)
    python experiments/analyze_study7.py --dev                 # development files, report only

Scores: u_lam = U - lam n_late / n (fixed cost lam w_bar per late arrival, studies 5-6) and u^w_lam = U - lam R_late / R
(cost lam w_j, proportional to the reward). Statistics as in studies 2-6: per mission the paired difference is averaged
over the configurations, then a paired bootstrap over missions (10 000 resamples, 95% percentile CI, two-sided p);
non-inferiority: one-sided p = share of bootstrap means at or below -margin, superiority tested after NI in a fixed
sequence. Holm over each primary family:
    7a (lam = 1): H24 CA-fee - CA-prop on u_1; H25 CA-fee vs the proportional buffer tuned for u_1 (NI);
                  H26 CA-prop vs the proportional buffer tuned for u^w_1 (NI)
    7b (five shifted conditions s): H27s proposed model with nominal fallback - nominal model on U;
                  H28s cost-aware (prop, lam = 1) - nominal fallback on u_1
Writes paper_journal/tables/numbers_s7.tex (macros \\val{U...}), tables/tab_s7.tex, figures/fig_s7.pdf and
results/study7/report.md.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import holm  # noqa: E402
from analyze_study4 import NI_MARGIN, noninf, paired, regime, sup  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core.study7 import TUNED7  # noqa: E402

P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study7"
MAC, REPORT = {}, []
T, A = "+periodic:60", "alns_fixed@40~"
LAMS = {0.5: "Half", 1.0: "One", 2.0: "Two"}
SHIFTS = [("high_t3", "high", "Tthree", "Student-$t$ errors"), ("high_outlier", "high", "Outlier", "rare long delays"),
          ("high_uavbias", "high", "Bias", "speed bias per UAV"), ("high_gauss", "high_pareto", "Pareto",
                                                                   "Pareto latency")]
CONTROL = ("high_gauss", "high", "Gauss", "Gaussian (control)")
M7B = {"Forty": "alns_fixed@40" + T, "Buf": A + "buf=60" + T, "Prop": A + "prop=auto;fb=nominal" + T,
       "CCfb": A + "z=auto4;fb=nominal" + T, "CA": A + "z=auto4;lam=1" + T, "CAfee": A + "z=auto4;lam=1;cost=fee" + T,
       "MPCA": A + "mp=auto;lam=1" + T}
LAB7B = {"Forty": "Nominal model", "Buf": "Constant 60 s buffer", "Prop": "Proportional buffer",
         "CCfb": "Proposed, nominal fallback", "CA": "Proposed, cost-aware (prop.)",
         "CAfee": "Proposed, cost-aware (fixed)", "MPCA": "Moment propagation, cost-aware"}


def put(k, v):
    MAC["U" + k] = v


def ca(lam, cost):
    return A + f"z=auto4;lam={lam:g}" + (";cost=fee" if cost == "fee" else "") + T


def score(df, lam, kind):
    if kind == "fee":
        return df.assign(u=df.utility_rate - lam * df.late_served / df.n_tasks)
    return df.assign(u=df.utility_rate - lam * df.reward_late / df.reward_total)


def tuned(df, kind, lam, fam):
    """Rows of the member selected on development missions for (score, lam, family), per disturbance level."""
    parts = [df[(df.exec_level == lvl) & (df.method == A + o + T)] for lvl, o in TUNED7[kind][lam][fam].items()]
    if any(p.empty for p in parts):
        return df.iloc[:0]
    return pd.concat(parts).assign(method=f"{fam}@{kind}{lam:g}")


def num(name, m, lo, hi):
    put(f"D{name}", f"{m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]".replace("-", "$-$"))
    put(f"Dabs{name}", f"{abs(m) * 100:.2f}")
    put(f"CI{name}", f"{lo * 100:.2f} to {hi * 100:.2f}".replace("-", "$-$"))


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def study7a(df):
    put("ANRuns", f"{len(df):,}".replace(",", "\\,"))
    put("ANMissions", str(df.scenario.nunique()))
    have = set(df.method)
    tests = []
    rows = []
    for kind in ("fee", "w"):
        for lam, key in LAMS.items():
            x = score(df, lam, kind)
            x = pd.concat([x] + [tuned(x, kind, lam, f) for f in ("Prop", "CCnf")], ignore_index=True)
            comp = {"CAprop": ca(lam, "prop"), "Prop": f"Prop@{kind}{lam:g}", "CCnf": f"CCnf@{kind}{lam:g}",
                    "CCfb": A + "z=auto4;fb=nominal" + T, "Forty": "alns_fixed@40" + T}
            own = ca(lam, "fee")
            for cname, b in comp.items():
                if b not in set(x.method) or own not in have:
                    continue
                m, lo, hi, p = sup(paired(x, own, b, "u"))
                num(f"Fee{cname}{key}{kind.capitalize()}", m, lo, hi)
                rows.append((kind, lam, "fixed", cname, m, lo, hi, p))
            for cname in ("Prop", "CCnf", "CCfb", "Forty"):
                b, a = comp[cname], comp["CAprop"]
                if b not in set(x.method) or a not in have:
                    continue
                m, lo, hi, p = sup(paired(x, a, b, "u"))
                num(f"Prop{cname}{key}{kind.capitalize()}", m, lo, hi)
                rows.append((kind, lam, "prop.", cname, m, lo, hi, p))
            g = x.groupby("method").u.mean()
            for nm, spec in (("CAFee", own), ("CAProp", comp["CAprop"]), ("Prop", comp["Prop"]),
                             ("CCnf", comp["CCnf"]), ("CCfb", comp["CCfb"]), ("Forty", comp["Forty"])):
                if spec in g.index:
                    put(f"S{nm}{key}{kind.capitalize()}", f"{g[spec] * 100:.2f}")
            if lam == 1.0:
                if kind == "fee":
                    tests.append(("HTwentyFour", "sup", x, own, comp["CAprop"]))
                    tests.append(("HTwentyFive", "ni", x, own, comp["Prop"]))
                else:
                    tests.append(("HTwentySix", "ni", x, comp["CAprop"], comp["Prop"]))
    res = []
    for name, kind, x, a, b in tests:
        if a in set(x.method) and b in set(x.method):
            d = paired(x, a, b, "u")
            res.append((name, kind) + (sup(d) if kind == "sup" else noninf(d)) + (d,))
    adj = holm(np.array([r[5] for r in res])) if res else []
    REPORT.extend(["## 7a primary family, lam = 1, Holm (H24 CA-fee - CA-prop on u_1; H25 CA-fee vs tuned prop. buffer "
                   "on u_1, NI; H26 CA-prop vs tuned prop. buffer on u^w_1, NI)", "",
                   "| H | test | diff pp [95% CI] | p | p Holm | sup. p (NI only) |", "|---|---|---|---|---|---|"])
    for (name, kind, m, lo, hi, p, d), pa in zip(res, adj):
        num(name, m, lo, hi)
        put(f"P{name}", pv(pa))
        ok = pa < 0.05 and (kind == "ni" or m > 0)
        extra = ""
        if kind == "ni":
            m2, lo2, hi2, p2 = sup(d)
            put(f"PSup{name}", pv(p2))
            sup_ok = ok and p2 < 0.05 and m2 > 0
            put(f"Out{name}", "supported, sup." if sup_ok else ("supported" if ok else "not supported"))
            extra = f"{p2:.4f}"
        else:
            put(f"Out{name}", "supported" if ok else ("reversed" if pa < 0.05 else "not supported"))
        REPORT.append(f"| {name} | {kind} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] | {p:.4f} | {pa:.4f} | "
                      f"{extra} |")
    REPORT.extend(["", "## 7a all comparisons (cost-aware fallback minus method)", "",
                   "| score | lam | rule | vs | diff pp [95% CI] | p |", "|---|---|---|---|---|---|"])
    for kind, lam, rule, c, m, lo, hi, p in rows:
        REPORT.append(f"| {kind} | {lam:g} | {rule} | {c} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] | "
                      f"{p:.4f} |")
    for lam, key in LAMS.items():
        for kind in ("fee", "w"):
            for fam in ("Prop", "CCnf"):
                o = TUNED7[kind][lam][fam]
                put(f"Sel{fam}{key}{kind.capitalize()}", f"{o['mid']} / {o['high']}".replace(";fb=", ", fb "))
    # regimes, lam = 1
    for xl, wf, tag in (("mid", 1.0, "MidWOne"), ("mid", 0.5, "MidWHalf"), ("high", 1.0, "HighWOne"),
                        ("high", 0.5, "HighWHalf")):
        for kind in ("fee", "w"):
            x = score(regime(df, xl, wf), 1.0, kind)
            x = pd.concat([x, tuned(x, kind, 1.0, "Prop")], ignore_index=True)
            for rule in ("fee", "prop"):
                a, b = ca(1.0, rule), f"Prop@{kind}1"
                if a in set(x.method) and b in set(x.method):
                    m, lo, hi, p = sup(paired(x, a, b, "u"))
                    num(f"R{rule.capitalize()}{tag}{kind.capitalize()}", m, lo, hi)
    return rows


def study7b(df):
    put("BNRuns", f"{len(df):,}".replace(",", "\\,"))
    put("BNMissions", str(df.scenario.nunique()))
    res = []
    for xl, ll, key, lab in SHIFTS:
        sub = df[(df.exec_level == xl) & (df.latency_level == ll)]
        if sub.empty:
            continue
        res.append((f"HTwentySeven{key}", "U", sub, M7B["CCfb"], M7B["Forty"]))
        res.append((f"HTwentyEight{key}", "u1", sub, M7B["CA"], M7B["CCfb"]))
    out = []
    for name, metric, sub, a, b in res:
        x = score(sub, 1.0, "fee") if metric == "u1" else sub.assign(u=sub.utility_rate)
        d = paired(x, a, b, "u")
        out.append((name,) + sup(d))
    adj = holm(np.array([r[4] for r in out])) if out else []
    REPORT.extend(["", "## 7b primary family, Holm (H27 proposed + nominal fallback - nominal model on U; H28 "
                   "cost-aware - nominal fallback on u_1), per shifted condition", "",
                   "| H | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"])
    nsig = 0
    for (name, m, lo, hi, p), pa in zip(out, adj):
        num(name, m, lo, hi)
        put(f"P{name}", pv(pa))
        ok = pa < 0.05 and m > 0
        nsig += ok
        put(f"Out{name}", "supported" if ok else ("reversed" if pa < 0.05 else "not supported"))
        REPORT.append(f"| {name} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] | {p:.4f} | {pa:.4f} |")
    put("BNSig", str(nsig))
    put("BNTests", str(len(out)))
    # descriptive table: every method under every condition, U and u_1, and differences to the nominal model
    conds = [CONTROL] + SHIFTS
    REPORT.extend(["", "## 7b utility U and score u_1 (%) per condition", "",
                   "| method | " + " | ".join(c[3] for c in conds) + " |", "|---|" + "---|" * len(conds)])
    tab = {}
    for k, spec in M7B.items():
        cells = []
        for xl, ll, key, lab in conds:
            sub = df[(df.exec_level == xl) & (df.latency_level == ll) & (df.method == spec)]
            if sub.empty:
                cells.append(("--", "--"))
                continue
            u, u1 = sub.utility_rate.mean(), (sub.utility_rate - sub.late_served / sub.n_tasks).mean()
            cells.append((f"{u * 100:.2f}", f"{u1 * 100:.2f}"))
            put(f"BU{k}{key}", f"{u * 100:.2f}")
            put(f"BUone{k}{key}", f"{u1 * 100:.2f}")
        tab[k] = cells
        REPORT.append(f"| {k} | " + " | ".join(f"{a} / {b}" for a, b in cells) + " |")
    diffs = {}
    for xl, ll, key, lab in conds:
        sub = df[(df.exec_level == xl) & (df.latency_level == ll)]
        for k in ("Buf", "Prop", "CCfb", "CA", "CAfee", "MPCA"):
            for metric in ("U", "u1"):
                x = score(sub, 1.0, "fee") if metric == "u1" else sub.assign(u=sub.utility_rate)
                if M7B[k] in set(x.method) and M7B["Forty"] in set(x.method):
                    m, lo, hi, p = sup(paired(x, M7B[k], M7B["Forty"], "u"))
                    num(f"BD{k}{key}{'U' if metric == 'U' else 'One'}", m, lo, hi)
                    diffs[(k, key, metric)] = (m, lo, hi)
            if M7B["CA"] in set(sub.method) and M7B[k] in set(sub.method) and k != "CA":
                x = score(sub, 1.0, "fee")
                m, lo, hi, p = sup(paired(x, M7B["CA"], M7B[k], "u"))
                num(f"BCA{k}{key}", m, lo, hi)
        # finish-time error of the proposed model under this condition
        s = sub[sub.method == M7B["CA"]]
        if not s.empty:
            put(f"BErr{key}", f"{s.finish_err_mean_s.mean():.1f}")
            put(f"BErrP{key}", f"{s.finish_err_p95_s.mean():.1f}")
    # largest drop of the proposed advantage relative to the control
    for k in ("CCfb", "CA"):
        if (k, "Gauss", "U") in diffs:
            ctl = diffs[(k, "Gauss", "U")][0]
            worst = min((diffs[(k, c[2], "U")][0] for c in SHIFTS if (k, c[2], "U") in diffs), default=ctl)
            put(f"BCtl{k}", f"{ctl * 100:.2f}")
            put(f"BWorst{k}", f"{worst * 100:.2f}")
    return tab, diffs, conds


def figure(rows7a, diffs, conds):
    fig, ax = plt.subplots(1, 2, figsize=(7.16, 2.7))
    # (a) 7a: cost-aware fallback with the fixed and the proportional cost model minus the tuned buffer, per score
    a = ax[0]
    ys, labels = [], []
    y = 0
    colors = {"fixed": "#C62828", "prop.": "#1F6FC5"}
    for kind, sname in (("fee", "$u_\\lambda$ (fixed cost)"), ("w", "$u^w_\\lambda$ (cost $\\propto w_j$)")):
        for lam in LAMS:
            for rule in ("fixed", "prop."):
                r = [x for x in rows7a if x[0] == kind and x[1] == lam and x[2] == rule and x[3] == "Prop"]
                if not r:
                    continue
                _, _, _, _, m, lo, hi, _ = r[0]
                a.errorbar(m * 100, y, xerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt="o", ms=3.5,
                           color=colors[rule], capsize=2, lw=1)
                y += 1
            labels.append((y - 1.5, f"{sname}, $\\lambda={lam:g}$"))
        y += 0.6
    a.axvline(0, color="black", lw=0.8)
    a.set_yticks([v for v, _ in labels])
    a.set_yticklabels([t for _, t in labels], fontsize=7)
    a.invert_yaxis()
    a.set_xlabel("cost-aware fallback minus tuned buffer (pp)")
    a.plot([], [], "o", color=colors["fixed"], label="fixed-cost rule")
    a.plot([], [], "o", color=colors["prop."], label="proportional rule")
    a.legend(loc="lower right", frameon=False, fontsize=7)
    a.set_title("(a) study 7a", fontsize=9)
    # (b) 7b: methods minus the nominal model on U, per condition
    b = ax[1]
    ks = [("CCfb", "#1F6FC5", "proposed, nominal fb"), ("CA", "#C62828", "proposed, cost-aware"),
          ("Prop", "#8C6D1F", "proportional buffer"), ("MPCA", "#6A4BB5", "moment prop., cost-aware")]
    for i, (k, c, lab) in enumerate(ks):
        xs, ms, los, his = [], [], [], []
        for j, cond in enumerate(conds):
            if (k, cond[2], "U") in diffs:
                m, lo, hi = diffs[(k, cond[2], "U")]
                xs.append(j + (i - 1.5) * 0.17)
                ms.append(m * 100)
                los.append((m - lo) * 100)
                his.append((hi - m) * 100)
        b.errorbar(xs, ms, yerr=[los, his], fmt="o", ms=3, color=c, capsize=1.5, lw=0.9, label=lab)
    b.axhline(0, color="black", lw=0.8)
    b.set_xticks(range(len(conds)))
    b.set_xticklabels([c[3].replace(" (control)", "\n(control)") for c in conds], fontsize=6.5, rotation=20)
    b.set_ylabel("$U$ minus nominal model (pp)")
    b.legend(loc="upper right", frameon=False, fontsize=6.5)
    b.set_title("(b) study 7b, high disturbances", fontsize=9)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s7.pdf")


def table(tab, conds):
    lines = ["% generated by experiments/analyze_study7.py -- do not edit",
             "\\begin{table*}[t]",
             "\\caption{Study~7b, tier B, held-out seeds 14000--14029, high disturbances: utility $U$ / score $u_1$ (\\%) "
             "of every method when the execution errors leave the calibrated Gaussian model. The error model, $z$ and "
             "every tuned parameter are those of the calibrated level.}\\label{tab:s7}",
             "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{@{}l" + "c" * len(conds) + "@{}}", "\\toprule",
             "Method & " + " & ".join(c[3] for c in conds) + " \\\\", "\\midrule"]
    for k, cells in tab.items():
        lines.append(f"{LAB7B[k]} & " + " & ".join(f"{a} / {b}" for a, b in cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (P / "tables" / "tab_s7.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    fa = TB / ("dev7a.csv" if a.dev else "s7a_heldout_B.csv")
    fb = [TB / f for f in (("dev7b.csv", "dev7b_lat.csv") if a.dev else ("s7b_heldout_B.csv", "s7b_lat_heldout_B.csv"))]
    REPORT.extend([f"# Study 7 ({'dev' if a.dev else 'held-out'})", ""])
    rows7a = study7a(pd.read_csv(fa)) if fa.exists() else []
    tab, diffs, conds = ({}, {}, [])
    if all(f.exists() for f in fb):
        tab, diffs, conds = study7b(pd.concat([pd.read_csv(f) for f in fb], ignore_index=True))
    print("\n".join(REPORT))
    if a.dev:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    with open(P / "tables" / "numbers_s7.tex", "w", encoding="utf-8") as fh:
        fh.write("% generated by experiments/analyze_study7.py -- do not edit\n")
        for k, v in sorted(MAC.items()):
            fh.write(f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}\n")
    if rows7a and diffs:
        figure(rows7a, diffs, conds)
    if tab:
        table(tab, conds)


if __name__ == "__main__":
    main()
