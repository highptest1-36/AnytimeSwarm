#!/usr/bin/env python3
"""Pre-registered analysis of study 2 (docs/08_PROTOCOL_V2.md) and every study-2 number, table and figure of the paper.

    python experiments/analyze_study2.py

Inputs : results/tier_b/s2_heldout_B.csv, s2_heldout_B_gz.csv, results/tier_c/s2_heldout_C*/gz-*.json
Outputs: results/study2/report.md; paper_journal/tables/numbers_s2.tex (macros \\vK<Name>), tab_s2_*.tex;
         paper_journal/figures/fig_s2_*.pdf. Parts without input files are skipped.
"""
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "paper_journal"
TB, TC, OUT = ROOT / "results" / "tier_b", ROOT / "results" / "tier_c", ROOT / "results" / "study2"
CFG = ["exec_level", "latency_level", "kappa", "window"]
PROP = "proposed+periodic:60"
M = {  # key: (spec, label in tables/figures)
    "Prop": (PROP, "Proposed"),
    "Rep": ("regret_repair+periodic:60", "Regret-2 repair (no search)"),
    "Fix": ("alns_fixed+periodic:60", "ALNS, fixed 250 ms"),
    "Forty": ("alns_fixed@40+periodic:60", "ALNS, fixed 40 ms"),
    "Scaled": ("alns_scaled~ms=1+periodic:60", "ALNS, size-scaled budget"),
    "Stag": ("alns_stagnation+periodic:60", "ALNS, stagnation stop"),
    "Prof": ("profile+periodic:60", "Performance profile"),
    "Onl": ("online_curve+periodic:60", "Online performance prediction"),
    "AS": ("anytime+periodic:60", "AnytimeSwarm"),
    "Risk": ("anytime_risk+periodic:60", "AnytimeSwarm-R"),
    "Buf": ("alns_fixed@40~buf=60+periodic:60", "Constant 60 s buffer"),
    "Conv": ("alns_fixed@40+event", "Conventional (40 ms, event-only)"),
    "AblTrig": ("proposed+event", "Proposed, event-only trigger"),
    "AblStop": ("alns_fixed@40~z=auto+periodic:60", "Proposed model, fixed 40 ms stop"),
    "AblZ": ("proposed~z=0+periodic:60", "Proposed, mean correction only"),
}
H1 = ["Forty", "Scaled", "Onl", "Prof", "Risk", "Buf"]
CITE = {"Fix": "~\\cite{ropke2006adaptive}", "Forty": "~\\cite{ropke2006adaptive}",
        "Prof": "~\\cite{boddy1994deliberation,zilberstein1996using}", "Onl": "~\\cite{svegliato2018meta}",
        "Buf": "~\\cite{agra2013robust}", "Stag": "", "Scaled": "", "AS": "", "Risk": "", "Rep": "", "Conv": ""}
MAC = {}
REPORT = []
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "xtick.labelsize": 8.5,
                     "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "text.color": "black", "axes.labelcolor": "black",
                     "xtick.color": "black", "ytick.color": "black", "axes.edgecolor": "black",
                     "font.family": "serif", "mathtext.fontset": "stix", "font.serif": ["STIXGeneral", "DejaVu Serif"]})
COL = {"Prop": "#C62828", "Forty": "#1F6FC5", "Buf": "#178A5E", "Conv": "#6B6B6B", "Fix": "#D9622B",
       "Onl": "#6A4BB5", "Scaled": "#0E7C86", "Prof": "#8C6D1F", "Risk": "#B8337C", "AS": "#4C4C4C",
       "Stag": "#2E2E8F", "Rep": "#9E9E9E"}


def put(k, v):
    MAC["K" + k] = v


def pp(x, d=2):
    return f"{x * 100:.{d}f}"


def spp(x, d=2):
    return f"{x * 100:+.{d}f}".replace("-", "$-$")


def boot(d, n=10_000, seed=0, level=95):
    d = np.asarray(d, float)
    idx = np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    a = (100 - level) / 2
    lo, hi = np.percentile(m, [a, 100 - a])
    p = 2 * min(np.mean(m <= 0), np.mean(m >= 0))
    return float(d.mean()), float(lo), float(hi), float(min(p, 1.0))


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(run, 1.0)
    return adj


def ci(m, lo, hi, d=2):
    return f"{spp(m, d)} [{spp(lo, d)}, {spp(hi, d)}]"


