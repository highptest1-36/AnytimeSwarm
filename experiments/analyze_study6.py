"""Study 6 analysis (docs/14_PROTOCOL_V6.md): CBBA as a published baseline, and the cost-aware fallback for moment
propagation.

    python experiments/analyze_study6.py                                  # held-out (results/tier_b/s6_heldout_B.csv)
    python experiments/analyze_study6.py --csv results/tier_b/dev6.csv results/tier_b/dev5_tune.csv --dev

Score u_lam = utility_rate - lam * late_served / n_tasks, as in study 5; the primary family uses lam = 1. Statistics as
in studies 2-5: per mission the paired difference is averaged over the configurations, then a paired bootstrap over
missions (10 000 resamples, 95% percentile CI, two-sided p); Holm over the primary family.

Writes paper_journal/tables/numbers_s6.tex (macros \\val{W...}), tables/tab_s6.tex, figures/fig_s6.pdf and
results/study6/report.md.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import holm, pp, pval  # noqa: E402
from analyze_study4 import REGIMES, paired, regime, sup  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study6"
MAC, REPORT = {}, []
T, A = "+periodic:60", "alns_fixed@40~"
LAMS = {0.0: "Zero", 0.5: "Half", 1.0: "One", 2.0: "Two"}
M = {"CA": A + "z=auto4;lam=1" + T, "CCfb": A + "z=auto4;fb=nominal" + T, "CBBA": "cbba" + T, "CBBAe": "cbba+event",
     "CBBACA": "cbba~z=auto4;lam=1" + T, "MPCA": A + "mp=auto;lam=1" + T, "MP": A + "mp=auto;fb=nominal" + T,
     "MPnf": A + "mp=auto" + T, "Forty": "alns_fixed@40" + T}
LAB = {"CA": "Proposed (ALNS, cost-aware fallback)", "CCfb": "Proposed, nominal fallback",
       "CBBACA": "CBBA on the proposed model", "CBBA": "CBBA, periodic", "CBBAe": "CBBA, event-triggered",
       "MPCA": "Moment propagation, cost-aware fallback", "MP": "Moment propagation, nominal fallback",
       "MPnf": "Moment propagation, no fallback", "Forty": "Nominal model (ALNS)"}
PRIMARY = [("CBBA", "CA", "CBBA"), ("CBBAModel", "CBBACA", "CBBA"), ("MPFb", "MPCA", "MP"), ("MPNoFb", "MPCA", "MPnf")]
SECONDARY = [("CBBAEvent", "CA", "CBBAe"), ("CBBAModelEvent", "CBBACA", "CBBAe"), ("CAMPCA", "CA", "MPCA"),
             ("CACBBACA", "CA", "CBBACA"), ("CACCfb", "CA", "CCfb"), ("CBBAForty", "CBBA", "Forty"),
             ("CAForty", "CA", "Forty")]


def put(k, v):
    MAC["W" + k] = v


def num(m, lo, hi, name):
    put(f"D{name}", f"{m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]".replace("-", "$-$"))
    put(f"Dabs{name}", f"{abs(m) * 100:.2f}")
    put(f"CI{name}", f"{lo * 100:.2f} to {hi * 100:.2f}".replace("-", "$-$"))


def scored(df, lam):
    return df.assign(u=df.utility_rate - lam * df.late_served / df.n_tasks)


def analyse(df, dev=False):
    have = set(df.method)
    put("NRuns", f"{len(df):,}".replace(",", "\\,"))
    put("NMissions", str(df.scenario.nunique()))
    # primary family (pre-registered), lam = 1, Holm over four tests
    x = scored(df, 1.0)
    fam = [(n, a, b) for n, a, b in PRIMARY if M[a] in have and M[b] in have]
    res = [(n,) + sup(paired(x, M[a], M[b], "u")) for n, a, b in fam]
    adj = holm(np.array([r[4] for r in res])) if res else []
    REPORT.extend(["## Primary family, lambda = 1, Holm (H20 proposed vs CBBA, H21 CBBA on the proposed model vs CBBA, "
                   "H22 cost-aware vs nominal fallback in moment propagation, H23 vs no fallback)", "",
                   "| comparison | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"])
    nsig = 0
    for (name, m, lo, hi, p), pa in zip(res, adj):
        num(m, lo, hi, f"{name}One")
        put(f"P{name}One", pval(pa))
        ok = pa < 0.05 and m > 0
        nsig += ok
        put(f"Holds{name}One", "yes" if ok else "no")
        REPORT.append(f"| {name} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] | {p:.4f} | {pa:.4f} |")
    put("NSig", str(nsig))
    # secondary (descriptive): every lam, every comparison
    REPORT.extend(["", "## Secondary (descriptive): A minus B at every late cost", "",
                   "| comparison | " + " | ".join(f"lambda {l:g}" for l in LAMS) + " |", "|---" * (len(LAMS) + 1) + "|"])
    curves = {}
    for name, a, b in PRIMARY + SECONDARY:
        if M[a] not in have or M[b] not in have:
            continue
        cells = []
        for lam, key in LAMS.items():
            m, lo, hi, p = sup(paired(scored(df, lam), M[a], M[b], "u"))
            if not (name in dict((n, 0) for n, _, _ in PRIMARY) and key == "One"):
                num(m, lo, hi, f"{name}{key}")
                put(f"P{name}{key}", pval(p))
            curves.setdefault(name, []).append((lam, m, lo, hi))
            cells.append(f"{m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]")
        REPORT.append(f"| {name} ({a} - {b}) | " + " | ".join(cells) + " |")
    # per disturbance level and regime, lam = 1 and lam = 0
    REPORT.extend(["", "## Per regime (lambda 1 | lambda 0)", ""])
    for name, a, b in PRIMARY[:2]:
        for lam, key in ((1.0, "One"), (0.0, "Zero")):
            s = scored(df, lam)
            for lvl in ("mid", "high"):
                m, lo, hi, _ = sup(paired(s[s.exec_level == lvl], M[a], M[b], "u"))
                num(m, lo, hi, f"{name}{key}{lvl.capitalize()}")
            for xl, wf, tag in REGIMES:
                m, lo, hi, _ = sup(paired(regime(s, xl, wf), M[a], M[b], "u"))
                num(m, lo, hi, f"{name}{key}{tag}")
                REPORT.append(f"{name} lambda {lam:g} {xl} w{wf:g}: {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]")
    # means, late services, planning time and rounds
    REPORT.extend(["", "## Means", "", "| method | U | u_0.5 | u_1 | u_2 | late | ms/call | iterations or rounds |",
                   "|---|---|---|---|---|---|---|---|"])
    for k, spec in M.items():
        if spec not in have:
            continue
        s = df[df.method == spec]
        us = [(s.utility_rate - lam * s.late_served / s.n_tasks).mean() for lam in LAMS]
        for (lam, key), u in zip(LAMS.items(), us):
            put(f"U{k}{key}", pp(u))
        put(f"Late{k}", f"{s.late_served.mean():.2f}")
        put(f"Ms{k}", f"{s.plan_ms_mean.mean():.1f}")
        put(f"Iters{k}", f"{s.iters_mean.mean():.1f}")
        REPORT.append(f"| {LAB[k]} | " + " | ".join(pp(u) for u in us) +
                      f" | {s.late_served.mean():.2f} | {s.plan_ms_mean.mean():.1f} | {s.iters_mean.mean():.1f} |")
    if M["CBBA"] in have and M["CA"] in have:
        put("URelCACBBA", f"{(df[df.method == M['CA']].utility_rate.mean() / df[df.method == M['CBBA']].utility_rate.mean() - 1) * 100:.1f}")
    if dev:
        return
    table(df, have)
    figure(curves)


def table(df, have):
    lines = ["\\begin{table}[t]",
             "\\caption{Study~6, tier B held-out results: mean score $u_\\lambda$ (\\%) for a late arrival that costs "
             "$\\lambda$ mean task rewards ($\\lambda=0$ is the utility), tasks served late per mission and planning "
             "time per call. Methods with the cost-aware fallback use $\\lambda=1$. "
             f"{df.scenario.nunique()} missions, 12 configurations each.}}\\label{{tab:s6}}",
             "\\centering\\small", "\\begin{tabular}{lrrrrrr}", "\\toprule",
             "Method & $\\lambda=0$ & $0.5$ & $1$ & $2$ & Late & ms \\\\", "\\midrule"]
    for k in ["CA", "CBBACA", "CBBA", "CBBAe", "MPCA", "MP", "MPnf", "Forty"]:
        if M[k] not in have:
            continue
        s = df[df.method == M[k]]
        cells = [pp((s.utility_rate - lam * s.late_served / s.n_tasks).mean()) for lam in LAMS]
        lines.append(f"{LAB[k]} & " + " & ".join(cells) +
                     f" & {s.late_served.mean():.2f} & {s.plan_ms_mean.mean():.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s6.tex").write_text("\n".join(lines) + "\n")


def figure(curves):
    style = {"CBBA": ("#6B6B6B", "o", "proposed vs. CBBA"),
             "CBBAModel": ("#1F6FC5", "s", "CBBA on the proposed model vs. CBBA"),
             "MPFb": ("#C62828", "D", "moment prop.: cost-aware vs. nominal fallback"),
             "MPNoFb": ("#6A4BB5", "^", "moment prop.: cost-aware vs. no fallback")}
    fig, ax = plt.subplots(figsize=(3.45, 2.7))
    xs = np.arange(len(LAMS))
    for i, (k, (col, mk, lab)) in enumerate(style.items()):
        if k not in curves:
            continue
        cv = np.array(curves[k])
        x = xs + (i - 1.5) * 0.06
        ax.errorbar(x, cv[:, 1] * 100, yerr=[(cv[:, 1] - cv[:, 2]) * 100, (cv[:, 3] - cv[:, 1]) * 100], fmt=mk + "-",
                    ms=4, lw=1.2, capsize=2, color=col, label=lab)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(xs, [f"{l:g}" for l in LAMS])
    ax.set_xlabel(r"cost of a late arrival $\lambda$ (mean task rewards)")
    ax.set_ylabel("difference in score (pp)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=6.4, loc="upper left")
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s6.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", nargs="+", default=[str(TB / "s6_heldout_B.csv")])
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    df = pd.concat([pd.read_csv(f) for f in a.csv], ignore_index=True)
    df = df[df.method.isin(M.values())]
    analyse(df, a.dev)
    print("\n".join(REPORT))
    if a.dev:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("# Study 6, tier B held-out\n\n" + "\n".join(REPORT) + "\n")
    lines = ["% generated by experiments/analyze_study6.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s6.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                         "font.family": "serif", "mathtext.fontset": "stix",
                         "font.serif": ["STIXGeneral", "DejaVu Serif"]})
    main()
