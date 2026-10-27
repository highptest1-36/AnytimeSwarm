"""Step 11 - figure of the extra-large scalability experiment (40 UAVs / 280 tasks, seeds 2000-2029).
(a) quality-compute frontier at kappa = 1 on identical search trajectories (fixed budgets, stagnation stopping,
    AnytimeSwarm, oracle; open markers = per-scale baselines chosen on development seeds)
(b) closed-loop mission utility at the largest kappa for every closed-loop method.

    python experiments/11_scale_figure.py
Output: results_xl/figures/fig_xl.pdf (+ copy to paper/figures/)
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm import plotting as PL  # noqa: E402

RES = ROOT / "results_xl"
FAM = [("fixed", "alns_fixed", "ALNS (fixed B)"), ("stagnation", "alns_stagnation", "ALNS (stagnation stop)"),
       ("anytime", "anytime", "AnytimeSwarm (proposed)"), ("oracle_stop", "oracle_stop", "Oracle stop")]
CL_ORDER = ["alns_fixed", "alns_fixed@180", "alns_fixed@ps", "alns_stagnation", "alns_stagnation@ps", "anytime_nodelay",
            "anytime"]


def main():
    PL.setup()
    plt = PL.plt
    fr = pd.read_csv(RES / "offline" / "frontier_test.csv")
    g = fr[(fr.scale == "all") & (fr.kappa == 1)]
    mu = 1e-5
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(PL.LNCS_WIDTH_IN, 2.05), gridspec_kw={"width_ratios": [1.05, 1]})
    for fam, key, lab in FAM:
        d = g[(g.family == fam) & (g.t_ms > 0)].sort_values("t_ms")
        st = PL.style(key)
        a1.plot(d.t_ms, d.regret_pct, color=st["color"], ls=st.get("ls", "-"), marker=st["marker"], ms=2.5, lw=0.9,
                label=lab, zorder=st.get("z", 2))
        if fam == "anytime":
            s = d[np.isclose(d.param, mu)]
            a1.plot(s.t_ms, s.regret_pct, marker="*", ms=7, color=st["color"], markeredgecolor="black",
                    markeredgewidth=0.4, ls="none", zorder=5)
    for fam, key, lab in (("fixed_ps", "alns_fixed", "fixed B per scale"), ("stagnation_ps", "alns_stagnation",
                                                                           "stagnation per scale")):
        d = g[g.family == fam]
        if len(d):
            a1.plot(d.t_ms, d.regret_pct, marker="s" if fam == "fixed_ps" else "^", ms=5, mfc="white",
                    color=PL.style(key)["color"], ls="none", mew=1.0, label=lab, zorder=4)
    a1.set_xscale("log")
    a1.set_xlabel("mean computation (ms)", fontsize=6.5)
    a1.set_ylabel("regret to best known (%)", fontsize=6.5)
    a1.set_title(r"(a) static snapshots, $\kappa$=1", fontsize=7)
    a1.tick_params(labelsize=6)
    a1.legend(fontsize=5.3, loc="upper right", frameon=False)

    cl = pd.read_csv(RES / "closed_loop" / "closed_loop_test.csv")
    kmax = cl.kappa.max()
    u = cl[cl.kappa == kmax].groupby("method").utility_rate.mean() * 100
    ms = [m for m in CL_ORDER if m in u.index]
    labels = [("ALNS (fixed 250 ms)" if m == "alns_fixed" else PL.style(m)["label"]) for m in ms]
    cols = [PL.PALETTE[0] if m == "anytime" else "#bdbab3" for m in ms]
    y = np.arange(len(ms))
    a2.barh(y, u[ms].values, color=cols, height=0.62)
    for yi, v, m in zip(y, u[ms].values, ms):
        a2.text(v + 0.04, yi, f"{v:.1f}", va="center", fontsize=6, color=PL.PALETTE[0] if m == "anytime" else PL.INK)
    a2.set_yticks(y)
    a2.set_yticklabels(labels, fontsize=5.8)
    a2.invert_yaxis()
    lo = np.floor(u[ms].min() - 0.6)
    a2.set_xlim(lo, u[ms].max() + 0.6)
    a2.set_xlabel(rf"mission utility (%), closed loop, $\kappa$={kmax:g}", fontsize=6.5)
    a2.set_title("(b) closed-loop missions", fontsize=7)
    a2.tick_params(labelsize=6)
    a2.grid(axis="y", visible=False)
    fig.tight_layout()
    out = RES / "figures" / "fig_xl"
    PL.save(fig, out)
    shutil.copy(out.with_suffix(".pdf"), ROOT / "paper" / "figures" / "fig_xl.pdf")
    print("[ok] fig_xl", dict(u[ms].round(2)))


if __name__ == "__main__":
    main()