def pval(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def paired(df, a, b, metric="utility_rate", by=CFG):
    w = df[df.method.isin([a, b])].pivot_table(index=["scenario"] + by, columns="method", values=metric).dropna()
    return (w[a] - w[b]).groupby(level="scenario").mean()


# ---------------------------------------------------------------------------------------------- tier B main
def tier_b():
    f = TB / "s2_heldout_B.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    df = df[df.method.isin([v[0] for v in M.values()])]
    put("NMissions", str(df.scenario.nunique()))
    put("NConfigs", str(df.groupby(CFG).ngroups))
    put("NRuns", f"{len(df):,}".replace(",", "\\,"))
    put("NMethods", str(df.method.nunique()))
    g = df.groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"), calls=("n_replans", "mean"),
                                 late=("late_served", "mean"), lost=("dropped_by_delay", "mean"),
                                 skip=("dropped_in_exec", "mean"), served=("served", "mean"))
    for k, (spec, _) in M.items():
        if spec in g.index:
            put(f"U{k}", pp(g.loc[spec, "u"]))
            put(f"Ms{k}", f"{g.loc[spec, 'ms']:.1f}")
            put(f"Calls{k}", f"{g.loc[spec, 'calls']:.1f}")
    rows = {}
    # H1: proposed vs six baselines, Holm
    tests = []
    for k in H1:
        if M[k][0] in g.index:
            tests.append((k,) + boot(paired(df, PROP, M[k][0])))
    adj = holm(np.array([t[4] for t in tests])) if tests else []
    REPORT.extend(["## H1: proposed vs. six baselines (periodic trigger), pooled, Holm", "",
                   "| baseline | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"])
    for (k, m, lo, hi, p), pa in zip(tests, adj):
        put(f"D{k}", ci(m, lo, hi))
        put(f"Dm{k}", spp(m))
        put(f"P{k}", pval(pa))
        rows[k] = (ci(m, lo, hi), pval(pa))
        REPORT.append(f"| {M[k][1]} | {ci(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
    put("HOneAll", "all" if len(adj) and all(a < 0.05 and t[1] > 0 for a, t in zip(adj, tests)) else "not all")
    put("HOneNSig", str(sum(1 for a, t in zip(adj, tests) if a < 0.05 and t[1] > 0)))
    # H2 and secondary comparisons
    REPORT.extend(["", "## H2 and secondary pooled comparisons (proposed minus method)", "",
                   "| method | diff pp [95% CI] | p |", "|---|---|---|"])
    for k in ["Conv", "Fix", "Stag", "AS", "Rep", "AblTrig", "AblStop", "AblZ"]:
        if M[k][0] in g.index:
            m, lo, hi, p = boot(paired(df, PROP, M[k][0]))
            put(f"D{k}", ci(m, lo, hi))
            put(f"Dm{k}", spp(m))
            put(f"Dabs{k}", pp(m))
            put(f"PRaw{k}", pval(p))
            rows.setdefault(k, (ci(m, lo, hi), "--"))
            REPORT.append(f"| {M[k][1]} | {ci(m, lo, hi)} | {p:.4f} |")
    for k in [k for k in M if k != "Prop" and M[k][0] in g.index]:
        put(f"URel{k}", f"{(g.loc[PROP, 'u'] / g.loc[M[k][0], 'u'] - 1) * 100:.1f}")
        put(f"LateRed{k}", f"{(1 - g.loc[PROP, 'late'] / g.loc[M[k][0], 'late']) * 100:.0f}")
    for k in M:
        if M[k][0] in g.index:
            put(f"Late{k}", f"{g.loc[M[k][0], 'late']:.2f}")
            put(f"Lost{k}", f"{g.loc[M[k][0], 'lost']:.2f}")
    # H3: equivalence of the stopping rule (TOST, margin 0.5 pp, 90% CI)
    if M["AblStop"][0] in g.index:
        m, lo, hi, _ = boot(paired(df, PROP, M["AblStop"][0]), level=90)
        put("TostCI", f"{spp(m)} [{spp(lo)}, {spp(hi)}]")
        put("TostEquiv", "equivalent" if lo > -0.005 and hi < 0.005 else "not shown equivalent")
        REPORT.extend(["", f"H3 TOST (margin 0.5 pp): proposed minus fixed-40-ms stop on the proposed model, 90% CI "
                       f"{ci(m, lo, hi)} -> {'equivalent' if lo > -0.005 and hi < 0.005 else 'not shown equivalent'}"])
        ms = paired(df, PROP, M["AblStop"][0], "plan_ms_mean")
        m, lo, hi, _ = boot(ms)
        put("TostMs", f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]".replace("-", "$-$"))
    for kap in sorted(df.kappa.unique()):
        sub = df[df.kappa == kap]
        tag = {10.0: "Ten", 50.0: "Fifty", 200.0: "TwoHundred"}.get(kap, str(int(kap)))
        for k in ["Fix", "Forty", "Buf", "Conv", "AblStop", "Onl", "Scaled"]:
            if M[k][0] in g.index:
                m, lo, hi, _ = boot(paired(sub, PROP, M[k][0], by=["exec_level", "latency_level", "window"]))
                put(f"D{k}K{tag}", ci(m, lo, hi))
        lost = sub.groupby("method").dropped_by_delay.mean()
        for k in ["Prop", "Fix", "Forty"]:
            put(f"Lost{k}K{tag}", f"{lost.get(M[k][0], float('nan')):.2f}")
    for wf, tag in [(1.0, "WOne"), (0.5, "WHalf")]:
        for xl in ["mid", "high"]:
            sub = df[(df.window == wf) & (df.exec_level == xl)]
            for k in ["Forty", "Buf", "Conv", "AblZ"]:
                m, lo, hi, _ = boot(paired(sub, PROP, M[k][0], by=["latency_level", "kappa"]))
                put(f"D{k}{tag}{xl.capitalize()}", ci(m, lo, hi))
            put(f"UProp{tag}{xl.capitalize()}", pp(sub[sub.method == PROP].utility_rate.mean()))
            for k in ["Prop", "Buf", "Forty"]:
                s = sub[sub.method == M[k][0]]
                put(f"Served{k}{tag}{xl.capitalize()}", f"{s.served.mean():.1f}")
                put(f"Late{k}{tag}{xl.capitalize()}", f"{s.late_served.mean():.1f}")
    per = []
    for key, gg in df.groupby(CFG):
        w = gg.pivot_table(index="scenario", columns="method", values="utility_rate")
        for k in H1 + ["Conv"]:
            if M[k][0] in w:
                _, lo, hi, _ = boot(w[PROP] - w[M[k][0]], n=4000)
                per.append((k, "+" if lo > 0 else ("-" if hi < 0 else "0")))
    per = pd.DataFrame(per, columns=["k", "s"])
    for k in H1 + ["Conv"]:
        s = per[per.k == k].s.value_counts()
        put(f"Win{k}", str(s.get("+", 0)))
        put(f"Loss{k}", str(s.get("-", 0)))
    table_main(df, g, rows)
    table_regime(df)
    fig_main(df, g, tests)
    fig_regime(df)
    return df


def table_main(df, g, rows):
    order = ["Prop", "Conv", "Rep", "Fix", "Forty", "Scaled", "Stag", "Prof", "Onl", "AS", "Risk", "Buf",
             "AblTrig", "AblStop", "AblZ"]
    lines = ["\\begin{table}[t]",
             f"\\caption{{Tier B, held-out missions of study 2: {df.scenario.nunique()} missions $\\times$ "
             f"{df.groupby(CFG).ngroups} configurations per method. Utility, tasks served late (Late), tasks lost "
             "because a plan arrived too late (Lost), planning calls and computation per call; difference of the "
             "proposed method minus each method, pooled over configurations (percentage points, 95\\% paired bootstrap "
             "interval; Holm-adjusted $p$ for the six primary comparisons, marked $^{\\ast}$).}\\label{tab:s2main}",
             "\\centering\\small", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lrrrrrl}", "\\toprule",
             "Method & Utility (\\%) & Late & Lost & Calls & ms/call & Proposed minus method (pp) \\\\", "\\midrule"]
    for i, k in enumerate(order):
        spec, lab = M[k]
        if spec not in g.index:
            continue
        if k == "AblTrig":
            lines.append("\\midrule")
            lines.append("\\multicolumn{7}{l}{\\textit{Ablations of the proposed method}} \\\\")
        r = g.loc[spec]
        d = rows.get(k, ("--", "--"))
        star = f", $p$ {d[1]}$^{{\\ast}}$" if k in H1 else ""
        name = ("\\textbf{" + lab + "}") if k == "Prop" else lab + CITE.get(k, "")
        lines.append(f"{name} & {pp(r.u)} & {r.late:.2f} & {r.lost:.2f} & {r.calls:.1f} & {r.ms:.1f} & "
                     f"{'--' if k == 'Prop' else d[0] + star} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s2_main.tex").write_text("\n".join(lines) + "\n")


