"""Step 13 - comparison at equal computation for EACH fleet scale (offline, identical search trajectories).

For every scale, AnytimeSwarm (selected mu, kappa = 1) has a mean computation t*. Each baseline family (fixed
budget, stagnation stopping) is evaluated at the same mean computation t* of that scale: its regret is interpolated
on a log-time axis between the two settings whose scale-level mean computation brackets t*, separately for every
mission (scenario), and compared with AnytimeSwarm by a paired bootstrap over missions. The computation that each
family needs to reach the regret of AnytimeSwarm is read from the scale-level frontier. Also reports per-mission
win rates (static: AnytimeSwarm regret <= interpolated baseline; closed loop at the largest kappa: utility >=).

    python experiments/13_scale_equal_compute.py
Outputs: results_test2/offline/scale_equal_compute.csv, paper/tables/tab_scale.tex, paper/tables/numbers_scale.tex
No experiment is re-run; reads results_test2/ and results_xl/ only.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.analysis import paired_bootstrap  # noqa: E402

MU = 1e-5
SOURCES = [(ROOT / "results_test2", ["small", "medium", "large", "all"]), (ROOT / "results_xl", ["xlarge"])]
LABEL = {"small": "Small (5/25)", "medium": "Medium (10/50)", "large": "Large (20/140)", "xlarge": "40 UAVs (40/280)",
         "all": "Small to large"}


def scen_means(df):
    return df.groupby("scenario")[["t_ms", "regret_pct"]].mean()


def interp_family(d, fam, t_star):
    """Per-mission regret of `fam` at scale-level mean computation t_star (log-time interpolation)."""
    g = d[d.family == fam]
    mt = g.groupby("param").t_ms.mean().sort_values()
    if t_star <= mt.iloc[0]:
        p_lo = p_hi = mt.index[0]
        w = 0.0
    elif t_star >= mt.iloc[-1]:
        p_lo = p_hi = mt.index[-1]
        w = 0.0
    else:
        k = int(np.searchsorted(mt.values, t_star))
        p_lo, p_hi = mt.index[k - 1], mt.index[k]
        w = (np.log(t_star) - np.log(mt.iloc[k - 1])) / (np.log(mt.iloc[k]) - np.log(mt.iloc[k - 1]))
    lo = scen_means(g[np.isclose(g.param, p_lo)]).regret_pct
    hi = scen_means(g[np.isclose(g.param, p_hi)]).regret_pct
    return (1 - w) * lo + w * hi


def time_to_reach(d, fam, r_target):
    """Scale-level mean computation that `fam` needs to reach regret r_target (None if never)."""
    # same unit as regret_ours: mean over missions of the per-mission means
    g = (d[d.family == fam].groupby(["param", "scenario"])[["t_ms", "regret_pct"]].mean()
         .groupby("param").mean().sort_values("t_ms"))
    t, r = g.t_ms.values, g.regret_pct.values
    ok = np.nonzero(r <= r_target + 5e-4)[0]  # within 0.0005 percentage points (numerical floor of tiny regrets)
    if not len(ok):
        return None
    i = ok[0]
    if i == 0:
        return float(t[0])
    return float(np.exp(np.interp(r_target, [r[i], r[i - 1]], [np.log(t[i]), np.log(t[i - 1])])))


def main():
    rows = []
    for res, scales in SOURCES:
        pol = pd.read_csv(res / "offline" / "policies_test.csv")
        pol = pol[pol.kappa.isna() | np.isclose(pol.kappa.fillna(-1), 1)]
        for sc in scales:
            d = pol if sc == "all" else pol[pol.scale == sc]
            a = scen_means(d[(d.family == "anytime") & np.isclose(d.param, MU)])
            t_star = a.t_ms.mean()
            r = {"scale": sc, "t_ours": t_star, "regret_ours": a.regret_pct.mean(), "n": len(a)}
            for fam, key in (("fixed", "fixed"), ("stagnation", "stag")):
                b = interp_family(d, fam, t_star)
                j = pd.concat([a.regret_pct.rename("a"), b.rename("b")], axis=1).dropna()
                bs = paired_bootstrap(j.a, j.b)
                need = time_to_reach(d, fam, r["regret_ours"])
                r.update({f"{key}_regret": j.b.mean(), f"{key}_diff": bs["diff"], f"{key}_lo": bs["ci_lo"],
                          f"{key}_hi": bs["ci_hi"], f"{key}_win": bs["ci_hi"] < 0, f"{key}_need": need,
                          f"{key}_winrate": float((j.a <= j.b + 1e-9).mean())})
            rows.append(r)
    t = pd.DataFrame(rows)
    out = ROOT / "results_test2" / "offline" / "scale_equal_compute.csv"
    t.to_csv(out, index=False)
    pd.set_option("display.width", 220)
    print(t.round(4).to_string(index=False))

    # closed-loop win rate at the largest kappa (missions where AnytimeSwarm >= baseline)
    cl = pd.read_csv(ROOT / "results_test2" / "closed_loop" / "closed_loop_test.csv")
    k = cl.kappa.max()
    u = cl[cl.kappa == k].pivot_table(index="scenario", columns="method", values="utility_rate")
    wr = {m: float((u["anytime"] >= u[m] - 1e-12).mean() * 100) for m in u.columns if m != "anytime"}
    print("closed-loop win rate at kappa", k, {m: round(v) for m, v in wr.items()})

    # ---------------------------------------------------------------- table (rows = scales)
    def cell(v, win):
        return f"{v:.3f}" + ("$^{\\dagger}$" if win else "")

    def need(v, t0):
        return "--" if v is None or not np.isfinite(v) else f"{v:.0f} ({v / t0:.1f}$\\times$)"

    order = ["small", "medium", "large", "xlarge", "all"]
    lines = ["\\begin{table}[t]",
             "\\caption{Regret at equal computation per fleet scale (UAVs/tasks). Baselines run for the mean time of "
             "AnytimeSwarm on the same scale; $^{\\dagger}$: 95\\% interval of the paired difference below zero. "
             "Right: computation a baseline needs to match AnytimeSwarm.}",
             "\\label{tab:scale}", "\\centering", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lrrrrrr}",
             "\\toprule",
             " & & \\multicolumn{3}{c}{Regret at equal computation (\\%)} & \\multicolumn{2}{c}{Computation to match (ms)} \\\\",
             "\\cmidrule(lr){3-5}\\cmidrule(lr){6-7}",
             "Scale & Time (ms) & Proposed & Fixed & Stagnation & Fixed & Stagnation \\\\", "\\midrule"]
    for sc in order:
        r = t[t.scale == sc]
        if not len(r):
            continue
        r = r.iloc[0]
        if sc == "all":
            lines.append("\\midrule")
        lines.append(f"{LABEL[sc]} & {r.t_ours:.0f} & {r.regret_ours:.3f} & {cell(r.fixed_regret, r.fixed_win)} & "
                     f"{cell(r.stag_regret, r.stag_win)} & {need(r.fixed_need, r.t_ours)} & "
                     f"{need(r.stag_need, r.t_ours)} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (ROOT / "paper" / "tables" / "tab_scale.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- macros for the text
    vals = {}
    for sc, key in (("small", "Small"), ("medium", "Medium"), ("large", "Large"), ("xlarge", "Xlarge"), ("all", "All")):
        r = t[t.scale == sc]
        if not len(r):
            continue
        r = r.iloc[0]
        best = min(r.fixed_regret, r.stag_regret)
        worst = max(r.fixed_regret, r.stag_regret)
        vals[f"Sc{key}Ms"] = f"{r.t_ours:.0f}"
        vals[f"Sc{key}Ours"] = f"{r.regret_ours:.3f}"
        vals[f"Sc{key}RedMin"] = f"{(1 - r.regret_ours / best) * 100:.0f}"
        vals[f"Sc{key}RedMax"] = f"{(1 - r.regret_ours / worst) * 100:.0f}"
        vals[f"Sc{key}WinStatic"] = f"{min(r.fixed_winrate, r.stag_winrate) * 100:.0f}"
        sp = [x / r.t_ours for x in (r.fixed_need, r.stag_need) if x is not None and np.isfinite(x)]
        if sp:
            vals[f"Sc{key}SpeedMin"], vals[f"Sc{key}SpeedMax"] = f"{min(sp):.1f}", f"{max(sp):.1f}"
    vals["ClWinFixed"] = f"{wr.get('alns_fixed', np.nan):.0f}"
    vals["ClWinStag"] = f"{wr.get('alns_stagnation', np.nan):.0f}"
    vals["ClWinFixedPS"] = f"{wr.get('alns_fixed@ps', np.nan):.0f}"
    lines = ["% generated by experiments/13_scale_equal_compute.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in vals.items()]
    (ROOT / "paper" / "tables" / "numbers_scale.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(vals)
    print(f"[ok] -> {out}, paper/tables/tab_scale.tex, paper/tables/numbers_scale.tex")


if __name__ == "__main__":
    main()
