"""Figures of study 8 (presentation only; the statistics come from the frozen experiments/analyze_study8.py and
analyze_study8c.py, docs/18_PROTOCOL_V8.md section 7). Same paired bootstrap as the analyses.

    python experiments/paper_s8fig.py          # figures/fig_s8.pdf (8a, 8b) and figures/fig_s8c.pdf (8c)
    python experiments/paper_s8fig.py --dev    # development files -> results/study8/fig_s8_dev.pdf
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import analyze_study8 as a8  # noqa: E402
import analyze_study8c as a8c  # noqa: E402
from analyze_study4 import paired, sup  # noqa: E402

plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 7.5, "font.family": "serif", "mathtext.fontset": "stix",
                     "font.serif": ["STIXGeneral", "DejaVu Serif"], "text.color": "black", "axes.labelcolor": "black"})
SHORT = {"CAfee": "proposed (fixed late cost)", "CAprop": "closed form, prop. cost", "MPCA": "moment propagation",
         "Prop": "tuned buffer", "Nom": "nominal model"}
RED, GREY = "#C62828", "0.35"


def budget_axis(ax, budgets):
    ax.set_xscale("log")
    ax.set_xticks(budgets)
    ax.set_xticklabels([str(B) for B in budgets])
    ax.minorticks_off()
    ax.set_xlabel("ALNS budget $B$ (ms)")
    ax.grid(alpha=0.25, lw=0.5)


def fig_s8(dfa, dfb, conf, path):
    dfa = a8.scores(dfa)
    budgets = sorted(int(b) for b in dfa.method.str.extract(r"alns_fixed@(\d+)")[0].unique())
    fig, ax = plt.subplots(1, 3, figsize=(7.16, 3.05), gridspec_kw={"width_ratios": [1, 1, 1.2]})
    a = ax[0]
    g = dfa.groupby("method").u1.mean()
    for k in a8.OPT_A:
        xs = [B for B in budgets if a8.spec_a(k, B) in g.index]
        a.plot(xs, [g[a8.spec_a(k, B)] * 100 for B in xs], "o-", ms=3, lw=1.1, color=a8.COL[k])
    budget_axis(a, budgets)
    a.set_ylabel("score $u_1$ (%)")
    a.set_title("(a) 8a: score vs budget")

    b = ax[1]
    lows = []
    for k, (lab, x, y) in enumerate((("closed form $-$ moment prop.", "CAprop", "MPCA"),
                                      ("proposed $-$ tuned buffer", "CAfee", "Prop"))):
        xs, ms, lo_, hi_ = [], [], [], []
        for B in budgets:
            m, lo, hi, _ = sup(paired(dfa, a8.spec_a(x, B), a8.spec_a(y, B), "u1"))
            xs.append(B * (1 + (k - 0.5) * 0.14))
            ms.append(m * 100)
            lo_.append((m - lo) * 100)
            hi_.append((hi - m) * 100)
            lows.append(lo * 100)
        b.errorbar(xs, ms, yerr=[lo_, hi_], fmt="o" if k == 0 else "s", ms=3.2, color=a8.COL[y], capsize=2, lw=1,
                   label=lab)
    b.axhline(0, color="black", lw=0.8)
    budget_axis(b, budgets)
    y0, y1 = b.get_ylim()
    b.set_ylim(y0 - 0.45 * (y1 - y0), y1)
    b.set_ylabel("difference in $u_1$ (pp)")
    b.set_title("(b) 8a: paired differences")
    b.legend(loc="lower center", frameon=False, handletextpad=0.3)

    c = ax[2]
    names = [("CAfeeForty", "proposed $-$ nominal, $u_1$"), ("CAfeeCCfb", "cost-aware $-$ nominal fb, $u_1$"),
             ("CAfeeProp", "proposed $-$ tuned buffer, $u_1$"), ("CCfbForty", "nominal fb $-$ nominal, $U$")]
    contrasts = {"CAfeeForty": ("CAfee", "Forty", "u1"), "CAfeeCCfb": ("CAfee", "CCfb", "u1"),
                 "CAfeeProp": ("CAfee", "Prop", "u1"), "CCfbForty": ("CCfb", "Forty", "U")}
    new = a8.with_tuned(dfb)
    for j, (key, _lab) in enumerate(names):
        p, q, metric = contrasts[key]
        for x, off, col, mk in ((new, -0.17, RED, "o"), (conf, 0.17, GREY, "s")):
            if x is None or a8.M8B[p] not in set(x.method) or a8.M8B[q] not in set(x.method):
                continue
            m, lo, hi, _ = sup(paired(x, a8.M8B[p], a8.M8B[q], metric))
            c.errorbar(m * 100, j + off, xerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt=mk, ms=3.2, color=col,
                       capsize=2, lw=1)
    c.axvline(0, color="black", lw=0.8)
    c.set_yticks(range(len(names)))
    c.set_yticklabels([n[1] for n in names])
    c.invert_yaxis()
    c.set_xlabel("difference (pp)")
    c.set_title("(c) 8b: new scenario family")
    c.grid(axis="x", alpha=0.25, lw=0.5)

    handles = [Line2D([], [], color=a8.COL[k], marker="o", ms=3, lw=1.1, label=SHORT[k]) for k in a8.OPT_A]
    handles += [Line2D([], [], color=RED, marker="o", ms=3.2, lw=0, label="emergency family (8b)"),
                Line2D([], [], color=GREY, marker="s", ms=3.2, lw=0, label="conference family (7a)")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.0),
               columnspacing=1.2, handletextpad=0.4)
    fig.tight_layout(rect=(0, 0.13, 1, 1), w_pad=1.0)
    fig.savefig(path)
    plt.close(fig)


def fig_s8c(path):
    df = a8c.complete(a8c.load(a8c.C))
    bgz = pd.read_csv(a8c.BGZ)
    bgz = bgz.assign(scenario=bgz.scenario.map(a8c.mission), U=bgz.utility_rate, late=bgz.late_served,
                     u1=bgz.utility_rate - bgz.late_served / bgz.n_tasks)
    bgz = bgz[bgz.scenario.isin(set(df.scenario))]
    fig, ax = plt.subplots(1, 2, figsize=(7.16, 2.15))
    pairs = ((a8c.CA, a8c.FB), (a8c.CA, a8c.PR), (a8c.FB, a8c.PR))
    for a, col, unit, sc in ((ax[0], "late", "late arrivals per mission", 1), (ax[1], "u1", "score $u_1$ (pp)", 100)):
        for j, (x, y) in enumerate(pairs):
            m, lo, hi, _ = a8c.boot(a8c.paired(df, x, y, col))
            mb, lob, hib, _ = a8c.boot(a8c.paired(bgz, a8c.B_OF[x], a8c.B_OF[y], col))
            a.errorbar(m * sc, j - 0.16, xerr=[[(m - lo) * sc], [(hi - m) * sc]], fmt="o", ms=3.4, color=RED,
                       capsize=2, lw=1)
            a.errorbar(mb * sc, j + 0.16, xerr=[[(mb - lob) * sc], [(hib - mb) * sc]], fmt="s", ms=3.2, color=GREY,
                       capsize=2, lw=1)
        a.set_yticks(range(len(pairs)))
        a.set_yticklabels([f"{a8c.KEY[x]} $-$ {a8c.KEY[y]}" for x, y in pairs])
        a.invert_yaxis()
        a.axvline(0, color="black", lw=0.8)
        a.set_xlabel(f"difference, {unit}")
        a.grid(axis="x", alpha=0.25, lw=0.5)
    ax[0].set_title("(a) late arrivals")
    ax[1].set_title("(b) score $u_1$")
    handles = [Line2D([], [], color=RED, marker="o", ms=3.4, lw=0, label="tier C flights (PX4 SITL)"),
               Line2D([], [], color=GREY, marker="s", ms=3.2, lw=0, label="tier B, same missions")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    fa, fb = ("dev8a_check.csv", "dev8b_check.csv") if a.dev else ("s8a_heldout_B.csv", "s8b_heldout_B.csv")
    conf_f = a8.TB / "s7a_heldout_B.csv"
    conf = a8.with_tuned(pd.read_csv(conf_f)) if conf_f.exists() else None
    out = a8.OUT / "fig_s8_dev.pdf" if a.dev else a8.P / "figures" / "fig_s8.pdf"
    fig_s8(pd.read_csv(a8.TB / fa), pd.read_csv(a8.TB / fb), conf, out)
    if not a.dev and a8c.C.exists():
        fig_s8c(a8.P / "figures" / "fig_s8c.pdf")
    print("written", out)


if __name__ == "__main__":
    main()