def table_regime(df):
    keys = ["Prop", "Buf", "Forty", "Fix", "Conv"]
    cols = [(xl, wf, k) for xl in ["mid", "high"] for wf in [1.0, 0.5] for k in [10.0, 50.0, 200.0]]
    t = df.pivot_table(index="method", columns=["exec_level", "window", "kappa"], values="utility_rate")
    head1 = " & ".join(f"\\multicolumn{{3}}{{c}}{{{xl}, windows $\\times${wf:g}}}" for xl in ["mid", "high"]
                       for wf in [1.0, 0.5])
    lines = ["\\begin{table}[t]",
             "\\caption{Utility (\\%) per regime: disturbance level, time-window factor and latency factor "
             "$\\kappa_B$ (10, 50, 200), tier B held-out missions of study 2. Bold: best of the five methods.}"
             "\\label{tab:s2regime}", "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{2.2pt}",
             "\\begin{tabular}{l" + "r" * len(cols) + "}", "\\toprule",
             " & " + head1 + " \\\\",
             "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}\\cmidrule(lr){11-13}",
             "Method & " + " & ".join(f"{int(c[2])}" for c in cols) + " \\\\", "\\midrule"]
    best = {c: max(t.loc[M[k][0], c] for k in keys if M[k][0] in t.index) for c in cols}
    for k in keys:
        if M[k][0] not in t.index:
            continue
        cells = []
        for c in cols:
            v = t.loc[M[k][0], c]
            s = pp(v, 1)
            cells.append(f"\\textbf{{{s}}}" if abs(v - best[c]) < 1e-12 else s)
        lab = M[k][1] if k != "Conv" else "Conventional"
        lines.append(f"{lab} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s2_regime.tex").write_text("\n".join(lines) + "\n")


