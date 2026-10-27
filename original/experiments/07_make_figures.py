"""Step 7 - every paper figure from results (re-run any time; never edit figures by hand).

    python experiments/07_make_figures.py --split test
    python experiments/07_make_figures.py --split dev --tag _quick

  fig_quality_time      regret (%) vs mean compute time, one curve per method over budgets   (H1/H2)
  fig_compute_used      fraction of the budget actually used                                  (H2)
  fig_kappa             net regret vs time dilation kappa at a fixed budget                   (H3)
  fig_anytime_profile   normalised anytime improvement curves (dev traces)                    (motivation)
  fig_predictor         predicted vs realised future gain (dev, out-of-fold)                  (controller)
  fig_stop_example      one run: predicted gain vs delay + compute cost, and the stop time     (intuition)
  fig_closed_loop       utility rate and dropped-by-delay per method and kappa                (H3)
  fig_ablation          ablations at fixed budget / kappa
PDFs are copied to paper/figures/.
"""
import argparse
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm import plotting as PL  # noqa: E402
from anytimeswarm.analysis import at_kappa, load_static  # noqa: E402
from anytimeswarm.utils import load_config, rpath  # noqa: E402

plt = PL.plt
MAIN = ["greedy_repair", "regret_repair", "ls_fixed", "alns_fixed", "alns_stagnation", "anytime", "oracle_stop"]
ABL = ["anytime", "anytime_online", "anytime_nodelay", "anytime_noffr", "alns_fixed"]


def _line(ax, d, x, y, m):
    st = PL.style(m)
    ax.plot(d[x], d[y], marker=st["marker"], color=st["color"], ls=st.get("ls", "-"), label=st["label"],
            zorder=st.get("z", 2), markeredgecolor="white", markeredgewidth=0.5)


def quality_time(df, cfg, out, k=1):
    dk = at_kappa(df, k)
    scales = list(cfg["scales"])
    fig, axes = plt.subplots(1, len(scales), figsize=(PL.LNCS_WIDTH_IN, 2.4), sharey=False)
    for ax, sc in zip(np.atleast_1d(axes), scales):
        g = dk[dk.scale == sc].groupby(["method", "budget_ms"])[["elapsed_ms", "regret_pct"]].mean().reset_index()
        for m in MAIN:
            d = g[g.method == m].sort_values("budget_ms")
            if len(d):
                _line(ax, d, "elapsed_ms", "regret_pct", m)
        ax.set_xscale("log")
        ax.set_title(sc)
        ax.set_xlabel("mean compute time (ms)")
    np.atleast_1d(axes)[0].set_ylabel("regret to best known (%)")
    h, lab = np.atleast_1d(axes)[-1].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=4, fontsize=6, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    PL.save(fig, out / "fig_quality_time")


def compute_used(df, out, k=1):
    dk = at_kappa(df, k)
    g = dk.groupby(["method", "budget_ms"]).compute_frac.mean().reset_index()
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.55, 1.9))
    for m in ["ls_fixed", "alns_fixed", "alns_stagnation", "anytime"]:
        d = g[g.method == m].sort_values("budget_ms")
        if len(d):
            _line(ax, d, "budget_ms", "compute_frac", m)
    ax.set_xscale("log")
    ax.set_ylim(0, 1.08)
    ax.set_xlabel("compute budget B (ms)")
    ax.set_ylabel("share of B used")
    ax.legend(fontsize=5.5)
    fig.tight_layout()
    PL.save(fig, out / "fig_compute_used")


def kappa_fig(df, cfg, out, B):
    rows = []
    for k in cfg["kappas"]:
        dk = at_kappa(df[df.budget_ms == B], k)
        for m, g in dk.groupby("method"):
            rows.append({"kappa": k, "method": m, "net": g[f"net_regret_k{k}"].mean()})
    r = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.55, 1.9))
    for m in ["regret_repair", "alns_fixed", "alns_stagnation", "anytime", "oracle_stop"]:
        d = r[r.method == m].sort_values("kappa")
        if len(d):
            _line(ax, d, "kappa", "net", m)
    ax.set_xscale("log")
    ax.set_xlabel(r"time dilation $\kappa$")
    ax.set_ylabel("net regret (%)")
    ax.set_title(f"B = {B:g} ms")
    ax.legend(fontsize=5.5)
    fig.tight_layout()
    PL.save(fig, out / "fig_kappa")


