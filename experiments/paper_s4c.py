#!/usr/bin/env python3
"""Study 4C for the paper: tier B prediction against tier C on the same held-out missions (seeds 9000-9011), and the
derived numbers the text needs beyond analyze_study4c.py (per-mission spread, the development estimate that sized the
study, the missions a confirmation would need). Repeats no primary test; reads the flights and the two tier B
counterparts.

    python experiments/paper_s4c.py            ->  paper_journal/figures/fig_s4c.pdf, paper_journal/tables/numbers_s4cx.tex
    python experiments/paper_s4c.py --out DIR  ->  writes into DIR instead (dry run on partial data)
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import ci  # noqa: E402
from analyze_study4c import B_OF, BGZ, FB, NOFB, NOM, C, boot, load, paired  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "results" / "tier_b" / "dev4c_gz.csv"
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 7.5, "font.family": "serif", "mathtext.fontset": "stix",
                     "font.serif": ["STIXGeneral", "DejaVu Serif"]})
TESTS = [("Nom", NOM, "vs. nominal\nmodel (H14)"), ("NoFb", NOFB, "vs. no\nfallback (H15)")]


def tier_b(csv: Path, window=0.5):
    b = pd.read_csv(csv)
    b = b[b.window == window]
    b = b.assign(method=b.method.map({v: k for k, v in B_OF.items()})).dropna(subset=["method"])
    return b.pivot_table(index="scenario", columns="method", values="utility_rate")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    fig_dir = a.out or ROOT / "paper_journal" / "figures"
    tab_dir = a.out or ROOT / "paper_journal" / "tables"
    df = load(C)
    complete = df.groupby("scenario").method.nunique()
    df = df[df.scenario.isin(complete[complete == 3].index)]
    # tier C names its scenarios with the window suffix, tier B without; analyze_study4c.py (frozen) merged on the
    # raw names, so its per-run correlation came out empty and is computed here instead (protocol section 9)
    df = df.assign(scenario=df.scenario.str.replace(r"-w0\.5$", "", regex=True))
    wb = tier_b(BGZ).loc[sorted(df.scenario.unique())]
    dev = tier_b(DEV)
    mac = {}
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for i, (k, s, lab) in enumerate(TESTS):
        dc, db, dd = paired(df, FB, s), wb[FB] - wb[s], dev[FB] - dev[s]
        for dx, d, col, mk, name in [(-0.2, dd, "#9E9E9E", "D", "tier B, dev. seeds"),
                                     (0.0, db, "#1F6FC5", "s", "tier B, same missions"),
                                     (0.2, dc, "#C62828", "o", "tier C (PX4 + Gazebo)")]:
            m, lo, hi, _ = boot(d)
            ax.errorbar(i + dx, m * 100, yerr=[[(m - lo) * 100], [(hi - m) * 100]], fmt=mk, ms=5, capsize=2.5,
                        color=col, label=name if i == 0 else None)
        mac[f"Sd{k}"] = f"{100 * dc.std(ddof=1):.1f}"
        mac[f"BSd{k}"] = f"{100 * db.std(ddof=1):.1f}"
        mac[f"Dev{k}"] = ci(*boot(dd)[:3])
        mac[f"DevN{k}"] = str(len(dd))
        mac[f"BMean{k}"] = f"{100 * db.mean():+.2f}".replace("-", "$-$")
        # missions per method for 80% power at the observed tier C spread and the development effect
        mac[f"NPower{k}"] = str(int(np.ceil(((1.96 + 0.84) * dc.std(ddof=1) / dd.mean()) ** 2)))
        if k == "Nom":
            # the same at the effect of the full tier B grid of study 4 in this regime (numbers_s4.tex)
            grid = (ROOT / "paper_journal" / "tables" / "numbers_s4.tex").read_text(encoding="utf-8")
            eff = float(grid.split(r"\csname vQDFortyHighWHalf\endcsname{")[1].split(" ")[0])
            mac["NPowerNomGrid"] = str(int(np.ceil(((1.96 + 0.84) * 100 * dc.std(ddof=1) / eff) ** 2)))
        mac[f"Win{k}"] = str(int((dc > 0).sum()))
        mac[f"Loss{k}"] = str(int((dc < 0).sum()))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(TESTS)), [t[2] for t in TESTS])
    ax.set_xlim(-0.5, len(TESTS) - 0.5)
    ax.set_ylabel("with fallback minus method (pp)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, handletextpad=0.3,
              columnspacing=0.8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_s4c.pdf")
    plt.close(fig)
    skip = df.groupby("method").skip.mean()
    if NOFB in skip and not np.isnan(skip[NOFB]):
        mac["SkipNoFb"] = f"{skip[NOFB]:.2f}"
    mac["NB"] = str(len(wb))
    u = df.groupby("method").u.mean()
    mac["URelNoFb"] = f"{100 * (u[FB] / u[NOFB] - 1):.0f}"
    mac["Repeats"] = str(len(list((C / "invalid_rtf").glob("gz-*.json")))) if (C / "invalid_rtf").exists() else "0"
    runs = df.pivot_table(index="scenario", columns="method", values="u").stack().rename("c").to_frame()
    runs["b"] = wb.stack().reindex(runs.index)
    runs = runs.dropna()
    mac["BCr"] = f"{np.corrcoef(runs.c, runs.b)[0, 1]:.2f}"
    mac["BCn"] = str(len(runs))
    lines = ["% generated by experiments/paper_s4c.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname vH{k}\\endcsname{{{v}}}" for k, v in sorted(mac.items())]
    (tab_dir / "numbers_s4cx.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(f"{k}: {v}" for k, v in sorted(mac.items())))


if __name__ == "__main__":
    main()
