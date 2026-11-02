"""Figure of study 7 for the manuscript (presentation only; the frozen analysis is experiments/analyze_study7.py).

(a) 7a: cost-aware fallback with the fixed-cost and with the proportional rule minus the proportional buffer tuned for
    the same score and late cost, for both scores and lam in {0.5, 1, 2}.
(b) 7b: the two primary comparisons per condition (control and four shifted conditions): proposed model with the
    nominal fallback minus the nominal model on U (H27), cost-aware fallback minus nominal fallback on u_1 (H28).

    python experiments/paper_s7fig.py  ->  paper_journal/figures/fig_s7.pdf
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import analyze_study7 as a7  # noqa: E402
from analyze_study4 import paired, sup  # noqa: E402

plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9, "xtick.labelsize": 8,
                     "ytick.labelsize": 8, "legend.fontsize": 7.5, "font.family": "serif", "mathtext.fontset": "stix",
                     "font.serif": ["STIXGeneral", "DejaVu Serif"], "text.color": "black", "axes.labelcolor": "black"})
RED, BLUE = "#C62828", "#1F6FC5"


def main():
    s7 = pd.read_csv(a7.TB / "s7a_heldout_B.csv")
    b = pd.concat([pd.read_csv(a7.TB / f) for f in ("s7b_heldout_B.csv", "s7b_lat_heldout_B.csv")], ignore_index=True)
    fig, ax = plt.subplots(1, 2, figsize=(7.16, 2.9), gridspec_kw={"width_ratios": [1.05, 1]})

    a = ax[0]
    ticks, labels, y = [], [], 0.0
    for kind, sname in (("fee", "$u_\\lambda$"), ("w", "$u^w_\\lambda$")):
        for lam in (0.5, 1.0, 2.0):
            x = a7.score(s7, lam, kind)
            x = pd.concat([x, a7.tuned(x, kind, lam, "Prop")], ignore_index=True)
            for k, (rule, c) in enumerate((("fee", RED), ("prop", BLUE))):
                m, lo, hi, _ = sup(paired(x, a7.ca(lam, rule), f"Prop@{kind}{lam:g}", "u"))
                a.errorbar(m * 100, y + 0.32 * k, xerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt="o", ms=3.5,
                           color=c, capsize=2, lw=1)
            ticks.append(y + 0.16)
            labels.append(f"{sname}, $\\lambda={lam:g}$")
            y += 1.0
        y += 0.5
    a.axvline(0, color="black", lw=0.8)
    a.set_yticks(ticks)
    a.set_yticklabels(labels)
    a.invert_yaxis()
    a.set_xlabel("cost-aware fallback minus tuned buffer (pp)")
    a.errorbar([], [], xerr=[], fmt="o", ms=3.5, color=RED, label="fixed-cost rule")
    a.errorbar([], [], xerr=[], fmt="o", ms=3.5, color=BLUE, label="proportional rule")
    a.legend(loc="lower right", frameon=False)
    a.set_title("(a) study 7a: late-cost model")
    a.grid(axis="x", alpha=0.25, lw=0.5)

    c = ax[1]
    conds = [a7.CONTROL] + a7.SHIFTS
    for k, (lab, a_, b_, metric, col) in enumerate(
            (("$H_{27}$: nominal fallback $-$ nominal model, $U$", a7.M7B["CCfb"], a7.M7B["Forty"], "U", BLUE),
             ("$H_{28}$: cost-aware $-$ nominal fallback, $u_1$", a7.M7B["CA"], a7.M7B["CCfb"], "u1", RED))):
        xs, ms, los, his = [], [], [], []
        for j, (xl, ll, key, _) in enumerate(conds):
            sub = b[(b.exec_level == xl) & (b.latency_level == ll)]
            x = a7.score(sub, 1.0, "fee") if metric == "u1" else sub.assign(u=sub.utility_rate)
            m, lo, hi, _ = sup(paired(x, a_, b_, "u"))
            xs.append(j + (k - 0.5) * 0.22)
            ms.append(m * 100)
            los.append((m - lo) * 100)
            his.append((hi - m) * 100)
        c.errorbar(xs, ms, yerr=[los, his], fmt="o", ms=3.5, color=col, capsize=2, lw=1, label=lab)
    c.axhline(0, color="black", lw=0.8)
    c.axvspan(-0.5, 0.5, color="0.92", zorder=0)
    c.set_xlim(-0.5, len(conds) - 0.5)
    c.set_ylim(0, 8.6)
    c.set_xticks(range(len(conds)))
    c.set_xticklabels(["Gaussian\n(control)", "Student-$t$", "rare long\ndelays", "bias\nper UAV", "Pareto\nlatency"])
    c.set_ylabel("difference (pp)")
    c.legend(loc="upper center", frameon=False, ncol=1, bbox_to_anchor=(0.5, 1.0))
    c.set_title("(b) study 7b: errors outside the model")
    c.grid(axis="y", alpha=0.25, lw=0.5)
    fig.tight_layout()
    fig.savefig(a7.P / "figures" / "fig_s7.pdf")
    regimes(s7)


def regimes(s7):
    """Fixed-cost rule minus the buffer tuned for u_1, per regime (lam = 1). The frozen analysis drops these
    descriptive numbers because its tuned() needs both disturbance levels in one frame (protocol V7, deviation 3)."""
    x = a7.score(s7, 1.0, "fee")
    x = pd.concat([x, a7.tuned(x, "fee", 1.0, "Prop")], ignore_index=True)
    mac = {}
    for xl, wf, tag in (("mid", 1.0, "MidWOne"), ("mid", 0.5, "MidWHalf"), ("high", 1.0, "HighWOne"),
                        ("high", 0.5, "HighWHalf")):
        sub = x[(x.exec_level == xl) & (x.window == wf)]
        m, lo, hi, _ = sup(paired(sub, a7.ca(1.0, "fee"), "Prop@fee1", "u"))
        mac[f"UXRFee{tag}"] = f"{m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]".replace("-", "$-$")
    with open(a7.P / "tables" / "numbers_s7x.tex", "w", encoding="utf-8") as fh:
        fh.write("% generated by experiments/paper_s7fig.py -- do not edit\n")
        for k, v in sorted(mac.items()):
            fh.write(f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}\n")
    print(mac)


if __name__ == "__main__":
    main()
