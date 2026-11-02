#!/usr/bin/env python3
"""Exploratory sensitivity analysis (not pre-registered): what if a late arrival has a cost of its own?

The utility of the studies counts only the reward of tasks served on time; a late service earns nothing and costs
nothing. Here every late service is charged lambda times the mean task reward of the mission, which gives
    u_lambda = utility_rate - lambda * late_served / n_tasks.
lambda = 1 means that a late arrival costs as much as an on-time service earns. The script re-scores the existing
held-out runs of studies 3, 4 and 4C (no new runs), and reports the paired difference at several lambda and the
break-even lambda* at which a comparison changes sign (ratio of the mean utility difference to the mean difference
in late services per task).

    python experiments/paper_latepen.py  ->  paper_journal/tables/numbers_latepen.tex, paper_journal/figures/fig_latepen.pdf,
                                             results/study4/report_latepen.md
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import CFG, boot, ci, paired  # noqa: E402
from analyze_study4c import C, FB, NOFB, NOM, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TB = ROOT / "results" / "tier_b"
P = ROOT / "paper_journal"
LAMBDAS = [0.0, 0.25, 0.5, 1.0, 2.0]
T = "+periodic:60"
S3 = {"FB": "proposed~fb=nominal" + T, "Prop": "proposed" + T, "Buf": "alns_fixed@40~buf=60" + T,
      "Forty": "alns_fixed@40" + T}
S4 = {"CC": "alns_fixed@40~z=auto4;fb=nominal" + T, "PropBuf": "alns_fixed@40~prop=auto;fb=nominal" + T,
      "MP": "alns_fixed@40~mp=auto;fb=nominal" + T, "MPnf": "alns_fixed@40~mp=auto" + T,
      "Buf": "alns_fixed@40~buf=60" + T, "Forty": "alns_fixed@40" + T, "Conv": "alns_fixed@40+event"}
# (macro name, study, data key, method a, method b, label)
COMP = [("SThreeFbProp", "3", "FB", "Prop", "fallback vs. no fallback (study 3)"),
        ("SFourCCForty", "4", "CC", "Forty", "proposed vs. nominal model"),
        ("SFourCCBuf", "4", "CC", "Buf", "proposed vs. constant buffer"),
        ("SFourCCConv", "4", "CC", "Conv", "proposed vs. conventional"),
        ("SFourMPMPnf", "4", "MP", "MPnf", "fallback within moment propagation"),
        ("SFourCCPropBuf", "4", "CC", "PropBuf", "proposed vs. proportional buffer"),
        ("CFbNoFb", "C", FB, NOFB, "fallback vs. no fallback (tier C)"),
        ("CFbNom", "C", FB, NOM, "proposed vs. nominal model (tier C)")]
MAC, REPORT = {}, []


def put(k, v):
    MAC["P" + k] = v


def tex(x, d=2):
    return f"{x:+.{d}f}".replace("-", "$-$")


def load_b(csv, names):
    df = pd.read_csv(TB / csv)
    inv = {v: k for k, v in names.items()}
    df = df[df.method.isin(inv)].copy()
    df["method"] = df.method.map(inv)
    df["latefrac"] = df.late_served / df.n_tasks
    return df


def diff_b(df, a, b, lam):
    d = df.assign(u_l=df.utility_rate - lam * df.latefrac)
    return paired(d, a, b, "u_l", CFG)


def diff_c(df, a, b, lam):
    d = df.assign(u_l=df.u - lam * df.late / df.n_tasks)
    w = d.pivot_table(index="scenario", columns="method", values="u_l").dropna(subset=[a, b])
    return w[a] - w[b]


def main():
    data = {"3": load_b("s3_heldout_B.csv", S3), "4": load_b("s4_heldout_B.csv", S4)}
    c = load(C)
    import json
    n_tasks = {f"{j['scenario']}|{j['method']}": j["n_tasks"]
               for j in (json.loads(f.read_text()) for f in sorted(C.glob("gz-*.json")))}
    c["n_tasks"] = [n_tasks[f"{s}|{m}"] for s, m in zip(c.scenario, c.method)]
    REPORT.append("# Late-arrival cost: exploratory sensitivity of the held-out comparisons\n")
    REPORT.append("u_lambda = utility - lambda * late/n_tasks; differences in pp with 95% paired bootstrap CI\n")
    REPORT.append("| comparison | " + " | ".join(f"lambda {l:g}" for l in LAMBDAS) + " | lambda* |")
    REPORT.append("|---" * (len(LAMBDAS) + 2) + "|")
    curves = {}
    for name, st, a, b, lab in COMP:
        fn = (lambda l: diff_c(c, a, b, l)) if st == "C" else (lambda l, st=st: diff_b(data[st], a, b, l))
        cells, curve = [], []
        for lam in LAMBDAS:
            m, lo, hi, p = boot(fn(lam))
            cells.append(f"{ci(m, lo, hi)}")
            curve.append((lam, m, lo, hi))
            key = {0.5: "Half", 1.0: "One", 2.0: "Two"}.get(lam)
            if key:
                put(f"{name}{key}", ci(m, lo, hi))
                put(f"{name}{key}Abs", f"{abs(m) * 100:.2f}")
                put(f"{name}{key}P", "$<$0.001" if p < 0.001 else f"{p:.3f}")
        du = fn(0.0).mean()
        dl = fn(0.0).mean() - fn(1.0).mean()        # mean difference in late services per task
        lam_star = du / dl if dl > 1e-12 else float("inf")
        put(f"{name}Star", "none" if not np.isfinite(lam_star) or lam_star < 0 else f"{lam_star:.1f}")
        put(f"{name}DLate", tex(dl * 100))
        cells.append("none" if not np.isfinite(lam_star) or lam_star < 0 else f"{lam_star:.2f}")
        REPORT.append(f"| {lab} | " + " | ".join(cells) + " |")
        curves[name] = (lab, curve)
    # how much the fallback raises late services, relative to the variant without it
    for name, st, a, b in [("SThree", "3", "FB", "Prop"), ("SFour", "4", "MP", "MPnf")]:
        g = data[st].groupby("method").late_served.mean()
        put(f"{name}LateFb", f"{g[a]:.2f}")
        put(f"{name}LateNoFb", f"{g[b]:.2f}")
    fig, ax = plt.subplots(figsize=(3.45, 2.6))
    style = {"SThreeFbProp": ("#C62828", "o", "fallback vs. none (study 3)"),
             "SFourMPMPnf": ("#E57373", "^", "fallback in moment prop. (study 4)"),
             "SFourCCForty": ("#1F6FC5", "s", "proposed vs. nominal (study 4)"),
             "SFourCCBuf": ("#178A5E", "D", "proposed vs. 60 s buffer (study 4)")}
    for k, (col, mk, lab) in style.items():
        _, cv = curves[k]
        x = np.array([v[0] for v in cv])
        ax.plot(x, [v[1] * 100 for v in cv], marker=mk, ms=4, color=col, lw=1.4, label=lab)
        ax.fill_between(x, [v[2] * 100 for v in cv], [v[3] * 100 for v in cv], color=col, alpha=0.12, lw=0)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel(r"cost of a late arrival $\lambda$ (mean task rewards)")
    ax.set_ylabel("utility difference (pp)")
    ax.set_xticks(LAMBDAS)
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=6.0, loc="lower left", handlelength=1.4, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_latepen.pdf")
    plt.close(fig)
    lines = ["% generated by experiments/paper_latepen.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_latepen.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "results" / "study4" / "report_latepen.md").write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    print("\n".join(REPORT))


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                         "font.family": "serif", "mathtext.fontset": "stix",
                         "font.serif": ["STIXGeneral", "DejaVu Serif"]})
    main()