def fig_main(df, g, tests):
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.3), gridspec_kw={"width_ratios": [1.0, 1.05]})
    ax = axes[0]
    keys = ["Rep", "Fix", "Stag", "AS", "Conv"] + [k for k, *_ in tests]
    est = []
    for k in keys:
        if M[k][0] in g.index:
            m, lo, hi, _ = boot(paired(df, PROP, M[k][0]), n=4000)
            est.append((k, m * 100, lo * 100, hi * 100))
    est.sort(key=lambda e: e[1])
    y = np.arange(len(est))
    for i, (k, m, lo, hi) in enumerate(est):
        c = "#C62828" if lo > 0 else ("#1F6FC5" if hi < 0 else "#6B6B6B")
        ax.errorbar(m, i, xerr=[[m - lo], [hi - m]], fmt="o", ms=4, capsize=2.5, color=c, lw=1.1)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, [M[k][1] for k, *_ in est])
    ax.set_xlabel("proposed minus method (percentage points)")
    ax.set_title("(a) paired difference, 95% CI", loc="left")
    ax.grid(axis="x", alpha=0.3)
    ax = axes[1]
    for k, (spec, lab) in M.items():
        if spec not in g.index or k.startswith("Abl"):
            continue
        r = g.loc[spec]
        ax.scatter(max(r.ms, 0.5), r.u * 100, s=42 if k == "Prop" else 26, color=COL.get(k, "#444444"),
                   marker="*" if k == "Prop" else "o", zorder=3, edgecolor="black", linewidth=0.4)
    ax.set_xscale("log")
    ax.set_xlabel("computation per planning call (ms)")
    ax.set_ylabel("utility (%)")
    ax.set_title("(b) utility and computation", loc="left")
    ax.grid(alpha=0.3)
    ax.set_xlim(0.3, 2e4)
    ax.set_xticks([1, 10, 100, 1000])
    # isolated points: label next to the marker; the dense cluster: labels in a column at the right, joined by
    # thin leader lines in the order of the utility so that no label overlaps another
    lab = {"Prop": ("Proposed", (6, 0), "left"), "Buf": ("60 s buffer", (6, 0), "left"),
           "Conv": ("Conventional", (6, 0), "left"), "Fix": ("ALNS 250 ms", (-6, 0), "right"),
           "Rep": ("repair only", (6, 0), "left")}
    for k, (t, off, ha) in lab.items():
        if M[k][0] in g.index:
            r = g.loc[M[k][0]]
            ax.annotate(t, (max(r.ms, 0.5), r.u * 100), textcoords="offset points", xytext=off, fontsize=8,
                        ha=ha, va="center", color="black")
    col = {"Risk": "AnytimeSwarm-R", "AS": "AnytimeSwarm", "Stag": "stagnation stop", "Prof": "profile",
           "Scaled": "size-scaled", "Onl": "online prediction", "Forty": "ALNS 40 ms"}
    cl = sorted([k for k in col if M[k][0] in g.index], key=lambda k: -g.loc[M[k][0]].u)
    top = g.loc[M["Buf"][0]].u * 100 - 0.45 if M["Buf"][0] in g.index else 50.4
    for i, k in enumerate(cl):
        r = g.loc[M[k][0]]
        ax.annotate(col[k], (max(r.ms, 0.5), r.u * 100), xytext=(220, top - 0.36 * i), textcoords="data",
                    fontsize=8, ha="left", va="center", color="black",
                    arrowprops=dict(arrowstyle="-", lw=0.5, color="#555555", shrinkA=1, shrinkB=3))
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s2_main.pdf")
    plt.close(fig)


