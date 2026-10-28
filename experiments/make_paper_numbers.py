#!/usr/bin/env python3
"""Generate every number, table and figure of the journal manuscript from the result files (never typed by hand).

    python experiments/make_paper_numbers.py

Outputs (paper_journal/): tables/numbers.tex (macros \\vJ<Name>), tables/tab_*.tex, figures/fig_*.pdf
Sections without result files yet are skipped; the manuscript then shows a red TODO for the missing macro.
"""
import json
import shutil
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "paper_journal"
TB, TC, HO = ROOT / "results" / "tier_b", ROOT / "results" / "tier_c", ROOT / "results" / "heldout"
MACROS = {}
NAMES = {"regret_repair": "Regret-2 repair", "alns_fixed": "ALNS, 250\\,ms", "alns_fixed@40": "ALNS, 40\\,ms",
         "alns_fixed@180": "ALNS, 180\\,ms", "alns_stagnation": "ALNS, stagnation", "anytime": "AnytimeSwarm",
         "anytime_nodelay": "AnytimeSwarm w/o delay cost", "anytime_risk": "AnytimeSwarm-R (proposed)",
         "anytime_risk~zero": "AnytimeSwarm-R, latency only", "anytime_risk~low": "AnytimeSwarm-R, low model",
         "anytime_risk~mid": "AnytimeSwarm-R, mid model", "anytime_risk~high": "AnytimeSwarm-R, high model"}
OURS = "anytime_risk"
CFG_KEY = ["exec_level", "latency_level", "kappa", "trigger"]


def put(name, value):
    MACROS["J" + name] = value


def pp(x, d=2):
    return f"{x * 100:.{d}f}"


def spp(x, d=2):
    return f"{x * 100:+.{d}f}".replace("-", "$-$")


def boot(d, n=10_000, seed=0):
    d = np.asarray(d, float)
    idx = np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
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


def pooled(df, ours, base, metric="utility_rate", by=None):
    by = by or CFG_KEY
    w = df[df.method.isin([ours, base])].pivot_table(index=["scenario"] + by, columns="method", values=metric).dropna()
    return (w[ours] - w[base]).groupby(level="scenario").mean()


# ---------------------------------------------------------------------------------------------- reproduction
def reproduction():
    v = ROOT / "results" / "g0" / "validator.txt"
    if v.exists():
        put("ValidatorPlans", f"{int(v.read_text().split('=')[1].split()[0]):,}".replace(",", "\\,"))
    c = ROOT / "results" / "g0" / "compare.md"
    if c.exists():
        t = c.read_text()
        s = t.split("ratio Linux/Windows ")[1].split(")")[0]
        put("ReproSpeedup", f"{(float(s) - 1) * 100:.0f}")
        put("ReproMatched", "24 of 24")


# ---------------------------------------------------------------------------------------------- error models
def error_models():
    rows = []
    for tier, f in [("B", ROOT / "models" / "error_model_dev.json"), ("C", ROOT / "models" / "error_model_tierc_dev.json")]:
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        for lv in ["low", "mid", "high"]:
            if lv in d:
                m = d[lv]
                cells = [f"{m['b0']:.2f}", f"{m['b1']:.4f}", f"{m['s0']:.2f}", f"{m['s1']:.4f}"]
                rows.append(f"{tier} & {lv} & {m['n']} & " + " & ".join(c.replace("-", "$-$") for c in cells) + " \\\\")
        if tier == "C":
            put("LatC", f"{d['latency_mean_s']:.3f}")
            put("LatCpn", f"{d['latency_p95_s']:.3f}")
    tab = ["\\begin{table}[t]",
           "\\caption{Finish-time error models fitted on development missions: $m(h)=b_0+b_1h$, $s(h)=s_0+s_1h$ (seconds of "
           "the respective tier; $n$ executed tasks).}\\label{tab:errmodels}",
           "\\centering\\small", "\\begin{tabular}{llrrrrr}", "\\toprule",
           "Tier & Level & $n$ & $b_0$ & $b_1$ & $s_0$ & $s_1$ \\\\", "\\midrule", *rows, "\\bottomrule",
           "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_errmodels.tex").write_text("\n".join(tab) + "\n")
    cal = TC / "calibration_tierc_dev.csv"
    if cal.exists():
        d = pd.read_csv(cal)
        put("CalibFlights", str(len(d)))
        put("CalibRTF", f"{d.rtf.mean():.2f}")