def anytime_profile(res, out):
    p = res / "traces" / "dev_traces.pkl"
    if not p.exists():
        return
    with open(p, "rb") as f:
        traces = pickle.load(f)
    grid = np.logspace(np.log10(0.3), np.log10(500), 160)  # log axis: most improvement arrives in the first ms
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.55, 1.9))
    for i, (sc, ls) in enumerate(zip(["small", "medium", "large"], ["-", "--", ":"])):
        curves = []
        for tr in traces:
            if tr["scale"] != sc:
                continue
            imp = tr["trace"]["imp"]
            Jf = imp[-1][2] if imp else tr["J0"]
            if Jf - tr["J0"] < 1e-9:
                continue
            ts = [x[0] for x in imp]
            Js = [x[2] for x in imp]
            idx = np.searchsorted(ts, grid, side="right") - 1
            v = np.where(idx >= 0, np.asarray(Js)[np.maximum(idx, 0)], tr["J0"])
            curves.append((v - tr["J0"]) / (Jf - tr["J0"]))
        if curves:
            c = np.asarray(curves)
            ax.plot(grid, np.median(c, 0), color=PL.PALETTE[i], ls=ls, label=f"{sc} (median, n={len(c)})")
            ax.fill_between(grid, np.percentile(c, 25, 0), np.percentile(c, 75, 0), color=PL.PALETTE[i], alpha=0.15, lw=0)
    ax.set_xscale("log")
    ax.set_xlabel("search time (ms)")
    ax.set_ylabel("share of final improvement")
    ax.legend(fontsize=6)
    fig.tight_layout()
    PL.save(fig, out / "fig_anytime_profile")


def predictor_fig(res, out):
    p = res / "predictor_deciles.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.45, 1.9))
    lim = max(d.pred.max(), d.true.max()) * 1.05
    ax.plot([0, lim], [0, lim], color=PL.MUTED, ls="--", lw=0.8)
    ax.plot(d.pred, d.true, marker="o", color=PL.PALETTE[0], label="learned (OOF)")
    ax.plot(d.online, d.true, marker="s", color=PL.PALETTE[5], label="online rate", ls=":")
    ax.set_xlabel("predicted gain next H (%)")
    ax.set_ylabel("realised gain (%)")
    ax.legend(fontsize=6)
    fig.tight_layout()
    PL.save(fig, out / "fig_predictor")


def stop_example(cfg, out, split):
    from anytimeswarm.algorithms.methods import solve
    from anytimeswarm.controller.improvement_model import LearnedPredictor

    pred_p = rpath(cfg["paths"]["models_dir"]) / "improvement_model.json"
    snap_p = rpath(cfg["paths"]["data_dir"]) / f"snapshots_{split}.pkl"
    if not (pred_p.exists() and snap_p.exists()):
        return
    with open(snap_p, "rb") as f:
        snaps = pickle.load(f)
    big = "large" if any(x["scale"] == "large" for x in snaps) else snaps[0]["scale"]
    s = next(x for x in snaps if x["scale"] == big)
    pred = LearnedPredictor.load(pred_p)
    k = max(cfg["kappas"])
    r = solve("anytime", s["P"], s["old"], 500, cfg, seed=0, predictor=pred, kappa=k)
    full = solve("alns_fixed", s["P"], s["old"], 500, cfg, seed=0)
    dec = np.asarray(r["decisions"] or [[0, 0, 0, 0]])
    imp = full["trace"]["imp"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(PL.LNCS_WIDTH_IN * 0.6, 2.8), sharex=True)
    if imp:
        a1.step([full["t_first_feasible_ms"]] + [x[0] for x in imp], [full["J_initial"]] + [x[2] for x in imp],
                where="post", color=PL.PALETTE[1], label="incumbent J (fixed 500 ms run)")
    a1.axvline(r["elapsed_ms"], color=PL.PALETTE[0], ls="--", lw=1, label="AnytimeSwarm stops")
    a1.set_ylabel("J")
    a1.legend(fontsize=5.5)
    a2.plot(dec[:, 0], dec[:, 1], color=PL.PALETTE[0], label="predicted gain")
    a2.plot(dec[:, 0], dec[:, 2] + dec[:, 3], color=PL.PALETTE[7], label="delay + compute cost")
    a2.set_xlabel("planning time (ms)")
    a2.set_ylabel("reward units")
    a2.set_title(rf"large snapshot, $\kappa$={k}", fontsize=7)
    a2.legend(fontsize=5.5)
    fig.tight_layout()
    PL.save(fig, out / "fig_stop_example")