def fig_regime(df):
    keys = ["Prop", "Buf", "Forty", "Fix", "Conv"]
    fig, axes = plt.subplots(1, 4, figsize=(6.3, 2.35), sharey=False)
    for ax, (xl, wf) in zip(axes, [("mid", 1.0), ("mid", 0.5), ("high", 1.0), ("high", 0.5)]):
        sub = df[(df.exec_level == xl) & (df.window == wf)]
        t = sub.pivot_table(index="kappa", columns="method", values="utility_rate") * 100
        for k in keys:
            if M[k][0] in t:
                ax.plot(t.index, t[M[k][0]], marker="*" if k == "Prop" else "o", ms=6 if k == "Prop" else 3.5,
                        color=COL[k], lw=1.6 if k == "Prop" else 1.0, label=M[k][1] if k != "Conv" else "Conventional")
        ax.set_xscale("log")
        ax.set_xticks([10, 50, 200], ["10", "50", "200"])
        ax.minorticks_off()
        ax.set_title(f"{xl}, windows $\\times${wf:g}", fontsize=8.5)
        ax.set_xlabel("$\\kappa_B$")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("utility (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=7.8)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(P / "figures" / "fig_s2_regime.pdf")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------- tier C
def tier_c():
    rows = []
    for d, trig in [("s2_heldout_C", "periodic:60"), ("s2_heldout_C_event", "event")]:
        for f in sorted((TC / d).glob("gz-*.json")) if (TC / d).exists() else []:
            m = json.loads(f.read_text())
            r = {k: v for k, v in m.items() if not k.startswith("_")}
            r["spec"] = f"{r['method']}+{trig}"
            rows.append(r)
    if not rows:
        return
    c = pd.DataFrame(rows)
    spec_map = {"proposed+periodic:60": "Prop", "alns_fixed@40+periodic:60": "Forty",
                "alns_fixed@40~buf=60+periodic:60": "Buf", "alns_fixed@40+event": "Conv"}
    c["k"] = c.spec.map(spec_map)
    put("CN", str(c.scenario.nunique()))
    put("CRuns", str(len(c)))
    put("CRTF", f"{c.rtf.mean():.2f}")
    put("CRTFmin", f"{c.rtf.min():.2f}")
    inv = sum(len(list((TC / d / "invalid_rtf").glob("gz-*.json"))) for d in ["s2_heldout_C", "s2_heldout_C_event"]
              if (TC / d / "invalid_rtf").exists())
    fails = sum(len(list((TC / d).glob("fail_*.log"))) for d in ["s2_heldout_C", "s2_heldout_C_event"]
                if (TC / d).exists())
    put("CInvalid", str(inv))
    put("CFails", str(fails))
    w = c.pivot_table(index="scenario", columns="k", values="utility_rate").dropna()
    g = c.groupby("k").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"), late=("late_served", "mean"),
                           calls=("n_replans", "mean"), skip=("dropped_in_exec", "mean"))
    for k in g.index:
        put(f"CU{k}", pp(g.loc[k, "u"]))
        put(f"CMs{k}", f"{g.loc[k, 'ms']:.1f}")
    tests = [(k,) + boot(w["Prop"] - w[k]) for k in ["Forty", "Conv"] if k in w and "Prop" in w]
    adj = holm(np.array([t[4] for t in tests])) if tests else []
    REPORT.extend(["", "## H4: tier C (PX4 SITL + Gazebo)", "",
                   f"{c.scenario.nunique()} missions, {len(c)} runs, RTF {c.rtf.mean():.2f} (min {c.rtf.min():.2f}), "
                   f"repeated for RTF: {inv}, failed attempts: {fails}", "",
                   "| baseline | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"])
    for (k, m, lo, hi, p), pa in zip(tests, adj):
        put(f"CD{k}", ci(m, lo, hi))
        put(f"CP{k}", pval(pa))
        REPORT.append(f"| {M[k][1]} | {ci(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
    if "Buf" in w:
        m, lo, hi, p = boot(w["Prop"] - w["Buf"])
        put("CDBuf", ci(m, lo, hi))
        REPORT.append(f"| {M['Buf'][1]} (secondary) | {ci(m, lo, hi)} | {p:.4f} | -- |")
    fb = TB / "s2_heldout_B_gz.csv"
    bm = pd.Series(dtype=float)
    if fb.exists():
        from scipy.stats import kendalltau, pearsonr
        b = pd.read_csv(fb)
        b["k"] = b.method.map(spec_map)
        bm = b.groupby("k").utility_rate.mean()
        both = c[["scenario", "k", "utility_rate"]].merge(b[["scenario", "k", "utility_rate"]], on=["scenario", "k"],
                                                         suffixes=("_c", "_b"))
        put("BCr", f"{pearsonr(both.utility_rate_b, both.utility_rate_c).statistic:.2f}")
        put("BCn", str(len(both)))
        com = bm.index.intersection(g.index)
        put("BCTau", f"{kendalltau(bm[com], g.loc[com, 'u']).statistic:.2f}")
        wb = b.pivot_table(index="scenario", columns="k", values="utility_rate").dropna()
        for k in ["Forty", "Conv", "Buf"]:
            if k in wb:
                m, lo, hi, _ = boot(wb["Prop"] - wb[k])
                put(f"BgzD{k}", ci(m, lo, hi))
        REPORT.append(f"\nTier B vs C (same missions): r per run {MAC.get('KBCr')}, Kendall tau {MAC.get('KBCTau')}")
        fig_bc(w, wb)
    lines = ["\\begin{table}[t]",
             f"\\caption{{Tier C (PX4 SITL, Gazebo, ROS~2), study 2: {c.scenario.nunique()} held-out missions per "
             "method, mid disturbances, $\\kappa_B=50$. Utility, tasks served late, tasks skipped at departure, planning "
             "calls and computation per call; tier B utility on the same rescaled missions.}\\label{tab:s2tierc}",
             "\\centering\\small", "\\begin{tabular}{lrrrrrr}", "\\toprule",
             "Method & Utility C (\\%) & Late & Skipped & Calls & ms/call & Utility B (\\%) \\\\", "\\midrule"]
    for k in ["Prop", "Forty", "Buf", "Conv"]:
        if k in g.index:
            r = g.loc[k]
            lab = ("\\textbf{" + M[k][1] + "}") if k == "Prop" else M[k][1]
            lines.append(f"{lab} & {pp(r.u)} & {r.late:.2f} & {r.skip:.2f} & {r.calls:.1f} & {r.ms:.1f} & "
                         f"{pp(bm[k]) if k in bm.index else '--'} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s2_tierc.tex").write_text("\n".join(lines) + "\n")


def fig_bc(wc, wb):
    keys = [k for k in ["Forty", "Buf", "Conv"] if k in wc and k in wb]
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    for i, k in enumerate(keys):
        for dx, w, col, mk, lab in [(-0.12, wb, "#1F6FC5", "s", "tier B (kinematic)"),
                                    (0.12, wc, "#C62828", "o", "tier C (PX4 + Gazebo)")]:
            m, lo, hi, _ = boot(w["Prop"] - w[k], n=4000)
            ax.errorbar(i + dx, m * 100, yerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt=mk, ms=5, capsize=2.5,
                        color=col, label=lab if i == 0 else None)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(keys)), [{"Forty": "vs. 40 ms", "Buf": "vs. buffer", "Conv": "vs. conventional"}[k]
                                     for k in keys])
    ax.set_ylabel("proposed minus method (pp)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_s2_bc.pdf")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (P / "tables").mkdir(exist_ok=True)
    REPORT.extend(["# Study 2: pre-registered held-out analysis (docs/08_PROTOCOL_V2.md)", ""])
    for part in (tier_b, tier_c):
        try:
            part()
        except (KeyError, ValueError, IndexError) as e:
            print(f"[skip] {part.__name__}: incomplete results ({type(e).__name__}: {e})")
    (OUT / "report.md").write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    out = ["% generated by experiments/analyze_study2.py -- do not edit"]
    out += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s2.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(REPORT))
    print(f"{len(MAC)} macros")


if __name__ == "__main__":
    main()
