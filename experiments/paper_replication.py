#!/usr/bin/env python3
"""Replication across the three sets of held-out tier B seeds (studies 2, 3 and 4): paired difference of the proposed
replanner to the constant buffer, ALNS with 40 ms on the nominal model, and the conventional planner, with 95%
bootstrap intervals. Reads only the generated numbers_s2/s3/s4.tex, so it repeats no analysis.

    python experiments/paper_replication.py   ->  paper_journal/figures/fig_replication.pdf
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "paper_journal" / "tables"
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 7.5, "font.family": "serif", "mathtext.fontset": "stix",
                     "font.serif": ["STIXGeneral", "DejaVu Serif"]})

# (macro of study 2, 3, 4) per comparison; study 2 is the replanner without fallback
ROWS = [("vs. constant\n60 s buffer", ("KDBuf", "LDBufAll", "QDBufAll")),
        ("vs. nominal\nmodel", ("KDForty", "LDFortyAll", "QDFortyAll")),
        ("vs. conventional\nplanner", ("KDConv", "LDConvAll", "QDCCConv"))]
STUDIES = [("study 2, seeds 5000–5029 (no fallback)", "#9E9E9E", "s"),
           ("study 3, seeds 7000–7029", "#1F6FC5", "o"),
           ("study 4, seeds 8000–8029", "#C62828", "D")]


def macros() -> dict:
    out = {}
    for f in ("numbers_s2.tex", "numbers_s3.tex", "numbers_s4.tex"):
        out.update(re.findall(r"\\csname v(\w+)\\endcsname\{([^}]*)\}", (TAB / f).read_text(encoding="utf-8")))
    return out


def parse(v: str):
    m = re.fullmatch(r"(\S+) \[(.+), (.+)\]", v.replace("$-$", "-"))
    return tuple(float(x) for x in m.groups())


def main():
    q = macros()
    fig, ax = plt.subplots(figsize=(3.45, 2.5))
    y, ticks = 0.0, []
    for label, keys in ROWS:
        ticks.append((y - 1.0, label))
        for k, (name, col, mk) in zip(keys, STUDIES):
            m, lo, hi = parse(q[k])
            ax.errorbar(m, y, xerr=[[m - lo], [hi - m]], fmt=mk, color=col, ms=4.5, capsize=2.5, lw=1.2,
                        label=name if label == ROWS[0][0] else None)
            y -= 1.0
        y -= 1.0
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks([t for t, _ in ticks])
    ax.set_yticklabels([lab for _, lab in ticks])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("proposed minus method (pp)")
    ax.set_xlim(left=-0.5)
    ax.grid(axis="x", alpha=0.3)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.22), ncol=1, handletextpad=0.4)
    fig.tight_layout()
    fig.savefig(ROOT / "paper_journal" / "figures" / "fig_replication.pdf", bbox_inches="tight")
    plt.close(fig)
    print("ok")


if __name__ == "__main__":
    main()
