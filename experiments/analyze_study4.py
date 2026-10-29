"""Study 4 analysis (docs/12_PROTOCOL_V4.md): planning models on the same search, fallback for moment propagation,
online calibration, coverage of the chance constraint.

    python experiments/analyze_study4.py                                   # held-out (results/tier_b/s4_heldout_B.csv)
    python experiments/analyze_study4.py --csv results/tier_b/dev4_check.csv --dev   # dev check, no outputs

Writes paper_journal/tables/numbers_s4.tex (macros \\val{Q...}), tables/tab_s4.tex, figures/fig_s4.pdf,
figures/fig_coverage.pdf and results/study4/report.md. Statistics as in studies 2 and 3: per mission the paired
difference is averaged over the configurations of the cell, then a paired bootstrap over missions (10 000 resamples,
95% percentile CI, two-sided p). Non-inferiority: one-sided p = share of bootstrap means at or below -margin.
Holm over the primary family; the superiority test of H10 follows its non-inferiority test in a fixed sequence.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analyze_study2 as a2
from analyze_study2 import ci, holm, pp, pval

ROOT = Path(__file__).resolve().parents[1]
P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study4"
CFG = ["exec_level", "latency_level", "kappa", "window"]
MAC, REPORT = {}, []
NI_MARGIN = 0.005
REGIMES = [("mid", 1.0, "MidWOne"), ("mid", 0.5, "MidWHalf"), ("high", 1.0, "HighWOne"), ("high", 0.5, "HighWHalf")]
T = "+periodic:60"
M = {"CC": ("alns_fixed@40~z=auto4;fb=nominal" + T, "Proposed planning model"),
     "PropBuf": ("alns_fixed@40~prop=auto;fb=nominal" + T, "Proportional buffer $c\\,h$"),
     "MP": ("alns_fixed@40~mp=auto;fb=nominal" + T, "Moment propagation"),
     "MPnf": ("alns_fixed@40~mp=auto" + T, "Moment propagation, no fallback"),
     "Onl": ("alns_fixed@40~online=auto;fb=nominal" + T, "Proposed, online calibration"),
     "Full": ("proposed~z=auto4;fb=nominal" + T, "Proposed, learned stopping rule"),
     "Buf": ("alns_fixed@40~buf=60" + T, "Constant 60 s buffer"),
     "Forty": ("alns_fixed@40" + T, "Nominal model"),
     "Conv": ("alns_fixed@40+event", "Conventional (event-only)"),
     "RepCC": ("regret_repair~z=auto4;fb=nominal" + T, "Repair only, proposed model"),
     "Rep": ("regret_repair" + T, "Repair only, nominal model")}
COL = {"PropBuf": "#8C6D1F", "MP": "#6A4BB5", "Buf": "#178A5E", "Forty": "#1F6FC5", "Conv": "#6B6B6B"}


def put(k, v):
    MAC["Q" + k] = v


def paired(df, a, b, metric="utility_rate", by=CFG):
    w = df[df.method.isin([a, b])].pivot_table(index=["scenario"] + by, columns="method", values=metric).dropna()
    return (w[a] - w[b]).groupby(level="scenario").mean()


def regime(df, xl, wf):
    return df[(df.exec_level == xl) & (df.window == wf)]


def boot_all(d, n=10_000, seed=0):
    d = np.asarray(d, float)
    idx = np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))
    return d.mean(), d[idx].mean(axis=1)


def sup(d):
    m, b = boot_all(d)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return float(m), float(lo), float(hi), float(min(2 * min(np.mean(b <= 0), np.mean(b >= 0)), 1.0))


def noninf(d, margin=NI_MARGIN):
    m, b = boot_all(d)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return float(m), float(lo), float(hi), float(np.mean(b <= -margin))


def analyse(df, dev=False):
    present = {k: v for k, v in M.items() if v[0] in set(df.method)}
    put("NRuns", f"{len(df):,}".replace(",", "\\,"))
    put("NMissions", str(df.scenario.nunique()))
    put("NConfigs", str(df.groupby(CFG).ngroups))
    put("NIMargin", f"{NI_MARGIN * 100:.1f}")
    g = df.groupby("method").agg(u=("utility_rate", "mean"), late=("late_served", "mean"),
                                 lost=("dropped_by_delay", "mean"), skip=("dropped_in_exec", "mean"),
                                 served=("served", "mean"), ms=("plan_ms_mean", "mean"), itms=("iters_per_ms", "mean"))
    for k, (spec, _) in present.items():
        r = g.loc[spec]
        put(f"U{k}", pp(r.u))
        put(f"Late{k}", f"{r.late:.2f}")
        put(f"Skip{k}", f"{r.skip:.2f}")
        put(f"Lost{k}", f"{r.lost:.2f}")
        put(f"Ms{k}", f"{r.ms:.1f}")
        put(f"ItMs{k}", f"{r.itms:.2f}")
    cc = M["CC"][0]
    # primary family (pre-registered), Holm over five tests
    fam = [("PropBufAll", "sup", cc, "PropBuf"), ("MPAll", "ni", cc, "MP"), ("FbMPAll", "sup", M["MP"][0], "MPnf"),
           ("BufAll", "sup", cc, "Buf"), ("FortyAll", "sup", cc, "Forty")]
    fam = [f for f in fam if f[3] in present and f[2] in set(df.method)]
    res = [(n, kind, k) + (sup if kind == "sup" else noninf)(paired(df, a, M[k][0])) for n, kind, a, k in fam]
    adj = holm(np.array([r[6] for r in res]))
    REPORT.extend(["## Primary family, Holm (H9 PropBuf, H10 MP non-inferiority, H11 fallback for MP, H12 Buf, "
                   "H13 Forty)", "", "| comparison | test | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|---|"])
    for (name, kind, k, m, lo, hi, p), pa in zip(res, adj):
        put(f"D{name}", ci(m, lo, hi))
        put(f"P{name}", pval(pa))
        REPORT.append(f"| {name} | {kind} | {ci(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
        if name == "MPAll":
            ni_ok = pa < 0.05
            put("NIMPHolds", "yes" if ni_ok else "no")
            m2, lo2, hi2, p2 = sup(paired(df, cc, M["MP"][0]))
            put("PSupMPAll", pval(p2))
            put("SupMPHolds", "yes" if (ni_ok and p2 < 0.05 and m2 > 0) else "no")
            REPORT.append(f"| MPAll | sup (fixed sequence) | {ci(m2, lo2, hi2)} | {p2:.4f} | {'tested' if ni_ok else 'not tested'} |")
    put("NSig", str(sum(1 for r, a in zip(res, adj) if a < 0.05 and (r[1] == "ni" or r[3] > 0))))
    # H10b: search throughput, proposed model minus moment propagation (iterations per planning millisecond)
    if "MP" in present:
        m, lo, hi, p = sup(paired(df, cc, M["MP"][0], "iters_per_ms"))
        put("DItMsMP", f"{m:+.2f} [{lo:+.2f}, {hi:+.2f}]".replace("-", "$-$"))
        put("PItMsMP", pval(p))
        put("RelItMsMP", f"{(g.loc[cc, 'itms'] / g.loc[M['MP'][0], 'itms'] - 1) * 100:.0f}")
        REPORT.append(f"\nH10b iterations/ms, CC minus MP: {m:+.3f} [{lo:+.3f}, {hi:+.3f}] p {p:.4f}")
    # secondary (pre-registered as descriptive)
    REPORT.extend(["", "## Secondary", ""])
    for name, a, b, kind in [("OnlCC", "Onl", "CC", "ni"), ("FullCC", "Full", "CC", "sup"), ("RepCCRep", "RepCC", "Rep", "sup"),
                             ("CCConv", "CC", "Conv", "sup"), ("FullConv", "Full", "Conv", "sup"),
                             ("FullBuf", "Full", "Buf", "sup"), ("FullForty", "Full", "Forty", "sup")]:
        if a in present and b in present:
            m, lo, hi, p = (sup if kind == "sup" else noninf)(paired(df, M[a][0], M[b][0]))
            put(f"D{name}", ci(m, lo, hi))
            put(f"P{name}", pval(p))
            REPORT.append(f"{name} ({kind}): {ci(m, lo, hi)} p {p:.4f}")
    for a, b in [("CC", "Conv"), ("CC", "Forty"), ("CC", "Buf"), ("Full", "Conv"), ("RepCC", "Rep")]:
        if a in present and b in present:
            put(f"URel{a}{b}", f"{(g.loc[M[a][0], 'u'] / g.loc[M[b][0], 'u'] - 1) * 100:.1f}")
    if "Forty" in present:
        put("LateRedForty", f"{(1 - g.loc[cc, 'late'] / g.loc[M['Forty'][0], 'late']) * 100:.0f}")
    REPORT.extend(["", "| regime | " + " | ".join(f"CC-{k}" for k in COL if k in present) + " | MP-MPnf |",
                   "|---|" + "---|" * (len([k for k in COL if k in present]) + 1)])
    for xl, wf, tag in REGIMES:
        sub = regime(df, xl, wf)
        if sub.empty:
            continue
        cells = []
        for k in [k for k in COL if k in present]:
            m, lo, hi, _ = sup(paired(sub, cc, M[k][0]))
            put(f"D{k}{tag}", ci(m, lo, hi))
            cells.append(ci(m, lo, hi))
        if "MPnf" in present:
            m, lo, hi, _ = sup(paired(sub, M["MP"][0], M["MPnf"][0]))
            put(f"DFbMP{tag}", ci(m, lo, hi))
            cells.append(ci(m, lo, hi))
        for k in present:
            put(f"U{k}{tag}", pp(sub[sub.method == M[k][0]].utility_rate.mean()))
        REPORT.append(f"| {xl} w{wf:g} | " + " | ".join(cells) + " |")
    REPORT.extend(["", "| method | U | late | lost | skipped | ms | it/ms |", "|---|---|---|---|---|---|---|"])
    for k, (spec, lab) in present.items():
        r = g.loc[spec]
        REPORT.append(f"| {lab} | {pp(r.u)} | {r.late:.2f} | {r.lost:.2f} | {r.skip:.2f} | {r.ms:.1f} | {r.itms:.2f} |")
    cov = coverage(df, present)
    if dev:
        return
    table(df, g, present)
    figure(df, present)
    figure_coverage(cov)


def coverage(df, present):
    """Reliability of the error model in closed loop: executed tasks binned by predicted on-time probability."""
    out = {}
    for k in ["CC", "Forty"]:
        if k not in present:
            continue
        for xl in ["mid", "high"]:
            s = df[(df.method == M[k][0]) & (df.exec_level == xl)]
            n = np.array([s[f"cov_n{i}"].sum() for i in range(10)], float)
            kk = np.array([s[f"cov_k{i}"].sum() for i in range(10)], float)
            pm = np.array([s[f"cov_p{i}"].sum() for i in range(10)], float)
            with np.errstate(invalid="ignore", divide="ignore"):
                out[(k, xl)] = (pm / n, kk / n, n)
            tot = n.sum()
            put(f"CovPred{k}{xl.capitalize()}", f"{100 * pm.sum() / tot:.1f}")
            put(f"CovObs{k}{xl.capitalize()}", f"{100 * kk.sum() / tot:.1f}")
            REPORT.append(f"coverage {k} {xl}: predicted {pm.sum() / tot:.3f} observed {kk.sum() / tot:.3f} "
                          f"(n={int(tot)})")
            hi = n[5:].sum()
            put(f"CovObsAbove{k}{xl.capitalize()}", f"{100 * kk[5:].sum() / hi:.1f}" if hi else "--")
            put(f"CovPredAbove{k}{xl.capitalize()}", f"{100 * pm[5:].sum() / hi:.1f}" if hi else "--")
    return out


def table(df, g, present):
    lines = ["\\begin{table}[t]",
             "\\caption{Study~4, tier B held-out results: utility (\\%) per planning model overall and per regime "
             "(disturbance level and time-window factor, mean over $\\kappa_B$), tasks served late per mission and "
             "search iterations per planning millisecond. All models use the same search with a fixed budget of "
             f"40\\,ms and periodic replanning. {df.scenario.nunique()} missions, {df.groupby(CFG).ngroups} "
             "configurations.}\\label{tab:s4}",
             "\\centering\\small", "\\begin{tabular}{lrrrrrrr}", "\\toprule",
             "& & \\multicolumn{2}{c}{Mid} & \\multicolumn{2}{c}{High} & & \\\\",
             "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}",
             "Planning model & All & $\\times 1$ & $\\times 0.5$ & $\\times 1$ & $\\times 0.5$ & Late & it/ms \\\\",
             "\\midrule"]
    for k in ["CC", "Onl", "MP", "MPnf", "PropBuf", "Buf", "Forty", "Conv"]:
        if k not in present:
            continue
        spec, lab = present[k]
        cells = [pp(g.loc[spec, "u"])]
        for xl, wf, _ in REGIMES:
            sub = regime(df, xl, wf)
            cells.append(pp(sub[sub.method == spec].utility_rate.mean()))
        lines.append(f"{lab} & " + " & ".join(cells) + f" & {g.loc[spec, 'late']:.2f} & {g.loc[spec, 'itms']:.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s4.tex").write_text("\n".join(lines) + "\n")


def figure(df, present):
    labels = {"PropBuf": "vs. proportional buffer", "MP": "vs. moment propagation", "Buf": "vs. constant 60 s buffer",
              "Forty": "vs. nominal model", "Conv": "vs. conventional planner"}
    keys = [k for k in labels if k in present]
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    width = 0.8 / len(keys)
    for j, k in enumerate(keys):
        for i, (xl, wf, _) in enumerate(REGIMES):
            m, lo, hi, _ = sup(paired(regime(df, xl, wf), M["CC"][0], M[k][0]))
            x = i + (j - (len(keys) - 1) / 2) * width
            ax.errorbar(x, m * 100, yerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt="o", ms=4.5, capsize=2.5,
                        color=COL[k], label=labels[k] if i == 0 else None)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(REGIMES)), [f"{xl} disturbances\nwindows $\\times${wf:g}" for xl, wf, _ in REGIMES])
    ax.set_ylabel("proposed minus method (pp)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, handletextpad=0.3,
              columnspacing=1.2, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s4.pdf")
    plt.close(fig)


def figure_coverage(cov):
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.7), sharey=True)
    for a, xl in zip(ax, ["mid", "high"]):
        a.plot([0, 1], [0, 1], color="black", lw=0.8, ls=":")
        for k, col, lab in [("CC", "#C62828", "proposed planning model"), ("Forty", "#1F6FC5", "nominal model")]:
            if (k, xl) not in cov:
                continue
            pr, ob, n = cov[(k, xl)]
            s = n >= 20
            a.plot(pr[s], ob[s], "o-", color=col, ms=4, lw=1.2, label=lab)
        a.set_title(f"{xl} disturbances", fontsize=9)
        a.set_xlabel("predicted probability of meeting the deadline")
        a.grid(alpha=0.3)
    ax[0].set_ylabel("observed share on time")
    ax[0].legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_coverage.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(TB / "s4_heldout_B.csv"))
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    analyse(df, a.dev)
    print("\n".join(REPORT))
    if a.dev:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("# Study 4, tier B held-out\n\n" + "\n".join(REPORT) + "\n")
    lines = ["% generated by experiments/analyze_study4.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s4.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