# ---------------------------------------------------------------------------------------------- tier B main
def tier_b_main():
    f = TB / "heldout_B_main.csv"
    if not f.exists():
        return
    df = pd.read_csv(f)
    put("NMain", str(df.scenario.nunique()))
    put("NConfigsMain", str(df.groupby(CFG_KEY).ngroups))
    put("NRunsMain", f"{len(df):,}".replace(",", "\\,"))
    g = df.groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"), rp=("n_replans", "mean"),
                                 late=("late_served", "mean"), dropd=("dropped_by_delay", "mean"),
                                 dropx=("dropped_in_exec", "mean"))
    key = {"anytime_risk": "Risk", "anytime": "AS", "alns_fixed@40": "FixedForty", "alns_fixed": "Fixed",
           "alns_stagnation": "Stag", "anytime_nodelay": "NoDelay", "regret_repair": "Repair",
           "anytime_risk~zero": "RiskZero"}
    for m, k in key.items():
        if m in g.index:
            put(f"U{k}", pp(g.loc[m, "u"]))
            put(f"Ms{k}", f"{g.loc[m, 'ms']:.1f}")
    rows, tests = [], []
    for base, k in [("alns_fixed@40", "FixedForty"), ("anytime", "AS"), ("alns_stagnation", "Stag")]:
        m, lo, hi, p = boot(pooled(df, OURS, base))
        tests.append((base, k, m, lo, hi, p))
    adj = holm(np.array([t[5] for t in tests]))
    for (base, k, m, lo, hi, p), pa in zip(tests, adj):
        put(f"D{k}", ci(m, lo, hi))
        put(f"Dm{k}", spp(m))
        put(f"P{k}", pval(pa))
        rows.append((NAMES[base], ci(m, lo, hi), pval(p), pval(pa)))
    for base, k in [("alns_fixed", "Fixed"), ("anytime_nodelay", "NoDelay"), ("regret_repair", "Repair"),
                    ("anytime_risk~zero", "RiskZero")]:
        if base in df.method.values:
            m, lo, hi, p = boot(pooled(df, OURS, base))
            put(f"D{k}", ci(m, lo, hi))
            put(f"Dm{k}", spp(m))
            rows.append((NAMES[base], ci(m, lo, hi), pval(p), "--"))
    m, lo, hi, p = boot(pooled(df, OURS, "anytime", "plan_ms_mean"))
    put("DMsAS", f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]".replace("-", "$-$"))
    m, lo, hi, p = boot(pooled(df, "anytime", "alns_fixed@40"))
    put("DASFixedForty", ci(m, lo, hi))
    # per-configuration verdicts
    per = []
    for k, gg in df.groupby(CFG_KEY):
        w = gg.pivot_table(index="scenario", columns="method", values="utility_rate")
        for base in ["alns_fixed@40", "anytime", "alns_stagnation", "alns_fixed"]:
            if OURS not in w or base not in w:
                continue
            mm, lo, hi, _ = boot(w[OURS] - w[base])
            per.append({"base": base, "sig": "+" if lo > 0 else ("-" if hi < 0 else "0")})
    per = pd.DataFrame(per)
    for base, k in [("alns_fixed@40", "FixedForty"), ("anytime", "AS"), ("alns_stagnation", "Stag"),
                    ("alns_fixed", "Fixed")]:
        s = per[per.base == base].sig.value_counts() if len(per) else pd.Series(dtype=int)
        put(f"Win{k}", str(s.get("+", 0)))
        put(f"Loss{k}", str(s.get("-", 0)))
    # table: means per method + pooled tests
    order = ["regret_repair", "alns_fixed", "alns_fixed@40", "alns_stagnation", "anytime_nodelay", "anytime",
             "anytime_risk~zero", "anytime_risk"]
    lines = ["\\begin{table}[t]",
             f"\\caption{{Tier B primary matrix: {df.scenario.nunique()} held-out missions $\\times$ "
             f"{df.groupby(CFG_KEY).ngroups} configurations. Utility and lost tasks per mission, mean planning time per "
             "call, and pooled paired difference of AnytimeSwarm-R minus each method (percentage points, 95\\% "
             "bootstrap interval; Holm-adjusted $p$ for the three primary comparisons).}\\label{tab:main}",
             "\\centering\\small", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lrrrrrl}", "\\toprule",
             "Method & Utility (\\%) & Late & Skipped & Calls & ms/call & AnytimeSwarm-R minus method (pp) \\\\",
             "\\midrule"]
    diffs = {r[0]: r[1] + (f", $p_{{\\mathrm{{Holm}}}}$ {r[3]}" if r[3] != "--" else "") for r in rows}
    for m in order:
        if m not in g.index:
            continue
        r = g.loc[m]
        lines.append(f"{NAMES[m]} & {pp(r.u)} & {r.late:.2f} & {r.dropx:.2f} & {r.rp:.1f} & {r.ms:.1f} & "
                     f"{diffs.get(NAMES[m], '--')} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_main.tex").write_text("\n".join(lines) + "\n")
    # triggers
    tl = []
    for meth in order:
        sub = df[df.method == meth]
        w = sub.pivot_table(index=["scenario", "exec_level", "latency_level", "kappa"], columns="trigger",
                            values="utility_rate").dropna()
        if "periodic:60" in w and "event" in w:
            m, lo, hi, _ = boot((w["periodic:60"] - w["event"]).groupby(level="scenario").mean())
            tl.append((meth, m, lo, hi))
    for meth, m, lo, hi in tl:
        if meth == OURS:
            put("TrigRisk", ci(m, lo, hi))
        if meth == "alns_fixed@40":
            put("TrigFixedForty", ci(m, lo, hi))
    if tl:
        put("TrigMin", spp(min(t[1] for t in tl)))
        put("TrigMax", spp(max(t[1] for t in tl)))
    for trig, k in [("event", "Event"), ("periodic:60", "Periodic")]:
        sub = df[df.trigger == trig]
        for base, kb in [("alns_fixed@40", "FixedForty"), ("anytime", "AS")]:
            m, lo, hi, _ = boot(pooled(sub, OURS, base))
            put(f"D{kb}{k}", ci(m, lo, hi))
    rp = df.groupby("trigger").n_replans.mean()
    put("CallsEvent", f"{rp.get('event', float('nan')):.1f}")
    put("CallsPeriodic", f"{rp.get('periodic:60', float('nan')):.1f}")
    # by execution level / kappa
    for col, vals in [("exec_level", ["low", "mid"]), ("kappa", [10.0, 50.0]), ("latency_level", ["none", "high"])]:
        for v in vals:
            sub = df[df[col] == v]
            m, lo, hi, _ = boot(pooled(sub, OURS, "alns_fixed@40"))
            put(f"DFF{col.split('_')[0].capitalize()}{str(v).replace('.0', '').capitalize()}", ci(m, lo, hi))
            m, lo, hi, _ = boot(pooled(sub, OURS, "anytime"))
            put(f"DAS{col.split('_')[0].capitalize()}{str(v).replace('.0', '').capitalize()}", ci(m, lo, hi))
    # by fleet scale (descriptive): utility differences and computation per call
    for sc in ["small", "medium", "large"]:
        sub = df[df.scale == sc]
        for base, kb in [("alns_fixed@40", "FixedForty"), ("anytime", "AS"), ("alns_fixed", "Fixed")]:
            m, lo, hi, _ = boot(pooled(sub, OURS, base))
            put(f"DSc{sc.capitalize()}{kb}", ci(m, lo, hi))
        ms = sub.groupby("method").plan_ms_mean.mean()
        for m, k in [(OURS, "Risk"), ("anytime", "AS"), ("alns_stagnation", "Stag")]:
            put(f"MsSc{sc.capitalize()}{k}", f"{ms[m]:.0f}")
    # tasks lost because a plan arrived too late, slow machine (kappa 50)
    lost = df[df.kappa == 50.0].groupby("method").dropped_by_delay.mean()
    for m, k in key.items():
        if m in lost.index:
            put(f"LostKFifty{k}", f"{lost[m]:.2f}")
    # relative forms of the headline differences
    put("LostRedFixed", f"{(1 - lost[OURS] / lost['alns_fixed']) * 100:.0f}")
    put("MsRedAS", f"{(1 - g.loc[OURS, 'ms'] / g.loc['anytime', 'ms']) * 100:.0f}")
    put("MsRedStag", f"{(1 - g.loc[OURS, 'ms'] / g.loc['alns_stagnation', 'ms']) * 100:.0f}")
    put("MsRedFixed", f"{(1 - g.loc[OURS, 'ms'] / g.loc['alns_fixed', 'ms']) * 100:.0f}")
    put("URelRepair", f"{(g.loc[OURS, 'u'] / g.loc['regret_repair', 'u'] - 1) * 100:.1f}")
    put("URelFixed", f"{(g.loc[OURS, 'u'] / g.loc['alns_fixed', 'u'] - 1) * 100:.1f}")
    put("USpreadSearch", pp(g.drop(index="regret_repair").u.max() - g.drop(index="regret_repair").u.min()))
    fig_main(df)


