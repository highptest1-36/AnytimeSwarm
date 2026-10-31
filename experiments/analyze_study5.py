"""Study 5 analysis (docs/13_PROTOCOL_V5.md): the cost-aware fallback against competitors tuned for each late cost.

    python experiments/analyze_study5.py                                     # held-out (results/tier_b/s5_heldout_B.csv)
    python experiments/analyze_study5.py --csv results/tier_b/dev5_tune.csv --dev   # dev check, no outputs

Score: u_lam = utility_rate - lam * late_served / n_tasks (a late arrival costs lam mean task rewards). The cost-aware
fallback CA(lam) is run with the late cost it is scored with. The tuned competitors (journal_core/study5.TUNED) use,
per disturbance level, the member of their family with the best development score at that lam. Statistics as in
studies 2-4: per mission the paired difference is averaged over the configurations, then a paired bootstrap over
missions (10 000 resamples, 95% percentile CI, two-sided p); non-inferiority: one-sided p = share of bootstrap means at
or below -margin. Holm over the primary family (lam = 1); the superiority tests of H17 and H18 follow their
non-inferiority tests in a fixed sequence.

Writes paper_journal/tables/numbers_s5.tex (macros \\val{F...}), tables/tab_s5.tex, figures/fig_s5.pdf and
results/study5/report.md.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import ci, holm, pp, pval  # noqa: E402
from analyze_study4 import NI_MARGIN, REGIMES, noninf, paired, regime, sup  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core.study5 import TUNED  # noqa: E402

P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study5"
MAC, REPORT = {}, []
T, A = "+periodic:60", "alns_fixed@40~"
LAMS = {0.5: "Half", 1.0: "One", 2.0: "Two"}
M = {"CAHalf": A + "z=auto4;lam=0.5" + T, "CAOne": A + "z=auto4;lam=1" + T, "CATwo": A + "z=auto4;lam=2" + T,
     "CCfb": A + "z=auto4;fb=nominal" + T, "MP": A + "mp=auto;fb=nominal" + T, "MPnf": A + "mp=auto" + T,
     "Buf": A + "buf=60" + T, "Forty": "alns_fixed@40" + T, "Conv": "alns_fixed@40+event"}
LAB = {"CA": "Cost-aware fallback (proposed)", "CCfb": "Nominal fallback (study 4)",
       "Prop": "Proportional buffer, tuned per $\\lambda$", "CCnf": "No fallback, $z$ tuned per $\\lambda$",
       "MP": "Moment propagation, fallback", "MPnf": "Moment propagation, no fallback", "Buf": "Constant 60 s buffer",
       "Forty": "Nominal model", "Conv": "Conventional (event-only)"}


def put(k, v):
    MAC["F" + k] = v


def ca(lam):
    return M["CA" + LAMS[lam]]


def tuned(df, fam, lam):
    """Rows of the member of family fam selected on dev for late cost lam, per disturbance level."""
    parts = [df[(df.exec_level == lvl) & (df.method == A + o + T)] for lvl, o in TUNED[lam][fam].items()]
    if any(p.empty for p in parts):
        return df.iloc[:0]
    return pd.concat(parts).assign(method=f"{fam}@{lam:g}")


def sel_tex(o):
    """'prop=0.3;fb=none' -> '$c = 0.3$, no fallback'; 'z=-0.5' -> '$z = -0.5$'."""
    k, _, rest = o.partition("=")
    v, _, fb = rest.partition(";fb=")
    t = f"${'c' if k == 'prop' else k} = {v}$"
    return t + {"": "", "nominal": ", nominal fallback", "none": ", no fallback"}[fb]


def scored(df, lam):
    return df.assign(u=df.utility_rate - lam * df.late_served / df.n_tasks)


def analyse(df, dev=False):
    put("NRuns", f"{len(df):,}".replace(",", "\\,"))
    df = pd.concat([df] + [tuned(df, f, lam) for lam in LAMS for f in ("Prop", "CCnf")], ignore_index=True)
    have = set(df.method)
    put("NMissions", str(df.scenario.nunique()))
    put("NIMargin", f"{NI_MARGIN * 100:.1f}")
    for lam, key in LAMS.items():
        put(f"Theta{key}", f"{lam / (1 + lam):.2f}")
    for lam in LAMS:
        for f in ("Prop", "CCnf"):
            for lvl, o in TUNED[lam][f].items():
                put(f"Sel{f}{LAMS[lam]}{lvl.capitalize()}", sel_tex(o))

    # primary family (pre-registered), lam = 1, Holm over four tests
    x = scored(df, 1.0)
    a = ca(1.0)
    fam = [("CCfb", "sup", M["CCfb"]), ("Prop", "ni", "Prop@1"), ("CCnf", "ni", "CCnf@1"), ("Forty", "sup", M["Forty"])]
    fam = [f for f in fam if f[2] in have and a in have]
    res = [(n, kind) + (sup if kind == "sup" else noninf)(paired(x, a, b, "u")) for n, kind, b in fam]
    adj = holm(np.array([r[5] for r in res])) if res else []
    REPORT.extend(["## Primary family, lambda = 1, Holm (H16 nominal fallback, H17 tuned proportional buffer NI, "
                   "H18 tuned no-fallback NI, H19 nominal model)", "",
                   "| comparison | test | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|---|"])
    nsig = 0
    for (name, kind, m, lo, hi, p), pa, (_, _, b) in zip(res, adj, fam):
        put(f"D{name}One", ci(m, lo, hi))
        put(f"P{name}One", pval(pa))
        put(f"Abs{name}One", f"{abs(m) * 100:.2f}")
        ok = pa < 0.05 and (kind == "ni" or m > 0)
        nsig += ok
        put(f"Holds{name}One", "yes" if ok else "no")
        REPORT.append(f"| CA(1) - {name} | {kind} | {ci(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
        if kind == "ni":
            m2, lo2, hi2, p2 = sup(paired(x, a, b, "u"))
            put(f"PSup{name}One", pval(p2))
            put(f"SupHolds{name}One", "yes" if (ok and p2 < 0.05 and m2 > 0) else "no")
            REPORT.append(f"| CA(1) - {name} | sup (fixed sequence) | {ci(m2, lo2, hi2)} | {p2:.4f} | "
                          f"{'tested' if ok else 'not tested'} |")
    put("NSig", str(nsig))

    # secondary: every late cost, every competitor (descriptive)
    REPORT.extend(["", "## Secondary: CA(lambda) minus competitor, scored at the same lambda", "",
                   "| competitor | " + " | ".join(f"lambda {l:g}" for l in LAMS) + " |", "|---" * (len(LAMS) + 1) + "|"])
    curves = {}
    for name in ("CCfb", "Prop", "CCnf", "MP", "MPnf", "Buf", "Forty", "Conv"):
        cells = []
        for lam, key in LAMS.items():
            b = f"{name}@{lam:g}" if name in ("Prop", "CCnf") else M[name]
            if b not in have or ca(lam) not in have:
                cells.append("--")
                continue
            m, lo, hi, p = sup(paired(scored(df, lam), ca(lam), b, "u"))
            put(f"D{name}{key}", ci(m, lo, hi))
            put(f"Abs{name}{key}", f"{abs(m) * 100:.2f}")
            put(f"P{name}{key}", pval(p))
            curves.setdefault(name, []).append((lam, m, lo, hi))
            cells.append(ci(m, lo, hi))
        REPORT.append(f"| {name} | " + " | ".join(cells) + " |")

    # robustness: competitors tuned for lam = 1 used at another late cost; CA(1) used at another late cost
    REPORT.extend(["", "## Robustness to the late cost assumed when tuning", ""])
    for lam in (0.5, 2.0):
        key, s = LAMS[lam], scored(df, lam)
        for name, a2, b2 in [("PropFix", ca(lam), "Prop@1"), ("CCnfFix", ca(lam), "CCnf@1"),
                             ("CAFix", ca(lam), ca(1.0))]:
            if a2 in have and b2 in have:
                m, lo, hi, p = sup(paired(s, a2, b2, "u"))
                put(f"D{name}{key}", ci(m, lo, hi))
                put(f"Abs{name}{key}", f"{abs(m) * 100:.2f}")
                REPORT.append(f"lambda {lam:g}: {a2} - {b2}: {ci(m, lo, hi)} p {p:.4f}")

    # per disturbance level and regime at lam = 1
    REPORT.extend(["", "## lambda = 1 per regime", "", "| regime | CCfb | Prop | CCnf | Forty |", "|---|---|---|---|---|"])
    for lvl in ("mid", "high"):
        sub = x[x.exec_level == lvl]
        for name, b in [("CCfb", M["CCfb"]), ("Prop", "Prop@1"), ("CCnf", "CCnf@1"), ("Forty", M["Forty"])]:
            if b in have and a in have:
                m, lo, hi, _ = sup(paired(sub, a, b, "u"))
                put(f"D{name}One{lvl.capitalize()}", ci(m, lo, hi))
    for xl, wf, tag in REGIMES:
        sub = regime(x, xl, wf)
        cells = []
        for name, b in [("CCfb", M["CCfb"]), ("Prop", "Prop@1"), ("CCnf", "CCnf@1"), ("Forty", M["Forty"])]:
            if b in have and a in have and not sub.empty:
                m, lo, hi, _ = sup(paired(sub, a, b, "u"))
                put(f"D{name}One{tag}", ci(m, lo, hi))
                cells.append(ci(m, lo, hi))
        REPORT.append(f"| {xl} w{wf:g} | " + " | ".join(cells) + " |")

    # means per method and late cost; late arrivals and fallback activity
    REPORT.extend(["", "## Mean score per method (%), late services per mission", "",
                   "| method | lambda 0 | 0.5 | 1 | 2 | late |", "|---|---|---|---|---|---|"])
    g = df.groupby("method")
    for k in sorted(have):
        s = df[df.method == k]
        r = [pp((s.utility_rate - lam * s.late_served / s.n_tasks).mean()) for lam in (0.0, 0.5, 1.0, 2.0)]
        REPORT.append(f"| {k} | " + " | ".join(r) + f" | {s.late_served.mean():.2f} |")
    for k, spec in M.items():
        if spec in have:
            s = df[df.method == spec]
            put(f"Late{k}", f"{s.late_served.mean():.2f}")
            put(f"U{k}", pp(s.utility_rate.mean()))
            for lam, key in LAMS.items():
                put(f"U{k}{key}", pp((s.utility_rate - lam * s.late_served / s.n_tasks).mean()))
            put(f"Ms{k}", f"{s.plan_ms_mean.mean():.1f}")
    for lam, key in LAMS.items():
        for f in ("Prop", "CCnf"):
            s = df[df.method == f"{f}@{lam:g}"]
            if len(s):
                put(f"U{f}{key}", pp((s.utility_rate - lam * s.late_served / s.n_tasks).mean()))
                put(f"Late{f}{key}", f"{s.late_served.mean():.2f}")
    if M["CAOne"] in have and M["CCfb"] in have:
        lc, lf = g.late_served.mean()[M["CAOne"]], g.late_served.mean()[M["CCfb"]]
        put("LateRedCCfb", f"{(1 - lc / lf) * 100:.0f}")
        uc, uf = g.utility_rate.mean()[M["CAOne"]], g.utility_rate.mean()[M["CCfb"]]
        put("UCostCCfb", f"{(uf - uc) * 100:.2f}")
    if dev:
        return
    table(df, have)
    figure(curves)


def table(df, have):
    def cell(spec, lam):
        s = df[df.method == spec]
        return pp((s.utility_rate - lam * s.late_served / s.n_tasks).mean()) if len(s) else "--"

    lines = ["\\begin{table}[t]",
             "\\caption{Study~5, tier B held-out results: mean score $u_\\lambda$ (\\%) for a late arrival that costs "
             "$\\lambda$ mean task rewards ($\\lambda = 0$ is the utility of studies 2--4), and tasks served late per "
             "mission at $\\lambda = 1$. The cost-aware fallback and the tuned competitors use the late cost of the "
             f"column. {df.scenario.nunique()} missions, 12 configurations each.}}\\label{{tab:s5}}",
             "\\centering\\small", "\\begin{tabular}{lrrrrr}", "\\toprule",
             "Method & $\\lambda = 0$ & $0.5$ & $1$ & $2$ & Late \\\\", "\\midrule"]
    rows = [("CA", {0.0: M["CCfb"], **{l: ca(l) for l in LAMS}}, ca(1.0)),
            ("CCfb", {l: M["CCfb"] for l in (0.0, *LAMS)}, M["CCfb"]),
            ("Prop", {l: f"Prop@{l:g}" for l in LAMS}, "Prop@1"),
            ("CCnf", {l: f"CCnf@{l:g}" for l in LAMS}, "CCnf@1")]
    rows += [(k, {l: M[k] for l in (0.0, *LAMS)}, M[k]) for k in ("MP", "MPnf", "Buf", "Forty", "Conv")]
    for k, specs, late in rows:
        if late not in have:
            continue
        cells = [cell(specs[l], l) if l in specs else "--" for l in (0.0, *LAMS)]
        lines.append(f"{LAB[k]} & " + " & ".join(cells) + f" & {df[df.method == late].late_served.mean():.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s5.tex").write_text("\n".join(lines) + "\n")


def figure(curves):
    style = {"CCfb": ("#C62828", "o", "vs. nominal fallback"),
             "Prop": ("#8C6D1F", "s", "vs. proportional buffer, tuned per $\\lambda$"),
             "CCnf": ("#178A5E", "D", "vs. no fallback, $z$ tuned per $\\lambda$"),
             "MP": ("#6A4BB5", "^", "vs. moment propagation with fallback")}
    fig, ax = plt.subplots(figsize=(3.45, 2.7))
    off = {k: (i - 1.5) * 0.035 for i, k in enumerate(style)}
    for k, (col, mk, lab) in style.items():
        if k not in curves:
            continue
        cv = np.array(curves[k])
        x = np.log2(cv[:, 0]) + off[k]
        ax.errorbar(x, cv[:, 1] * 100, yerr=[(cv[:, 1] - cv[:, 2]) * 100, (cv[:, 3] - cv[:, 1]) * 100], fmt=mk + "-",
                    ms=4, lw=1.2, capsize=2, color=col, label=lab)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(np.log2(list(LAMS)), [f"{l:g}" for l in LAMS])
    ax.set_xlabel(r"cost of a late arrival $\lambda$ (mean task rewards)")
    ax.set_ylabel("cost-aware fallback minus method (pp)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=6.6, loc="upper left")
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s5.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", nargs="+", default=[str(TB / "s5_heldout_B.csv")])
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    df = pd.concat([pd.read_csv(f) for f in a.csv], ignore_index=True)
    analyse(df, a.dev)
    print("\n".join(REPORT))
    if a.dev:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("# Study 5, tier B held-out\n\n" + "\n".join(REPORT) + "\n")
    lines = ["% generated by experiments/analyze_study5.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s5.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                         "font.family": "serif", "mathtext.fontset": "stix",
                         "font.serif": ["STIXGeneral", "DejaVu Serif"]})
    main()
