"""Study 3 analysis (docs/10_PROTOCOL_V3.md): chance-constrained planning with a nominal fallback.

    python experiments/analyze_study3.py                          # held-out (results/tier_b/s3_heldout_B.csv)
    python experiments/analyze_study3.py --csv results/tier_b/dev3_fallback.csv --dev   # dev check, no outputs

Writes paper_journal/tables/numbers_s3.tex (macros \\val{L...}), tables/tab_s3.tex, figures/fig_s3.pdf and
results/study3/report.md. Statistics as in study 2: per mission the paired difference is averaged over the configurations
of the cell, then a paired bootstrap over missions (10 000 resamples, 95% percentile CI, two-sided p), Holm on the
primary family.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

import analyze_study2 as a2
from analyze_study2 import boot, ci, holm, pp, pval, spp

ROOT = Path(__file__).resolve().parents[1]
P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study3"
CFG = ["exec_level", "latency_level", "kappa", "window"]
MAC, REPORT = {}, []
REGIMES = [("mid", 1.0, "MidWOne", "mid, windows $\\times 1$"), ("mid", 0.5, "MidWHalf", "mid, windows $\\times 0.5$"),
           ("high", 1.0, "HighWOne", "high, windows $\\times 1$"), ("high", 0.5, "HighWHalf", "high, windows $\\times 0.5$")]


def put(k, v):
    MAC["L" + k] = v


def methods(fb_spec):
    return {"FB": (fb_spec, "Proposed with fallback"), "Prop": ("proposed+periodic:60", "Proposed (study 2)"),
            "Buf": ("alns_fixed@40~buf=60+periodic:60", "Constant 60 s buffer"),
            "Forty": ("alns_fixed@40+periodic:60", "ALNS, fixed 40 ms"),
            "Conv": ("alns_fixed@40+event", "Conventional (40 ms, event-only)")}


def paired(df, a, b, metric="utility_rate", by=CFG):
    w = df[df.method.isin([a, b])].pivot_table(index=["scenario"] + by, columns="method", values=metric).dropna()
    return (w[a] - w[b]).groupby(level="scenario").mean()


def regime(df, xl, wf):
    return df[(df.exec_level == xl) & (df.window == wf)]


def analyse(df, M, dev=False):
    present = {k: v for k, v in M.items() if v[0] in set(df.method)}
    fb = M["FB"][0]
    put("NRuns", f"{len(df):,}".replace(",", "\\,"))
    put("NMissions", str(df.scenario.nunique()))
    put("NConfigs", str(df.groupby(CFG).ngroups))
    g = df.groupby("method").agg(u=("utility_rate", "mean"), late=("late_served", "mean"), lost=("dropped_by_delay", "mean"),
                                 skip=("dropped_in_exec", "mean"), served=("served", "mean"), ms=("plan_ms_mean", "mean"))
    for k, (spec, _) in present.items():
        put(f"U{k}", pp(g.loc[spec, "u"]))
        put(f"Late{k}", f"{g.loc[spec, 'late']:.2f}")
        put(f"Ms{k}", f"{g.loc[spec, 'ms']:.1f}")
    # primary family (pre-registered): FB vs Prop pooled, FB vs Buf in high/w0.5, FB vs Forty pooled, FB vs Buf pooled
    fam = [("PropAll", df, "Prop"), ("BufHighWHalf", regime(df, "high", 0.5), "Buf"), ("FortyAll", df, "Forty"),
           ("BufAll", df, "Buf")]
    tests = [(name, k) + boot(paired(sub, fb, M[k][0], by=CFG)) for name, sub, k in fam if k in present]
    adj = holm(np.array([t[5] for t in tests]))
    REPORT.extend(["## Primary family (fallback minus method), Holm", "", "| comparison | diff pp [95% CI] | p | p Holm |",
                   "|---|---|---|---|"])
    for (name, k, m, lo, hi, p), pa in zip(tests, adj):
        put(f"D{name}", ci(m, lo, hi))
        put(f"P{name}", pval(pa))
        put(f"Dabs{name}", pp(abs(m)))
        REPORT.append(f"| {name} | {ci(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
    put("NSig", str(sum(1 for a, t in zip(adj, tests) if a < 0.05 and t[2] > 0)))
    REPORT.extend(["", "## Secondary: per regime (fallback minus method; proposed minus buffer = replication)", "",
                   "| regime | " + " | ".join(f"FB-{k}" for k in present if k != "FB") + " | Prop-Buf |",
                   "|---|" + "---|" * len(present)])
    for xl, wf, tag, _ in REGIMES:
        sub = regime(df, xl, wf)
        cells = []
        for k in [k for k in present if k != "FB"]:
            m, lo, hi, _ = boot(paired(sub, fb, M[k][0]))
            put(f"D{k}{tag}", ci(m, lo, hi))
            cells.append(ci(m, lo, hi))
        if "Buf" in present:
            m, lo, hi, _ = boot(paired(sub, M["Prop"][0], M["Buf"][0]))
            put(f"DPropBuf{tag}", ci(m, lo, hi))
            cells.append(ci(m, lo, hi))
        for k in present:
            s = sub[sub.method == M[k][0]]
            put(f"U{k}{tag}", pp(s.utility_rate.mean()))
            put(f"Served{k}{tag}", f"{s.served.mean():.1f}")
            put(f"Late{k}{tag}", f"{s.late_served.mean():.1f}")
        REPORT.append(f"| {xl} w{wf} | " + " | ".join(cells) + " |")
    if "Conv" in present:
        m, lo, hi, p = boot(paired(df, fb, M["Conv"][0]))
        put("DConvAll", ci(m, lo, hi))
        put("URelConv", f"{(g.loc[fb, 'u'] / g.loc[M['Conv'][0], 'u'] - 1) * 100:.1f}")
        REPORT.append(f"\nFB minus conventional, pooled: {ci(m, lo, hi)} (p {p:.4f})")
    m, lo, hi, _ = boot(paired(df, fb, M["Prop"][0], "plan_ms_mean"))
    put("DMsProp", f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]".replace("-", "$-$"))
    # replication of the study-2 primary result on the new seeds (descriptive)
    for k in ["Buf", "Forty"]:
        if k in present:
            m, lo, hi, _ = boot(paired(df, M["Prop"][0], M[k][0]))
            put(f"DPropRep{k}", ci(m, lo, hi))
    REPORT.extend(["", "| method | U | late | lost | skipped | ms |", "|---|---|---|---|---|---|"])
    for k, (spec, lab) in present.items():
        r = g.loc[spec]
        REPORT.append(f"| {lab} | {pp(r.u)} | {r.late:.2f} | {r.lost:.2f} | {r.skip:.2f} | {r.ms:.1f} |")
    if dev:
        return
    table(df, g, present)
    figure(df, present)


def table(df, g, M):
    lines = ["\\begin{table}[t]",
             "\\caption{Study~3, tier B held-out results: utility (\\%) per method overall and per regime (disturbance "
             "level and time-window factor, mean over $\\kappa_B$), tasks served late per mission and computation per "
             f"call. {df.scenario.nunique()} missions, {df.groupby(CFG).ngroups} configurations.}}\\label{{tab:s3}}",
             "\\centering\\small", "\\begin{tabular}{lrrrrrrr}", "\\toprule",
             "& & \\multicolumn{2}{c}{Mid} & \\multicolumn{2}{c}{High} & & \\\\",
             "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}",
             "Method & All & $\\times 1$ & $\\times 0.5$ & $\\times 1$ & $\\times 0.5$ & Late & ms/call \\\\", "\\midrule"]
    for k, (spec, lab) in M.items():
        cells = [pp(g.loc[spec, "u"])]
        for xl, wf, _, _ in REGIMES:
            sub = regime(df, xl, wf)
            cells.append(pp(sub[sub.method == spec].utility_rate.mean()))
        name = "\\textbf{" + lab + "}" if k == "FB" else lab
        lines.append(f"{name} & " + " & ".join(cells) + f" & {g.loc[spec, 'late']:.2f} & {g.loc[spec, 'ms']:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s3.tex").write_text("\n".join(lines) + "\n")


def figure(df, M):
    keys = [k for k in ["Prop", "Buf", "Forty", "Conv"] if k in M]
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    width = 0.8 / len(keys)
    for j, k in enumerate(keys):
        for i, (xl, wf, _, _) in enumerate(REGIMES):
            m, lo, hi, _ = boot(paired(regime(df, xl, wf), M["FB"][0], M[k][0]), n=4000)
            x = i + (j - (len(keys) - 1) / 2) * width
            ax.errorbar(x, m * 100, yerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt="o", ms=4.5, capsize=2.5,
                        color=a2.COL[k], label=("vs. " + M[k][1][0].lower() + M[k][1][1:]) if i == 0 else None)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(REGIMES)), [f"{xl} disturbances\nwindows $\\times${wf:g}" for xl, wf, _, _ in REGIMES])
    ax.set_ylabel("fallback minus method (pp)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(keys), handletextpad=0.3,
              columnspacing=1.0)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s3.pdf")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(TB / "s3_heldout_B.csv"))
    ap.add_argument("--config", default=str(ROOT / "experiments" / "configs" / "S3_B.yaml"))
    ap.add_argument("--fb", default=None, help="fallback spec (default: first method of the config)")
    ap.add_argument("--dev", action="store_true", help="print the report only")
    args = ap.parse_args()
    fb = args.fb or yaml.safe_load(Path(args.config).read_text())["grid"]["methods"][0]
    df = pd.read_csv(args.csv)
    REPORT.extend([f"# Study 3 ({'dev' if args.dev else 'held-out'}): {args.csv}", f"fallback spec: {fb}", ""])
    analyse(df, methods(fb), dev=args.dev)
    print("\n".join(REPORT))
    if args.dev:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.md").write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    out = ["% generated by experiments/analyze_study3.py -- do not edit"]
    out += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s3.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(MAC)} macros")


if __name__ == "__main__":
    main()