def closed_loop_fig(cl, out):
    order = ["regret_repair", "alns_fixed"] + sorted(m for m in set(cl.method) if "@" in m) + ["alns_stagnation", "anytime_nodelay", "anytime"]
    methods = [m for m in order if m in set(cl.method)] + sorted(set(cl.method) - set(order))
    kappas = sorted(cl.kappa.unique())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 2.2))
    w = 0.8 / len(methods)
    means = []
    for i, m in enumerate(methods):
        g = cl[cl.method == m].groupby("kappa")
        x = np.arange(len(kappas)) + i * w
        label = PL.style(m)["label"]
        if m == "alns_fixed":  # name the closed-loop budget explicitly
            label = f"ALNS (fixed {cl[cl.method == m].budget_ms.iloc[0]:g} ms)"
        u = g.utility_rate.mean().reindex(kappas) * 100
        means.append(u)
        a1.bar(x, u, w * 0.92, color=PL.style(m)["color"], label=label)
        a2.bar(x, g.dropped_by_delay.mean().reindex(kappas), w * 0.92, color=PL.style(m)["color"])
    for a in (a1, a2):
        a.set_xticks(np.arange(len(kappas)) + w * (len(methods) - 1) / 2)
        a.set_xticklabels([rf"$\kappa$={k:g}" for k in kappas])
    lo, hi = min(float(u.min()) for u in means), max(float(u.max()) for u in means)
    a1.set_ylim(max(lo - 2, 0), min(hi + 1.5, 100))
    a1.set_ylabel("mission utility (%)")
    a2.set_ylabel("tasks dropped by delay")
    h, lab = a1.get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=3, fontsize=5.8, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    PL.save(fig, out / "fig_closed_loop")


def ablation_fig(df, out, B, k):
    dk = at_kappa(df[df.budget_ms == B], k)
    g = dk.groupby("method")[[f"net_regret_k{k}", "elapsed_ms"]].mean()
    ms = [m for m in ABL if m in g.index]
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.55, 1.9))
    ax.barh([PL.style(m)["label"] for m in ms], g.loc[ms, f"net_regret_k{k}"], color=[PL.style(m)["color"] for m in ms], height=0.6)
    ax.invert_yaxis()
    ax.set_xlabel(rf"net regret (%), B={B:g} ms, $\kappa$={k}")
    fig.tight_layout()
    PL.save(fig, out / "fig_ablation")


KCURVE = ["alns_fixed@40", "alns_fixed@ps", "alns_stagnation", "alns_stagnation@ps", "anytime_nodelay", "anytime"]
KLABEL = {"alns_fixed@40": "ALNS (fixed 40 ms)", "alns_fixed@ps": "ALNS (fixed B per scale)",
          "alns_stagnation": "ALNS (stagnation stop)", "alns_stagnation@ps": "ALNS (stagnation per scale)",
          "anytime_nodelay": "w/o delay cost", "anytime": "AnytimeSwarm (proposed)"}
KSTYLE = {"alns_fixed@40": (PL.PALETTE[3], "d", "--"), "alns_fixed@ps": (PL.PALETTE[1], "s", ":"),
          "alns_stagnation": (PL.PALETTE[2], "^", "-"), "alns_stagnation@ps": (PL.PALETTE[2], "v", ":"),
          "anytime_nodelay": (PL.PALETTE[7], "X", "--"), "anytime": (PL.PALETTE[0], "o", "-")}


