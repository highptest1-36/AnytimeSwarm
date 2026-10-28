#!/usr/bin/env python3
"""Pre-registered analysis of the held-out experiments (docs/05_PROTOCOL_JOURNAL.md).

    python experiments/analyze_heldout.py            # whatever result files exist are analysed

Inputs : results/tier_b/heldout_B_main.csv, heldout_B_xl.csv, heldout_B_sens.csv, heldout_B_misspec.csv,
         results/tier_c/heldout_C/*.json, results/tier_b/heldout_B_gz.csv (tier B counterpart of tier C)
Outputs: results/heldout/report.md, results/heldout/*.csv, results/heldout/fig_*.pdf
Statistics: paired bootstrap over missions (10 000 resamples, 95% percentile CI). Pooled tests average the per-mission
difference over the configurations of a matrix first (one value per mission). Holm correction for the H1 and H4
families.
"""
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "results" / "tier_b"
OUT = ROOT / "results" / "heldout"
OURS = "anytime_risk"
CFG_KEY = ["exec_level", "latency_level", "kappa", "trigger"]
NAMES = {"regret_repair": "Regret-2 repair", "alns_fixed": "ALNS 250 ms", "alns_fixed@40": "ALNS 40 ms",
         "alns_fixed@180": "ALNS 180 ms", "alns_stagnation": "ALNS stagnation", "anytime": "AnytimeSwarm",
         "anytime_nodelay": "AnytimeSwarm w/o delay cost", "anytime_risk": "AnytimeSwarm-R",
         "anytime_risk~zero": "AnytimeSwarm-R, zero error model", "anytime_risk~low": "AnytimeSwarm-R, low model",
         "anytime_risk~mid": "AnytimeSwarm-R, mid model", "anytime_risk~high": "AnytimeSwarm-R, high model"}


