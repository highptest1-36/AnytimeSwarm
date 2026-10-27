"""Step 12 - final, uncluttered paper figures drawn from the result CSV files (no experiment is re-run).

    python experiments/12_paper_figures.py
Reads results_test2/ (confirmatory test set) and results_xl/ (40 UAVs) and writes to paper/figures/:
    fig_summary.pdf     equal-computation regret and closed-loop utility at kappa = 50
    fig_frontier.pdf    quality-compute frontiers (medium, large, all fleets after delay)
    fig_allocation.pdf  computation per snapshot vs available improvement
    fig_kappa_curve.pdf closed-loop utility and dropped tasks over the latency factor
    fig_xl.pdf          40-UAV fleet: frontier and closed-loop utility
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm import plotting as PL  # noqa: E402

plt = PL.plt
T2, XL, OUT = ROOT / "results_test2", ROOT / "results_xl", ROOT / "paper" / "figures"
BLUE, ORANGE, GREEN, GREY, RED = PL.PALETTE[0], PL.PALETTE[1], PL.PALETTE[2], "#5c5a55", PL.PALETTE[7]
BAR = "#c4c1b9"
MU = 1e-5


def style():
    PL.setup()
    plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "legend.fontsize": 6.8,
                         "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "axes.titlepad": 4,
                         "axes.grid": True, "grid.linewidth": 0.4})


def save(fig, name):
    PL.save(fig, OUT / name)
    for ext in (".png",):  # keep the PNG preview next to the results, not in the paper folder
        p = (OUT / name).with_suffix(ext)
        if p.exists():
            p.unlink()


# ------------------------------------------------------------------ frontier helpers
FAM = [("fixed", "ALNS, fixed budget", ORANGE, "s", "-"), ("stagnation", "ALNS, stagnation stop", GREEN, "^", "-"),
       ("oracle_stop", "Oracle stop (hindsight)", GREY, None, ":"), ("anytime", "AnytimeSwarm (proposed)", BLUE, "o", "-")]


def frontier_panel(ax, g, ycol, title):
    for fam, lab, col, mk, ls in FAM:
        d = g[(g.family == fam) & (g.t_ms >= 0.8)].sort_values("t_ms")
        prop = fam == "anytime"
        ax.plot(d.t_ms, d[ycol], color=col, ls=ls, lw=1.8 if prop else 1.0, marker=mk, ms=3.2 if prop else 2.4,
                mec="white" if prop else col, mew=0.4, label=lab, zorder=5 if prop else 2)
        if prop:
            s = d[np.isclose(d.param, MU)]
            ax.plot(s.t_ms, s[ycol], marker="*", ms=9, color=BLUE, mec="black", mew=0.5, ls="none", zorder=6)
    for fam, col, mk, lab in (("fixed_ps", ORANGE, "s", "ALNS, fixed budget per scale"),
                              ("stagnation_ps", GREEN, "^", "ALNS, stagnation per scale")):
        d = g[g.family == fam]
        if len(d):
            ax.plot(d.t_ms, d[ycol], marker=mk, ms=5.5, mfc="white", mec=col, mew=1.1, ls="none", label=lab, zorder=4)
    ax.set_xscale("log")
    ax.set_xlim(1, 600)
    ax.set_xticks([1, 10, 100])
    ax.set_xticklabels(["1", "10", "100"])
    ax.set_xlabel("mean computation (ms)")
    ax.set_title(title)
    ax.set_ylim(bottom=0)


def fig_frontier():
    fr = pd.read_csv(T2 / "offline" / "frontier_test.csv")
    fig, axes = plt.subplots(1, 3, figsize=(PL.LNCS_WIDTH_IN, 2.0))
    frontier_panel(axes[0], fr[(fr.scale == "medium") & (fr.kappa == 1)], "regret_pct", "(a) medium fleet, $\\kappa$=1")
    frontier_panel(axes[1], fr[(fr.scale == "large") & (fr.kappa == 1)], "regret_pct", "(b) large fleet, $\\kappa$=1")
    frontier_panel(axes[2], fr[(fr.scale == "all") & (fr.kappa == 50)], "eff_regret", "(c) all fleets, $\\kappa$=50")
    axes[0].set_ylim(0, 0.3)
    axes[1].set_ylim(0, 0.9)
    axes[2].set_ylim(0, 0.8)
    axes[0].set_ylabel("regret (%)")
    h, lab = axes[1].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02), columnspacing=1.2,
               handlelength=1.8)
    fig.tight_layout(rect=(0, 0, 1, 0.83), w_pad=0.8)
    save(fig, "fig_frontier")


def fig_xl():
    fr = pd.read_csv(XL / "offline" / "frontier_test.csv")
    cl = pd.read_csv(XL / "closed_loop" / "closed_loop_test.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 2.0), gridspec_kw={"width_ratios": [1, 1.05]})
    frontier_panel(a1, fr[(fr.scale == "all") & (fr.kappa == 1)], "regret_pct", "(a) regret vs. computation, $\\kappa$=1")
    a1.set_xlim(5, 600)
    a1.set_xticks([10, 100])
    a1.set_xticklabels(["10", "100"])
    a1.set_ylim(0, 1.0)
    a1.set_ylabel("regret (%)")
    order = [("alns_fixed", "Fixed 250 ms"), ("alns_fixed@180", "Fixed 180 ms"), ("alns_fixed@ps", "Fixed per scale"),
             ("alns_stagnation", "Stagnation"), ("alns_stagnation@ps", "Stagnation per scale"),
             ("anytime_nodelay", "w/o delay cost"), ("anytime", "AnytimeSwarm (proposed)")]
    u = cl[cl.kappa == cl.kappa.max()].groupby("method").utility_rate.mean() * 100
    bars(a2, [lab for m, lab in order if m in u.index], [u[m] for m, _ in order if m in u.index],
         [m == "anytime" for m, _ in order if m in u.index], "%.1f")
    a2.set_xlim(np.floor(u.min()) - 0.5, u.max() + 0.7)
    a2.set_xlabel("mission utility (%)")
    a2.set_title("(b) closed loop, $\\kappa$=50")
    h, lab = a1.get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02), columnspacing=1.2,
               handlelength=1.8)
    fig.tight_layout(rect=(0, 0, 1, 0.83), w_pad=1.0)
    save(fig, "fig_xl")


# ------------------------------------------------------------------ bar helper
def bars(ax, labels, vals, prop, fmt):
    y = np.arange(len(labels))
    ax.barh(y, vals, height=0.6, color=[BLUE if p else BAR for p in prop])
    for yy, v, p in zip(y, vals, prop):
        ax.text(v, yy, " " + fmt % v, va="center", ha="left", fontsize=6.6, color=BLUE if p else PL.INK,
                fontweight="bold" if p else "normal")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    for t, p in zip(ax.get_yticklabels(), prop):
        if p:
            t.set_color(BLUE)


def fig_summary():
    eq = pd.read_csv(T2 / "offline" / "equal_compute_test.csv")
    sm = pd.read_csv(T2 / "closed_loop" / "summary_k50_test.csv")
    short = {"ALNS (fixed 50 ms)": "Fixed 50 ms", "ALNS (stagnation 50 ms)": "Stagnation 50 ms",
             "ALNS (fixed B per scale)": "Fixed per scale", "ALNS (stagnation per scale)": "Stagnation per scale",
             "ALNS (fixed 250 ms)": "Fixed 250 ms", "ALNS (fixed 40 ms)": "Fixed 40 ms",
             "ALNS (stagnation stop)": "Stagnation", "w/o delay cost": "w/o delay cost",
             "AnytimeSwarm (proposed)": "AnytimeSwarm (proposed)"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 1.85))
    bars(a1, [short[x] for x in eq.label], eq.regret, eq.proposed, "%.3f")
    a1.set_xlim(0, eq.regret.max() * 1.32)
    a1.set_xlabel("regret (%), lower is better")
    a1.set_title("(a) equal computation, $\\kappa$=1")
    bars(a2, [short.get(x, x) for x in sm.label], sm.u, sm.proposed, "%.1f")
    a2.set_xlim(np.floor(sm.u.min()) - 0.5, sm.u.max() + 0.9)
    a2.set_xlabel("mission utility (%), higher is better")
    a2.set_title("(b) closed loop, $\\kappa$=50")
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig_summary")


def fig_allocation():
    al = pd.read_csv(T2 / "offline" / "allocation_test.csv").set_index("family")
    share = al.n_none.iloc[0] / (al.n_none.iloc[0] + al.n_pos.iloc[0]) * 100
    groups = [f"no gain\n({share:.0f}% of snapshots)", "low", "medium", "high"]
    cols = ["t_none", "t_low", "t_mid", "t_high"]
    series = [("fixed_ps", "ALNS, fixed budget per scale", "#f2a27e"),
              ("stagnation_ps", "ALNS, stagnation per scale", "#7fd3b4"), ("anytime", "AnytimeSwarm (proposed)", BLUE)]
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.62, 1.8))
    x = np.arange(len(groups))
    w = 0.26
    for i, (fam, lab, col) in enumerate(series):
        v = al.loc[fam, cols].values
        ax.bar(x + (i - 1) * w, v, w * 0.92, color=col, label=lab)
        if fam == "anytime":
            for xx, vv in zip(x + (i - 1) * w, v):
                ax.text(xx, vv + 2, f"{vv:.0f}", ha="center", va="bottom", fontsize=6.2, color=BLUE)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel("mean computation (ms)")
    ax.set_xlabel("improvement that a 500 ms search can still find")
    top = al[cols].values.max()
    ax.set_ylim(0, top * 1.32)
    ax.grid(axis="x", visible=False)
    # reading aid: little time is wanted where nothing can be gained, much time where the search still pays off
    ax.annotate("less is better", xy=(x[0], top * 0.3), ha="center", fontsize=6.2, color=GREY)
    ax.annotate("more is better", xy=(x[-1] - 0.05, top * 1.2), ha="center", fontsize=6.2, color=GREY)
    ax.legend(loc="upper left", frameon=False, fontsize=6.3, bbox_to_anchor=(0.0, 1.0))
    fig.tight_layout()
    save(fig, "fig_allocation")


def fig_kappa_curve():
    kc = pd.read_csv(T2 / "closed_loop" / "kappa_curve_test.csv")
    cl = pd.read_csv(T2 / "closed_loop" / "closed_loop_test.csv")
    lines = [("alns_fixed@ps", "ALNS, fixed budget per scale", ORANGE, "--"),
             ("alns_stagnation@ps", "ALNS, stagnation per scale", GREEN, "--"),
             ("anytime_nodelay", "w/o delay cost", RED, ":"), ("anytime", "AnytimeSwarm (proposed)", BLUE, "-")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 1.85))
    ks = sorted(kc.kappa.unique())
    a1.axhline(0, color=GREY, lw=1.0)  # the full-budget ALNS is the reference (zero line)
    for m, lab, col, ls in lines:
        d = kc[kc.method == m].sort_values("kappa")
        prop = m == "anytime"
        if prop:
            a1.fill_between(d.kappa, d.ci_lo, d.ci_hi, color=BLUE, alpha=0.14, lw=0)
        a1.plot(d.kappa, d["diff"], color=col, ls=ls, lw=1.8 if prop else 1.1, marker="o" if prop else None, ms=3,
                mec="white", mew=0.4, label=lab, zorder=5 if prop else 2)
        if prop:  # asterisk where the 95% interval against the full-budget search lies above zero
            for kk, hi, lo in zip(d.kappa, d.ci_hi, d.ci_lo):
                if lo > 0:
                    a1.text(kk, hi + 0.08, "*", ha="center", va="bottom", fontsize=9, color=BLUE)
    a1.set_ylabel("utility gain over full budget\n(percentage points)")
    a1.set_title("(a) mission utility")
    drop = cl.groupby(["method", "kappa"]).dropped_by_delay.mean()
    for m, lab, col, ls in [("alns_fixed", "ALNS, full 250 ms budget", GREY, "-")] + lines:
        d = drop.loc[m].reindex(ks)
        prop = m == "anytime"
        a2.plot(ks, d.values, color=col, ls=ls, lw=1.8 if prop else 1.1, marker="o" if prop else None, ms=3,
                mec="white", mew=0.4, label=lab if m == "alns_fixed" else None, zorder=5 if prop else 2)
    a2.set_ylabel("tasks lost to late plans\nper mission")
    a2.set_title("(b) tasks lost because of delay")
    for ax in (a1, a2):
        ax.set_xscale("log")
        ax.set_xticks(ks)
        ax.set_xticklabels([f"{k:g}" for k in ks])
        ax.minorticks_off()
        ax.set_xlabel("latency factor $\\kappa$")
    h1, l1 = a1.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    fig.legend(h2 + h1, l2 + l1, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02),
               columnspacing=1.2, handlelength=2.0)
    fig.tight_layout(rect=(0, 0, 1, 0.83), w_pad=1.0)
    save(fig, "fig_kappa_curve")


def main():
    style()
    fig_summary()
    fig_frontier()
    fig_allocation()
    fig_kappa_curve()
    fig_xl()
    print("[ok] paper figures ->", OUT)


if __name__ == "__main__":
    main()
