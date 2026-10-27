"""Paper-ready matplotlib style (Springer LNCS text width 12.2 cm = 4.8 in).
Colour follows the METHOD (fixed per method, never by rank); markers give a colour-free channel."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LNCS_WIDTH_IN = 4.8
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

METHOD_STYLE = {
    "anytime":          {"color": PALETTE[0], "marker": "o", "label": "AnytimeSwarm (proposed)", "z": 10},
    "alns_fixed":       {"color": PALETTE[1], "marker": "s", "label": "ALNS (fixed B)"},
    "alns_stagnation":  {"color": PALETTE[2], "marker": "^", "label": "ALNS (stagnation stop)"},
    "ls_fixed":         {"color": PALETTE[3], "marker": "v", "label": "LS (fixed B)"},
    "regret_repair":    {"color": PALETTE[4], "marker": "D", "label": "Regret-2 repair"},
    "greedy_repair":    {"color": PALETTE[6], "marker": "x", "label": "Greedy repair"},
    "oracle_stop":      {"color": INK2, "marker": "*", "label": "Oracle stop", "ls": ":"},
    "anytime_online":   {"color": PALETTE[5], "marker": "P", "label": "w/o learned predictor"},
    "anytime_nodelay":  {"color": PALETTE[7], "marker": "X", "label": "w/o delay cost"},
    "anytime_noffr":    {"color": PALETTE[3], "marker": "h", "label": "w/o feasibility-first repair"},
}


def style(name: str) -> dict:
    if "@" in name:  # method spec of experiments/05 (own budget, per-scale parameters, other mu / patience)
        base, _, b = name.partition("@")
        st = dict(style(base))
        if b == "ps":
            lab = "ALNS (fixed B per scale)" if base == "alns_fixed" else "ALNS (stagnation per scale)"
            st.update(label=lab, ls=":", marker="s" if base == "alns_fixed" else "v")
        elif b.startswith("mu="):
            st.update(label=f"AnytimeSwarm ($\\mu$={b[3:]})", ls="--")
        elif b.startswith("pat="):
            st.update(label=f"ALNS (stagnation {b[4:]} ms)", ls="--")
        else:
            st.update(color=PALETTE[3] if base == "alns_fixed" else MUTED, marker="d", ls="--",
                      label=f"ALNS (fixed {float(b):g} ms)" if base == "alns_fixed" else f"{st['label']} ({b} ms)")
        return st
    return METHOD_STYLE.get(name, {"color": MUTED, "marker": "o", "label": name})


def setup():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "mathtext.fontset": "stix",
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.5, "lines.markersize": 4.5,
        "legend.frameon": False, "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def save(fig, out_base):
    out_base = Path(out_base)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"))
    plt.close(fig)