def boot(d, n=10_000, seed=0):
    d = np.asarray(d, float)
    idx = np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))
    m = d[idx].mean(axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    p = 2 * min(np.mean(m <= 0), np.mean(m >= 0))          # two-sided bootstrap p-value
    return float(d.mean()), float(lo), float(hi), float(min(p, 1.0))


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(run, 1.0)
    return adj


def pooled(df, ours, base, metric="utility_rate", by=None):
    """Per-mission mean (over configurations) of ours - base."""
    by = by or CFG_KEY
    w = df[df.method.isin([ours, base])].pivot_table(index=["scenario"] + by, columns="method", values=metric)
    w = w.dropna()
    return (w[ours] - w[base]).groupby(level="scenario").mean()


def fmt(m, lo, hi, scale=100.0, digits=2):
    return f"{m * scale:+.{digits}f} [{lo * scale:+.{digits}f}, {hi * scale:+.{digits}f}]"


def main_matrix(L):
    f = B / "heldout_B_main.csv"
    if not f.exists():
        return
    df = pd.read_csv(f)
    n_m, n_c = df.scenario.nunique(), df.groupby(CFG_KEY).ngroups
    L += ["## H1-H3: tier B primary matrix", "",
          f"{n_m} held-out missions x {n_c} configurations. Utility differences in percentage points (pp).", ""]
    means = df.groupby("method").agg(utility=("utility_rate", "mean"), plan_ms=("plan_ms_mean", "mean"),
                                     replans=("n_replans", "mean"), late=("late_served", "mean"))
    means.index = [NAMES.get(i, i) for i in means.index]
    L += ["Mean over all missions and configurations:", "", means.round(4).to_markdown(), ""]
    rows = []
    for base in ["alns_fixed@40", "anytime", "alns_stagnation"]:
        rows.append((base,) + boot(pooled(df, OURS, base)))
    adj = holm(np.array([r[4] for r in rows]))
    L += ["H1 (pooled, Holm-adjusted):", "", "| baseline | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"]
    for (base, m, lo, hi, p), pa in zip(rows, adj):
        L.append(f"| {NAMES[base]} | {fmt(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
    L.append("")
    other = []
    for base in ["alns_fixed", "anytime_nodelay", "regret_repair", "anytime_risk~zero"]:
        m, lo, hi, p = boot(pooled(df, OURS, base))
        other.append(f"| {NAMES[base]} | {fmt(m, lo, hi)} | {p:.4f} |")
    L += ["Secondary pooled comparisons (not part of the H1 family):", "", "| baseline | diff pp [95% CI] | p |",
          "|---|---|---|"] + other + [""]
    m, lo, hi, p = boot(pooled(df, OURS, "anytime", "plan_ms_mean"))
    L += [f"H2 (compute, AnytimeSwarm-R minus AnytimeSwarm, ms per planning call): {m:+.2f} [{lo:+.2f}, {hi:+.2f}].", ""]
    # per configuration
    per = []
    for k, g in df.groupby(CFG_KEY):
        w = g.pivot_table(index="scenario", columns="method", values="utility_rate")
        for base in ["alns_fixed@40", "anytime", "alns_stagnation", "alns_fixed"]:
            mm, lo, hi, _ = boot(w[OURS] - w[base])
            per.append(dict(zip(CFG_KEY, k)) | {"baseline": base, "diff": mm, "lo": lo, "hi": hi,
                                                 "sig": "+" if lo > 0 else ("-" if hi < 0 else "0")})
    per = pd.DataFrame(per)
    per.to_csv(OUT / "B_main_per_config.csv", index=False)
    cnt = per.groupby("baseline").sig.value_counts().unstack(fill_value=0)
    L += ["Per-configuration comparisons of AnytimeSwarm-R (count of significant +, 0, -):", "", cnt.to_markdown(), ""]
    # H3 triggers
    L += ["H3: periodic (60 s) minus event-only replanning, pooled per method:", "", "| method | diff pp [95% CI] |",
          "|---|---|"]
    for meth in sorted(df.method.unique()):
        sub = df[df.method == meth]
        w = sub.pivot_table(index=["scenario", "exec_level", "latency_level", "kappa"], columns="trigger",
                            values="utility_rate").dropna()
        d = (w["periodic:60"] - w["event"]).groupby(level="scenario").mean()
        m, lo, hi, _ = boot(d)
        L.append(f"| {NAMES.get(meth, meth)} | {fmt(m, lo, hi)} |")
    L.append("")
    for trig in sorted(df.trigger.unique()):
        sub = df[df.trigger == trig]
        m, lo, hi, _ = boot(pooled(sub, OURS, "alns_fixed@40"))
        m2, lo2, hi2, _ = boot(pooled(sub, OURS, "anytime"))
        L.append(f"- trigger {trig}: AnytimeSwarm-R vs ALNS 40 ms {fmt(m, lo, hi)}; vs AnytimeSwarm {fmt(m2, lo2, hi2)}")
    L.append("")
    tab = df.pivot_table(index=CFG_KEY, columns="method", values="utility_rate")
    tab.columns = [NAMES.get(c, c) for c in tab.columns]
    tab.to_csv(OUT / "B_main_means.csv")
    L += ["Mean utility per configuration:", "", tab.round(4).to_markdown(), ""]
    figures_main(df, per)


def figures_main(df, per):
    meths = ["regret_repair", "alns_fixed", "alns_fixed@40", "alns_stagnation", "anytime", "anytime_nodelay",
             "anytime_risk"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    g = df[df.method.isin(meths)].groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"))
    for mth, r in g.iterrows():
        ax.scatter(r.ms, r.u * 100, s=40, zorder=3, color="C3" if mth == OURS else "C0")
        ax.annotate(NAMES[mth], (r.ms, r.u * 100), textcoords="offset points", xytext=(5, -3), fontsize=7)
    ax.set_xscale("log")
    ax.set_xlabel("mean planning time per call (ms, log scale)")
    ax.set_ylabel("utility (%)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_compute_utility.pdf")
    plt.close(fig)
    sub = per[per.baseline == "alns_fixed@40"].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    y = np.arange(len(sub))
    ax.errorbar(sub["diff"] * 100, y, xerr=[(sub["diff"] - sub.lo) * 100, (sub.hi - sub["diff"]) * 100], fmt="o",
                ms=3, color="C3", capsize=2)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(y, [f"{r.exec_level}/{r.latency_level}/k{r.kappa:g}/{r.trigger}" for r in sub.itertuples()],
                  fontsize=6)
    ax.set_xlabel("AnytimeSwarm-R minus ALNS 40 ms (utility, pp)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_forest_alns40.pdf")
    plt.close(fig)


def simple_matrix(L, name, title, comparisons):
    f = B / f"{name}.csv"
    if not f.exists():
        return
    df = pd.read_csv(f)
    L += [f"## {title}", "", f"{df.scenario.nunique()} missions, {df.groupby(CFG_KEY).ngroups} configurations.", ""]
    tab = df.pivot_table(index=CFG_KEY, columns="method", values="utility_rate")
    tab.columns = [NAMES.get(c, c) for c in tab.columns]
    L += [tab.round(4).to_markdown(), ""]
    ms = df.pivot_table(index=CFG_KEY, columns="method", values="plan_ms_mean")
    ms.columns = [NAMES.get(c, c) for c in ms.columns]
    L += ["Planning time per call (ms):", "", ms.round(1).to_markdown(), ""]
    rows = []
    for ours, base in comparisons:
        if ours in df.method.values and base in df.method.values:
            m, lo, hi, p = boot(pooled(df, ours, base))
            rows.append((ours, base, m, lo, hi, p))
    if rows:
        adj = holm(np.array([r[5] for r in rows]))
        L += ["| comparison | pooled diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"]
        for (o, b, m, lo, hi, p), pa in zip(rows, adj):
            L.append(f"| {NAMES.get(o, o)} vs {NAMES.get(b, b)} | {fmt(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
        L.append("")
    for k, g in df.groupby(CFG_KEY):
        w = g.pivot_table(index="scenario", columns="method", values="utility_rate")
        parts = []
        for ours, base in comparisons:
            if ours in w and base in w:
                m, lo, hi, _ = boot(w[ours] - w[base])
                parts.append(f"{NAMES.get(base, base)} {fmt(m, lo, hi)}")
        L.append(f"- {'/'.join(str(x) for x in k)}: " + "; ".join(parts))
    L.append("")


def tier_c(L):
    d = ROOT / "results" / "tier_c" / "heldout_C"
    files = sorted(d.glob("gz-*.json")) if d.exists() else []
    if not files:
        return
    rows = []
    for f in files:
        m = json.loads(f.read_text())
        rows.append({k: v for k, v in m.items() if not k.startswith("_")} | {"scenario": m["scenario"]})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "C_main.csv", index=False)
    L += ["## H4: tier C (PX4 SITL + Gazebo)", "",
          f"{df.scenario.nunique()} held-out missions, {len(df)} runs. RTF mean {df.rtf.mean():.2f} "
          f"(min {df.rtf.min():.2f}); plan acceptance latency mean {np.nanmean(df.accept_latency_s_mean):.3f} s "
          f"(simulation time). Runs repeated because their RTF left [0.8F, 1.1F]: "
          f"{len(list((d / 'invalid_rtf').glob('gz-*.json')))} (originals in heldout_C/invalid_rtf/).", ""]
    g = df.groupby("method").agg(utility=("utility_rate", "mean"), served=("served", "mean"),
                                 late=("late_served", "mean"), plan_ms=("plan_ms_mean", "mean"),
                                 finish_err_p95=("finish_err_p95_s", "mean"), n=("scenario", "count"))
    g.index = [NAMES.get(i, i) for i in g.index]
    L += [g.round(4).to_markdown(), ""]
    w = df.pivot_table(index="scenario", columns="method", values="utility_rate").dropna()
    rows = []
    for base in ["alns_fixed@40", "anytime"]:
        if base in w and OURS in w:
            rows.append((base,) + boot(w[OURS] - w[base]))
    if rows:
        adj = holm(np.array([r[4] for r in rows]))
        L += ["| baseline | diff pp [95% CI] | p | p Holm |", "|---|---|---|---|"]
        for (b, m, lo, hi, p), pa in zip(rows, adj):
            L.append(f"| {NAMES[b]} | {fmt(m, lo, hi)} | {p:.4f} | {pa:.4f} |")
        L.append("")
    if "alns_fixed" in w and OURS in w:
        m, lo, hi, p = boot(w[OURS] - w["alns_fixed"])
        L += [f"Secondary: AnytimeSwarm-R vs ALNS 250 ms {fmt(m, lo, hi)} (p {p:.4f}).", ""]
    fb = B / "heldout_B_gz.csv"
    if fb.exists():
        bdf = pd.read_csv(fb)
        bm = bdf.groupby("method").utility_rate.mean()
        cm = df.groupby("method").utility_rate.mean()
        common = bm.index.intersection(cm.index)
        from scipy.stats import kendalltau, pearsonr
        tau = kendalltau(bm[common], cm[common]).statistic
        # pair each tier C run with the tier B run of the same mission and method (the earlier stack/join paired
        # every run with every run of the mission and reported r = 0.00 for n = 3600)
        both = df[["scenario", "method", "utility_rate"]].rename(columns={"utility_rate": "C"}).merge(
            bdf[["scenario", "method", "utility_rate"]].rename(columns={"utility_rate": "B"}), on=["scenario", "method"])
        r = pearsonr(both.B, both.C).statistic if len(both) > 2 else float("nan")
        L += [f"Tier B vs tier C on the same gz missions: Kendall tau of method means {tau:.2f}; Pearson r of "
              f"per-run utility {r:.2f} (n={len(both)}); mean utility B {bdf.utility_rate.mean():.4f} vs "
              f"C {df.utility_rate.mean():.4f}.", ""]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    L = ["# Held-out results (pre-registered analysis)", ""]
    main_matrix(L)
    simple_matrix(L, "heldout_B_xl", "H5: tier B scalability, 40 UAVs / 280 tasks",
                  [(OURS, "alns_fixed@180"), (OURS, "anytime"), (OURS, "alns_stagnation"), (OURS, "alns_fixed")])
    simple_matrix(L, "heldout_B_sens", "Sensitivity: high disturbance, kappa 1, deviation-triggered replanning",
                  [(OURS, "alns_fixed@40"), (OURS, "anytime"), (OURS, "alns_stagnation")])
    simple_matrix(L, "heldout_B_misspec", "Sensitivity: misspecified error model",
                  [(OURS, "anytime"), ("anytime_risk~zero", "anytime"), ("anytime_risk~low", "anytime"),
                   ("anytime_risk~mid", "anytime"), ("anytime_risk~high", "anytime")])
    tier_c(L)
    (OUT / "report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