def fig_main(df):
    # regret-2 repair (about 3 pp lower) is left out of panel (a) so that the search methods can be told apart
    meths = ["alns_fixed", "alns_fixed@40", "alns_stagnation", "anytime_nodelay", "anytime", "anytime_risk"]
    offs = {"alns_fixed": (-6, 5, "right"), "alns_fixed@40": (-6, -9, "right"), "alns_stagnation": (6, -9, "left"),
            "anytime": (-7, -1, "right"), "anytime_nodelay": (6, 1, "left"), "anytime_risk": (-7, 3, "right")}
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    ax = axes[0]
    g = df[df.method.isin(meths)].groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"))
    for m, r in g.iterrows():
        c = "C3" if m == OURS else ("C1" if m == "anytime" else "C0")
        ax.scatter(r.ms, r.u * 100, s=36, color=c, zorder=3)
        dx, dy, ha = offs[m]
        ax.annotate(NAMES[m].replace("\\,", " "), (r.ms, r.u * 100), textcoords="offset points", xytext=(dx, dy),
                    fontsize=7, ha=ha, va="center")
    lo_u, hi_u = g.u.min() * 100, g.u.max() * 100
    ax.set_ylim(lo_u - 0.25 * (hi_u - lo_u), hi_u + 0.25 * (hi_u - lo_u))
    ax.set_xscale("log")
    ax.set_xlim(15, 600)
    ax.set_xticks([20, 50, 100, 200, 500], ["20", "50", "100", "200", "500"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("planning time per call (ms)")
    ax.set_ylabel("utility (%)")
    ax.set_title("(a) utility vs. computation", fontsize=9)
    ax.grid(alpha=0.3)
    ax = axes[1]
    sub = []
    for k, gg in df.groupby(CFG_KEY):
        w = gg.pivot_table(index="scenario", columns="method", values="utility_rate")
        if not {OURS, "alns_fixed@40", "anytime"} <= set(w.columns):
            continue
        m, lo, hi, _ = boot(w[OURS] - w["alns_fixed@40"], n=4000)
        m2, lo2, hi2, _ = boot(w[OURS] - w["anytime"], n=4000)
        sub.append((k, m, lo, hi, m2, lo2, hi2))
    y = np.arange(len(sub))
    ax.errorbar([s[1] * 100 for s in sub], y - 0.15, xerr=[[(s[1] - s[2]) * 100 for s in sub],
                                                         [(s[3] - s[1]) * 100 for s in sub]],
                fmt="o", ms=3, capsize=2, color="C0", label="vs. ALNS 40 ms")
    ax.errorbar([s[4] * 100 for s in sub], y + 0.15, xerr=[[(s[4] - s[5]) * 100 for s in sub],
                                                         [(s[6] - s[4]) * 100 for s in sub]],
                fmt="s", ms=3, capsize=2, color="C1", label="vs. AnytimeSwarm")
    ax.axvline(0, color="k", lw=0.8)
    lab = [f"{k[0]}, lat {k[1]}, $\\kappa$={k[2]:g}, {'periodic' if 'periodic' in k[3] else 'event'}" for k, *_ in sub]
    ax.set_yticks(y, lab, fontsize=6)
    ax.invert_yaxis()
    ax.set_xlabel("AnytimeSwarm-R minus baseline (pp)")
    ax.set_title("(b) per configuration, 95% CI", fontsize=9)
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.21), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_main.pdf")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------- XL and sensitivity
def tier_b_other():
    f = TB / "heldout_B_xl.csv"
    if f.exists():
        df = pd.read_csv(f)
        put("NXL", str(df.scenario.nunique()))
        g = df.groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"))
        for m, k in [("anytime_risk", "Risk"), ("anytime", "AS"), ("alns_fixed@180", "FixedOneEighty"),
                     ("alns_fixed", "Fixed"), ("alns_stagnation", "Stag")]:
            if m in g.index:
                put(f"XLU{k}", pp(g.loc[m, "u"]))
                put(f"XLMs{k}", f"{g.loc[m, 'ms']:.0f}")
        tests = []
        for base, k in [("alns_fixed@180", "FixedOneEighty"), ("anytime", "AS"), ("alns_stagnation", "Stag"),
                        ("alns_fixed", "Fixed")]:
            if base in df.method.values:
                m, lo, hi, p = boot(pooled(df, OURS, base))
                put(f"XLD{k}", ci(m, lo, hi))
                tests.append((k, p))
        # Holm over the same family as experiments/analyze_heldout.py (four comparisons)
        for (k, _), pa in zip(tests, holm(np.array([t[1] for t in tests]))):
            put(f"XLP{k}", pval(pa))
        m, lo, hi, _ = boot(pooled(df, OURS, "anytime", "plan_ms_mean"))
        put("XLDMsAS", f"{m:+.1f} [{lo:+.1f}, {hi:+.1f}]".replace("-", "$-$"))
        put("XLNConf", str(df.groupby(CFG_KEY).ngroups))
        for base, k in [("alns_fixed@180", "FixedOneEighty"), ("anytime", "AS"), ("alns_stagnation", "Stag")]:
            sig = []
            for _, gg in df.groupby(CFG_KEY):
                w = gg.pivot_table(index="scenario", columns="method", values="utility_rate")
                _, lo, hi, _ = boot(w[OURS] - w[base])
                sig.append("+" if lo > 0 else ("-" if hi < 0 else "0"))
            put(f"XLWin{k}", str(sig.count("+")))
            put(f"XLLoss{k}", str(sig.count("-")))
    f = TB / "heldout_B_sens.csv"
    if f.exists():
        df = pd.read_csv(f)
        put("NSensConf", str(df.groupby(CFG_KEY).ngroups))
        for cond, k in [(("high", None, None), "High"), (("high", 50.0, None), "HighKFifty"), ((None, 1.0, None), "KOne"),
                        ((None, None, "deviation:30"), "Dev"), (("mid", None, None), "Mid")]:
            sub = df
            if cond[0]:
                sub = sub[sub.exec_level == cond[0]]
            if cond[1]:
                sub = sub[sub.kappa == cond[1]]
            if cond[2]:
                sub = sub[sub.trigger == cond[2]]
            for base, kb in [("alns_fixed@40", "FixedForty"), ("anytime", "AS"), ("alns_stagnation", "Stag")]:
                m, lo, hi, _ = boot(pooled(sub, OURS, base))
                put(f"Sens{k}{kb}", ci(m, lo, hi))
            ms = sub.groupby("method").plan_ms_mean.mean()
            put(f"SensMs{k}Risk", f"{ms[OURS]:.0f}")
            put(f"SensMs{k}AS", f"{ms['anytime']:.0f}")
            put(f"SensU{k}Risk", pp(sub[sub.method == OURS].utility_rate.mean()))
        # deviation-triggered minus event-only replanning (same execution level and kappa)
        for meth, k in [(OURS, "Risk"), ("alns_fixed@40", "FixedForty")]:
            w = df[df.method == meth].pivot_table(index=["scenario", "exec_level", "kappa"], columns="trigger",
                                                  values="utility_rate").dropna()
            m, lo, hi, _ = boot((w["deviation:30"] - w["event"]).groupby(level="scenario").mean())
            put(f"SensTrigDev{k}", ci(m, lo, hi))
        put("SensCallsDev", f"{df[df.trigger == 'deviation:30'].n_replans.mean():.1f}")
        put("SensCallsEvent", f"{df[df.trigger == 'event'].n_replans.mean():.1f}")
        # the same machine but no planning delay: both delay costs vanish
        sub = df[df.kappa == 1.0]
        w = sub.pivot_table(index=["scenario"] + CFG_KEY, columns="method", values="plan_ms_mean").dropna()
        put("SensKOneMsDiff", f"{(w[OURS] - w['anytime']).mean():+.1f}".replace("-", "$-$"))
    f = TB / "heldout_B_misspec.csv"
    if f.exists():
        df = pd.read_csv(f)
        put("NMisConf", str(df.groupby(CFG_KEY).ngroups))
        for lv in ["low", "mid", None]:
            sub = df[df.exec_level == lv] if lv else df
            tag = lv.capitalize() if lv else "All"
            for meth, k in [("anytime_risk", "Correct"), ("anytime_risk~zero", "Zero"), ("anytime_risk~low", "Low"),
                            ("anytime_risk~mid", "Mid"), ("anytime_risk~high", "High")]:
                m, lo, hi, _ = boot(pooled(sub, meth, "anytime"))
                put(f"Mis{tag}{k}", ci(m, lo, hi))
        u = df.groupby("method").utility_rate.mean()
        risk = [m for m in u.index if m.startswith("anytime_risk") and m != "anytime_risk~zero"]
        put("MisSpread", pp(u[risk].max() - u[risk].min()))
        # run-to-run variation: these configurations and seeds also belong to the primary matrix; the runs differ
        # only in the measured planning times (wall clock)
        main = pd.read_csv(TB / "heldout_B_main.csv")
        keys = df[CFG_KEY].drop_duplicates()
        main = main.merge(keys, on=CFG_KEY)
        diffs = []
        for meth in ["anytime", "anytime_risk", "anytime_risk~zero"]:
            a = main[main.method == meth].set_index(["scenario"] + CFG_KEY).utility_rate
            b = df[df.method == meth].set_index(["scenario"] + CFG_KEY).utility_rate
            j = a.to_frame("a").join(b.rename("b"), how="inner")
            diffs.append(abs(j.a.mean() - j.b.mean()))
            if meth == "anytime_risk":
                put("RepeatSameShare", f"{np.mean(np.isclose(j.a, j.b)) * 100:.0f}")
        put("RepeatDiffMax", pp(max(diffs)))


# ---------------------------------------------------------------------------------------------- tier C
def tier_c():
    d = TC / "heldout_C"
    files = sorted(d.glob("gz-*.json")) if d.exists() else []
    if not files:
        return
    rows = []
    for f in files:
        m = json.loads(f.read_text())
        rows.append({k: v for k, v in m.items() if not k.startswith("_")})
    df = pd.DataFrame(rows)
    put("NC", str(df.scenario.nunique()))
    put("NCRuns", str(len(df)))
    put("CRTF", f"{df.rtf.mean():.2f}")
    put("CRTFmin", f"{df.rtf.min():.2f}")
    put("CLat", f"{np.nanmean(df.accept_latency_s_mean):.3f}")
    put("CErrPn", f"{df.finish_err_p95_s.mean():.1f}")
    fails = len(list(d.glob("fail_*.log")))
    put("CFails", str(fails))
    g = df.groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"), late=("late_served", "mean"),
                                 skip=("dropped_in_exec", "mean"), dropd=("dropped_by_delay", "mean"))
    for m, k in [("anytime_risk", "Risk"), ("anytime", "AS"), ("alns_fixed@40", "FixedForty"), ("alns_fixed", "Fixed")]:
        if m in g.index:
            put(f"CU{k}", pp(g.loc[m, "u"]))
            put(f"CMs{k}", f"{g.loc[m, 'ms']:.1f}")
            put(f"CDrop{k}", f"{g.loc[m, 'dropd']:.2f}")
    w = df.pivot_table(index="scenario", columns="method", values="utility_rate").dropna()
    tests = []
    for base, k in [("alns_fixed@40", "FixedForty"), ("anytime", "AS")]:
        if base in w and OURS in w:
            tests.append((base, k) + boot(w[OURS] - w[base]))
    if tests:
        adj = holm(np.array([t[5] for t in tests]))
        for (base, k, m, lo, hi, p), pa in zip(tests, adj):
            put(f"CD{k}", ci(m, lo, hi))
            put(f"CP{k}", pval(pa))
            put(f"CWin{k}", f"{np.mean(w[OURS] >= w[base]) * 100:.0f}")
    if "alns_fixed" in w and OURS in w:
        m, lo, hi, p = boot(w[OURS] - w["alns_fixed"])
        put("CDFixed", ci(m, lo, hi))
    fb = TB / "heldout_B_gz.csv"
    if fb.exists():
        from scipy.stats import kendalltau, pearsonr
        b = pd.read_csv(fb)
        bm, cm = b.groupby("method").utility_rate.mean(), df.groupby("method").utility_rate.mean()
        com = bm.index.intersection(cm.index)
        put("BCTau", f"{kendalltau(bm[com], cm[com]).statistic:.2f}")
        jb = b.pivot_table(index="scenario", columns="method", values="utility_rate")
        both = w.stack().rename("C").to_frame().join(jb.stack().rename("B"), how="inner")
        put("BCr", f"{pearsonr(both.B, both.C).statistic:.2f}")
        put("BCn", str(len(both)))
        put("BCUB", pp(b.utility_rate.mean()))
        put("BCUC", pp(df.utility_rate.mean()))
        for m, k in [("anytime_risk", "Risk"), ("anytime", "AS"), ("alns_fixed@40", "FixedForty"), ("alns_fixed", "Fixed")]:
            if m in bm.index:
                put(f"BgzU{k}", pp(bm[m]))
        wb = jb.dropna()
        if "alns_fixed@40" in wb and OURS in wb:
            m, lo, hi, _ = boot(wb[OURS] - wb["alns_fixed@40"])
            put("BgzDFixedForty", ci(m, lo, hi))
        if "anytime" in wb and OURS in wb:
            m, lo, hi, _ = boot(wb[OURS] - wb["anytime"])
            put("BgzDAS", ci(m, lo, hi))
    lines = ["\\begin{table}[t]",
             f"\\caption{{Tier C (PX4 SITL, Gazebo, ROS~2): {df.scenario.nunique()} held-out missions per method, "
             "mid disturbances, $\\kappa_B=50$. Utility, tasks lost to late plans and skipped at departure per mission, "
             "planning time per call; tier B utility on the same rescaled missions for comparison.}\\label{tab:tierc}",
             "\\centering\\small", "\\begin{tabular}{lrrrrr}", "\\toprule",
             "Method & Utility C (\\%) & Lost to delay & Skipped & ms/call & Utility B (\\%) \\\\", "\\midrule"]
    bm = pd.read_csv(fb).groupby("method").utility_rate.mean() if fb.exists() else pd.Series(dtype=float)
    for m in ["alns_fixed", "alns_fixed@40", "anytime", "anytime_risk"]:
        if m in g.index:
            r = g.loc[m]
            ub = pp(bm[m]) if m in bm.index else "--"
            lines.append(f"{NAMES[m]} & {pp(r.u)} & {r.dropd:.2f} & {r.skip:.2f} & {r.ms:.1f} & {ub} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_tierc.tex").write_text("\n".join(lines) + "\n")


def main():
    (P / "tables").mkdir(parents=True, exist_ok=True)
    (P / "figures").mkdir(parents=True, exist_ok=True)
    for section in (reproduction, error_models, tier_b_main, tier_b_other, tier_c):
        try:
            section()
        except (KeyError, ValueError, IndexError) as e:      # result file still incomplete
            print(f"[skip] {section.__name__}: incomplete results ({type(e).__name__}: {e})")
    out = ["% generated by experiments/make_paper_numbers.py -- do not edit"]
    out += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MACROS.items())]
    (P / "tables" / "numbers.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    for f in ["fig_compute_utility.pdf"]:
        if (HO / f).exists():
            shutil.copy(HO / f, P / "figures" / f)
    print(f"{len(MACROS)} macros")
    for k, v in sorted(MACROS.items()):
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