def kappa_curve_fig(cl, out, seed=0):
    """Closed loop over the latency factor: utility minus that of the full-budget ALNS (mission-paired, 95% CI),
    and tasks dropped because the plan arrived too late."""
    from anytimeswarm.analysis import paired_bootstrap
    kappas = sorted(cl.kappa.unique())
    ref = cl[cl.method == "alns_fixed"].set_index(["kappa", "scenario"]).utility_rate
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 1.95))
    rows = []
    for m in [x for x in KCURVE if x in set(cl.method)]:
        col, mk, ls = KSTYLE[m]
        mean, lo, hi, drop = [], [], [], []
        for k in kappas:
            g = cl[(cl.method == m) & (cl.kappa == k)].set_index("scenario").utility_rate
            b = ref.xs(k, level="kappa").reindex(g.index)
            r = paired_bootstrap(g.values * 100, b.values * 100, seed=seed)
            mean.append(r["diff"]), lo.append(r["ci_lo"]), hi.append(r["ci_hi"])
            drop.append(cl[(cl.method == m) & (cl.kappa == k)].dropped_by_delay.mean())
            rows.append({"method": m, "kappa": k, **r})
        a1.plot(kappas, mean, color=col, marker=mk, ls=ls, ms=3, lw=1.1, label=KLABEL[m], zorder=3 if m == "anytime" else 2)
        if m == "anytime":
            a1.fill_between(kappas, lo, hi, color=col, alpha=0.15, lw=0)
        a2.plot(kappas, drop, color=col, marker=mk, ls=ls, ms=3, lw=1.1)
    d250 = [cl[(cl.method == "alns_fixed") & (cl.kappa == k)].dropped_by_delay.mean() for k in kappas]
    a2.plot(kappas, d250, color=PL.MUTED, marker="o", ls="-", ms=3, lw=1.1, label="ALNS (fixed 250 ms)")
    a1.axhline(0, color=PL.MUTED, lw=0.8, ls="-")
    for a in (a1, a2):
        a.set_xscale("log")
        a.set_xticks(kappas)
        a.set_xticklabels([f"{k:g}" for k in kappas])
        a.set_xlabel(r"latency factor $\kappa$")
    a1.set_ylabel("utility vs. ALNS 250 ms (points)")
    a2.set_ylabel("tasks dropped by delay")
    h1, l1 = a1.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, loc="lower center", ncol=4, fontsize=5.6, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    PL.save(fig, out / "fig_kappa_curve")
    return pd.DataFrame(rows)


def cl_frontier_fig(cl, out):
    """Closed-loop utility versus mean planning time per call, for kappa = 1 and the largest kappa."""
    fam = {"fixed": ["alns_fixed@20", "alns_fixed@40", "alns_fixed@100", "alns_fixed"],
           "stagnation": ["alns_stagnation@pat=10", "alns_stagnation@pat=25", "alns_stagnation"],
           "anytime": ["anytime@mu=3e-5", "anytime", "anytime@mu=3e-6"]}
    sty = {"fixed": (PL.PALETTE[1], "s", "ALNS (fixed B)"), "stagnation": (PL.PALETTE[2], "^", "ALNS (stagnation stop)"),
           "anytime": (PL.PALETTE[0], "o", "AnytimeSwarm (proposed)")}
    ks = [k for k in (1, max(cl.kappa)) if k in set(cl.kappa)]
    fig, axes = plt.subplots(1, len(ks), figsize=(PL.LNCS_WIDTH_IN, 1.8))
    for ax, k in zip(np.atleast_1d(axes), ks):
        g = cl[cl.kappa == k].groupby("method")[["plan_ms_mean", "utility_rate"]].mean()
        for f, ms in fam.items():
            ms = [m for m in ms if m in g.index]
            col, mk, lab = sty[f]
            d = g.loc[ms].sort_values("plan_ms_mean")
            ax.plot(d.plan_ms_mean, d.utility_rate * 100, color=col, marker=mk, ms=3.5, lw=1.1, label=lab)
        for m, (col, mk, lab) in {"alns_fixed@ps": (PL.PALETTE[1], "s", "fixed B per scale"),
                                  "alns_stagnation@ps": (PL.PALETTE[2], "^", "stagnation per scale")}.items():
            if m in g.index:
                ax.plot(g.loc[m, "plan_ms_mean"], g.loc[m, "utility_rate"] * 100, marker=mk, ms=5.5, color="white",
                        markeredgecolor=col, markeredgewidth=1.1, ls="none", label=lab)
        if "anytime" in g.index:
            ax.plot(g.loc["anytime", "plan_ms_mean"], g.loc["anytime", "utility_rate"] * 100, marker="*", ms=8,
                    color=PL.PALETTE[0], markeredgecolor="black", markeredgewidth=0.4, ls="none", zorder=5)
        ax.set_xscale("log")
        ax.set_xticks([10, 20, 50, 100, 200])
        ax.set_xticklabels(["10", "20", "50", "100", "200"])
        ax.xaxis.set_minor_formatter(PL.plt.NullFormatter())
        ax.set_title(rf"$\kappa$={k:g}", fontsize=7)
        ax.set_xlabel("mean planning time per call (ms)", fontsize=6.5)
        ax.set_ylabel("mission utility (%)", fontsize=6.5)
        ax.tick_params(labelsize=6)
    h, lab = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=5, fontsize=5.6, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    PL.save(fig, out / "fig_cl_frontier")


EQ = [("fixed", 50, "ALNS (fixed 50 ms)"), ("stagnation", 50, "ALNS (stagnation 50 ms)"),
      ("fixed_ps", 0, "ALNS (fixed B per scale)"), ("stagnation_ps", 0, "ALNS (stagnation per scale)"),
      ("anytime", None, "AnytimeSwarm (proposed)")]
CL_ORDER = [("alns_fixed", "ALNS (fixed 250 ms)"), ("alns_fixed@40", "ALNS (fixed 40 ms)"),
            ("alns_fixed@ps", "ALNS (fixed B per scale)"), ("alns_stagnation", "ALNS (stagnation stop)"),
            ("alns_stagnation@ps", "ALNS (stagnation per scale)"), ("anytime_nodelay", "w/o delay cost"),
            ("anytime", "AnytimeSwarm (proposed)")]


def _mean_ci(x, seed=0, n=2000):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    bs = x[rng.integers(0, len(x), size=(n, len(x)))].mean(1)
    return x.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def summary_fig_and_table(cfg, res, out, seed=0):
    """Headline comparison: (a) regret at equal mean computation (offline, identical trajectories),
    (b) closed-loop utility at the largest kappa. Also writes tables/tab_equal_compute.tex."""
    pp = res / "offline" / "policies_test.csv"
    cp = res / "closed_loop" / "closed_loop_test.csv"
    if not (pp.exists() and cp.exists()):
        return
    df = pd.read_csv(pp)
    mu, kx = cfg["controller"]["mu"], max(cfg["kappas"])
    rows = []
    for fam, p, lab in EQ:
        g = df[df.family == fam]
        if fam == "anytime":
            g1, gk = g[np.isclose(g.param, mu) & np.isclose(g.kappa, 1)], g[np.isclose(g.param, mu) & np.isclose(g.kappa, kx)]
        else:
            g1 = gk = g[np.isclose(g.param, p)]
        if not len(g1):
            continue
        sc = g1.groupby("scenario").regret_pct.mean()
        m, lo, hi = _mean_ci(sc.values, seed)
        # scenario means first (same unit as the paired bootstrap of experiments/10)
        rows.append({"label": lab, "t": g1.groupby("scenario").t_ms.mean().mean(), "regret": m, "lo": lo, "hi": hi,
                     "eff": gk.groupby("scenario")[f"eff_regret_k{kx}"].mean().mean(), "proposed": fam == "anytime"})
    eq = pd.DataFrame(rows)
    cl = pd.read_csv(cp)
    ck = cl[cl.kappa == kx]
    crow = []
    for m, lab in CL_ORDER:
        g = ck[ck.method == m]
        if len(g):
            mm, lo, hi = _mean_ci(g.utility_rate.values * 100, seed)
            crow.append({"label": lab, "u": mm, "lo": lo, "hi": hi, "proposed": m == "anytime"})
    clr = pd.DataFrame(crow)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 2.05))
    for ax, d, col, xl in ((a1, eq, "regret", r"regret at equal computation, $\kappa$=1 (%)"),
                           (a2, clr, "u", rf"mission utility, closed loop, $\kappa$={kx:g} (%)")):
        y = np.arange(len(d))[::-1]
        colors = [PL.PALETTE[0] if p else "#b9b7b0" for p in d.proposed]
        # means only: the comparisons are paired (same scenarios / missions); their intervals are in the text
        ax.barh(y, d[col], height=0.62, color=colors)
        ax.set_yticks(y)
        ax.set_yticklabels(d.label, fontsize=6)
        ax.set_xlabel(xl, fontsize=6.5)
        ax.tick_params(axis="x", labelsize=6)
        for yy, v, p in zip(y, d[col], d.proposed):
            ax.text(v, yy, f" {v:.3f}" if col == "regret" else f" {v:.1f}", va="center", ha="left", fontsize=5.8,
                    color=PL.PALETTE[0] if p else PL.INK)
        ax.grid(axis="y", visible=False)
    a1.set_xlim(0, eq.regret.max() * 1.3)
    a2.set_xlim(clr.u.min() - 1.5, clr.u.max() + 0.8)
    a1.set_title("(a) static snapshots", fontsize=7)
    a2.set_title("(b) closed-loop missions", fontsize=7)
    fig.tight_layout(w_pad=0.6)
    PL.save(fig, out / "fig_summary")
    lines = ["\\begin{table}[t]", "\\caption{Comparison at equal mean computation on identical search trajectories of "
             f"the confirmatory test snapshots. The two per-scale baselines were tuned on the development seeds. Regret is given in "
             f"\\% of the reward scale at $\\kappa=1$ and after the publication delay at $\\kappa={kx:g}$. The last column "
             f"gives the paired difference in regret at $\\kappa=1$ between AnytimeSwarm and each baseline, where negative "
             f"values favour AnytimeSwarm.}}",
             "\\label{tab:equal}", "\\centering", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lrrrc}", "\\toprule",
             " & & \\multicolumn{2}{c}{Regret (\\%)} & \\\\", "\\cmidrule(lr){3-4}",
             f"Method & Time (ms) & $\\kappa=1$ & $\\kappa={kx:g}$ & Difference (95\\% CI) \\\\", "\\midrule"]
    # paired difference (proposed - baseline, kappa = 1 regret) from experiments/10_offline_policies.py
    mp = res / "offline" / "matched_test.csv"
    dif = {}
    if mp.exists():
        mm = pd.read_csv(mp)
        mm = mm[(mm.kappa == 1) & (mm.metric == "regret_pct") & (mm.scale == "all")].set_index("baseline")
        fam_of = {lab: fam for fam, _, lab in EQ}
        for lab, fam in fam_of.items():
            if fam in mm.index:
                r_ = mm.loc[fam]
                dif[lab] = f"${r_['diff']:.3f}$ [${r_.ci_lo:.3f}$, ${r_.ci_hi:.3f}$]"
    for r in eq.itertuples():
        lines.append(f"{r.label} & {r.t:.1f} & {r.regret:.3f} & {r.eff:.3f} & {dif.get(r.label, '--')} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    tdir = res / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "tab_equal_compute.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pt = rpath(cfg["paths"]["paper_dir"]) / "tables"
    pt.mkdir(parents=True, exist_ok=True)
    shutil.copy(tdir / "tab_equal_compute.tex", pt / "tab_equal_compute.tex")
    eq.to_csv(res / "offline" / "equal_compute_test.csv", index=False)
    clr.to_csv(res / "closed_loop" / f"summary_k{kx:g}_test.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--tag", default="")
    ap.add_argument("--budget", type=float, default=250)
    args = ap.parse_args()
    cfg = load_config(args.config)
    PL.setup()
    res = rpath(cfg["paths"]["results_dir"])
    out = res / "figures"
    made = []
    if (res / "static" / f"static_{args.split}{args.tag}.csv").exists():
        df = load_static(cfg, args.split, args.tag)
        B = args.budget if args.budget in set(df.budget_ms) else sorted(df.budget_ms.unique())[-1]
        quality_time(df, cfg, out)
        compute_used(df, out)
        kappa_fig(df, cfg, out, B)
        ablation_fig(df, out, B, sorted(cfg["kappas"])[len(cfg["kappas"]) // 2])
        made += ["quality_time", "compute_used", "kappa", "ablation"]
    anytime_profile(res, out)
    predictor_fig(res, out)
    stop_example(cfg, out, args.split)
    cl_p = res / "closed_loop" / f"closed_loop_{args.split}{args.tag}.csv"
    if cl_p.exists():
        cl = pd.read_csv(cl_p)
        closed_loop_fig(cl[cl.kappa.isin([1, 10, 50])], out)
        made.append("closed_loop")
        if cl.kappa.nunique() > 3:
            kc = kappa_curve_fig(cl, out, seed=cfg["seed"])
            kc.to_csv(res / "closed_loop" / f"kappa_curve_{args.split}{args.tag}.csv", index=False)
            made.append("kappa_curve")
        if args.split == "test" and not args.tag:
            summary_fig_and_table(cfg, res, out, seed=cfg["seed"])
            made.append("summary")
        fp = res / "closed_loop" / f"closed_loop_{args.split}{args.tag}_frontier.csv"
        if fp.exists():
            cl_frontier_fig(pd.concat([cl, pd.read_csv(fp)], ignore_index=True), out)
            made.append("cl_frontier")
    pf = rpath(cfg["paths"]["paper_dir"]) / "figures"
    pf.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.pdf"):
        shutil.copy(f, pf / f.name)
    print(f"[ok] figures ({', '.join(made + ['profile/predictor/stop_example if data exist'])}) -> {out}")


if __name__ == "__main__":
    main()
