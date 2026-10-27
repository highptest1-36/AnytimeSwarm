"""Step 8 - LaTeX tables (booktabs) from results; \\input them in paper/main.tex.

    python experiments/08_make_tables.py --split test --budget 250

  tab_static.tex       per scale: regret, compute time, share of budget, net regret (kappa=1 and max)
  tab_closed_loop.tex  per kappa: utility, completion, dropped by delay, planning time
  tab_ablation.tex     ablations at the chosen budget
  tab_predictor.tex    predictor quality (dev, OOF)
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.analysis import at_kappa, load_static, paired_bootstrap  # noqa: E402
from anytimeswarm.plotting import style  # noqa: E402
from anytimeswarm.utils import load_config, rpath  # noqa: E402

MAIN = ["greedy_repair", "regret_repair", "ls_fixed", "alns_fixed", "alns_stagnation", "anytime", "oracle_stop"]
ABL = ["anytime", "anytime_online", "anytime_nodelay", "anytime_noffr"]


def write(lines, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def static_table(df, cfg, B, out):
    kmax = max(cfg["kappas"])
    d1, dk = at_kappa(df[df.budget_ms == B], 1), at_kappa(df[df.budget_ms == B], kmax)
    lines = ["\\begin{table}[t]",
             f"\\caption{{Static snapshots of the test seeds with a budget of {B:g}\\,ms. Regret (lower is better) is "
             f"given in \\% of the reward scale. The oracle stop is the best stopping time in hindsight.}}",
             "\\label{tab:static}", "\\centering", "\\setlength{\\tabcolsep}{3.5pt}"]
    scs = list(cfg["scales"])
    lines += ["\\begin{tabular}{l" + "r" * (len(scs) + 4) + "}", "\\toprule",
              f" & \\multicolumn{{{len(scs) + 1}}}{{c}}{{Regret, $\\kappa=1$ (\\%)}} & & & \\\\",
              f"\\cmidrule(lr){{2-{len(scs) + 2}}}",
              "Method & " + " & ".join(scs) + f" & all & Time (ms) & Used & Regret, $\\kappa={kmax}$ \\\\", "\\midrule"]
    for m in MAIN:  # one row per method; per-scale regret columns, pooled time / budget share / delayed regret
        a, b = d1[d1.method == m], dk[dk.method == m]
        if m in ("greedy_repair", "ls_fixed") or not len(a):
            continue
        per = " & ".join(f"{a[a.scale == sc].regret_pct.mean():.2f}" for sc in scs)
        lines.append(f"{style(m)['label']} & {per} & {a.regret_pct.mean():.2f} & {a.elapsed_ms.mean():.1f} & "
                     f"{a.compute_frac.mean() * 100:.0f}\\% & {b[f'eff_regret_k{kmax}'].mean():.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    rows = []
    for sc in cfg["scales"]:
        first = True
        for m in MAIN:
            if m in ("greedy_repair", "ls_fixed"):  # weaker constructive baselines: CSV only, text in the paper
                rows.append({"scale": sc, "method": m, "regret": d1[(d1.scale == sc) & (d1.method == m)].regret_pct.mean()})
                continue
            a, b = d1[(d1.scale == sc) & (d1.method == m)], dk[(dk.scale == sc) & (dk.method == m)]
            if not len(a):
                continue
            r = {"scale": sc, "method": m, "regret": a.regret_pct.mean(), "ms": a.elapsed_ms.mean(),
                 "used": a.compute_frac.mean() * 100, "net1": a.net_regret_k1.mean(),
                 "netk": b[f"net_regret_k{kmax}"].mean(), "effk": b[f"eff_regret_k{kmax}"].mean()}
            rows.append(r)
            first = False
    write(lines, out / "tab_static.tex")
    pd.DataFrame(rows).to_csv(out / "tab_static.csv", index=False)


def ablation_table(df, cfg, B, out):
    k = max(cfg["kappas"])
    Bs = min(df.budget_ms.unique())
    d1, ds, dk = (at_kappa(df[df.budget_ms == B], 1), at_kappa(df[df.budget_ms == Bs], 1),
                  at_kappa(df[df.budget_ms == B], k))
    lines = ["\\begin{table}[t]", f"\\caption{{Ablation of AnytimeSwarm on the test snapshots, averaged over all "
             f"scales. Regret is given in \\% of the reward scale for $B={Bs:g}$\\,ms and $B={B:g}$\\,ms at $\\kappa=1$, "
             f"and after the publication delay at $\\kappa={k}$ for $B={B:g}$\\,ms.}}", "\\label{tab:ablation}",
             "\\centering", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{lrrrr}", "\\toprule",
             f"Variant & Regret, {Bs:g}\\,ms & Regret, {B:g}\\,ms & Time (ms) & Regret, $\\kappa={k}$ \\\\", "\\midrule"]
    for m in ABL + ["alns_fixed"]:
        g1, gs, gk = d1[d1.method == m], ds[ds.method == m], dk[dk.method == m]
        if len(g1):
            lines.append(f"{style(m)['label']} & {gs.regret_pct.mean():.2f} & {g1.regret_pct.mean():.2f} & "
                         f"{g1.elapsed_ms.mean():.1f} & {gk[f'eff_regret_k{k}'].mean():.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write(lines, out / "tab_ablation.tex")


CL_ROWS = [("regret_repair", "Regret-2 repair"), ("alns_fixed", "ALNS (fixed 250 ms)"), ("alns_fixed@40", "ALNS (fixed 40 ms)"),
           ("alns_fixed@ps", "ALNS (fixed B per scale)"), ("alns_stagnation", "ALNS (stagnation stop)"),
           ("alns_stagnation@ps", "ALNS (stagnation per scale)"), ("anytime_nodelay", "w/o delay cost"),
           ("anytime", "AnytimeSwarm (proposed)")]


def closed_loop_table_wide(cl, out):
    """One row per method: utility at three latency factors, tasks dropped at the largest one, planning time."""
    ks = [k for k in (1, 10, max(cl.kappa)) if k in set(cl.kappa)]
    kx = max(cl.kappa)
    lines = ["\\begin{table}[t]", "\\caption{Closed-loop missions on the confirmatory seeds. Dropped: tasks per mission "
             f"lost to late plans at $\\kappa={kx:g}$. Last column: utility difference of AnytimeSwarm to each method at "
             f"$\\kappa={kx:g}$ with its 95\\% interval.}}",
             "\\label{tab:closedloop}", "\\centering", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{l" + "r" * (len(ks) + 1) + "c}", "\\toprule",
             " & \\multicolumn{" + str(len(ks)) + "}{c}{Utility (\\%)} & & \\\\",
             "\\cmidrule(lr){2-" + str(len(ks) + 1) + "}",
             "Method & " + " & ".join(f"$\\kappa={k:g}$" for k in ks) +
             f" & Dropped & Difference at $\\kappa={kx:g}$ \\\\", "\\midrule"]
    ck = cl[cl.kappa == kx]
    a = ck[ck.method == "anytime"].set_index("scenario").utility_rate * 100
    for m, lab in CL_ROWS:
        g = cl[cl.method == m]
        if not len(g):
            continue
        u = [g[g.kappa == k].utility_rate.mean() * 100 for k in ks]
        if m == "anytime":
            dcell = "--"
        else:
            b = ck[ck.method == m].set_index("scenario").utility_rate * 100
            j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
            r = paired_bootstrap(j.a, j.b)
            dcell = f"${r['diff']:+.2f}$ [${r['ci_lo']:.2f}$, ${r['ci_hi']:.2f}$]"
        lines.append(f"{lab} & " + " & ".join(f"{x:.1f}" for x in u) +
                     f" & {g[g.kappa == kx].dropped_by_delay.mean():.2f} & {dcell} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write(lines, out / "tab_closed_loop.tex")


def closed_loop_table(cl, out):
    if cl.kappa.nunique() > 3:
        return closed_loop_table_wide(cl, out)
    lines = ["\\begin{table}[t]", "\\caption{Closed-loop missions of the test seeds over all scales and event "
             "profiles. The columns give the served share of the total reward (utility), the completion rate, the "
             "number of tasks per mission dropped because the plan arrived too late, and the mean planning time per "
             "replanning call.}", "\\label{tab:closedloop}", "\\centering", "\\setlength{\\tabcolsep}{4pt}",
             "\\begin{tabular}{rlrrrr}", "\\toprule",
             "$\\kappa$ & Method & Utility (\\%) & Completion (\\%) & Dropped & Time (ms) \\\\", "\\midrule"]
    if cl.kappa.nunique() > 3:  # the kappa curve figure shows the other latency factors
        cl = cl[cl.kappa.isin([1, max(cl.kappa)])]
    for k, gk in cl.groupby("kappa"):
        for m, g in gk.groupby("method", sort=False):
            lab = f"ALNS (fixed {g.budget_ms.iloc[0]:g} ms)" if m == "alns_fixed" else style(m)["label"]
            lines.append(f"{k:g} & {lab} & {g.utility_rate.mean() * 100:.1f} & "
                         f"{g.completion_rate.mean() * 100:.1f} & {g.dropped_by_delay.mean():.2f} & {g.plan_ms_mean.mean():.1f} \\\\")
        lines.append("\\midrule")
    lines[-1] = "\\bottomrule"
    lines += ["\\end{tabular}", "\\end{table}"]
    write(lines, out / "tab_closed_loop.tex")


def predictor_table(path, out):
    ev = json.loads(path.read_text(encoding="utf-8"))
    lines = ["\\begin{table}[t]", "\\caption{Prediction of an improvement within the next $H$\\,ms of search on "
             "development checkpoints with scenario-grouped 5-fold cross-validation. AUC and average precision refer "
             "to the event of any improvement.}", "\\label{tab:predictor}", "\\centering",
             "\\begin{tabular}{lrrrr}", "\\toprule",
             "Predictor & AUC & Avg.\\ prec. & Spearman $\\rho$ & MAE (\\%) \\\\", "\\midrule"]
    for key, name in (("online", "Online improvement rate"), ("learned_oof", "Learned (Poisson GLM)")):
        e = ev[key]
        lines.append(f"{name} & {e.get('auc', float('nan')):.3f} & {e.get('avg_precision', float('nan')):.3f} & "
                     f"{e['spearman']:.3f} & {e['mae_pct']:.4f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    write(lines, out / "tab_predictor.tex")


def _pooled(df, ours, base, metric, unit="scenario", seed=0):
    """Paired bootstrap over units pooled across scales (mean per unit first)."""
    a = df[df.method == ours].groupby(unit)[metric].mean()
    b = df[df.method == base].groupby(unit)[metric].mean()
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    return paired_bootstrap(j.a, j.b, seed=seed)


def numbers_tex(cfg, split, tag, res, out, B, prefix=""):
    """tables/numbers.tex: one \\newcommand per number quoted in the text (no number is typed by hand).
    Development values are printed in orange so they cannot be mistaken for final results."""
    vals = {"mu": f"{cfg['controller']['mu']:.0e}".replace("e-0", "\\cdot 10^{-").replace("1\\cdot ", "") + "}"}
    matched = [m for m in cfg["methods"]["closed_loop"] if m.startswith("alns_fixed@") and m.split("@")[1].isdigit()]
    if matched:
        vals["MatchedB"] = matched[0].split("@")[1]
    for key, name in (("fixed_ms", "PSFixed"), ("stagnation_ms", "PSStag")):
        for sc, v in cfg.get("per_scale_baselines", {}).get(key, {}).items():
            vals[f"{name}{sc.capitalize()}"] = f"{v:g}"
    f2 = lambda x: f"{x:.2f}"  # noqa: E731
    f3 = lambda x: f"{x:.3f}"  # noqa: E731
    ci = lambda r, f=f2: f"[{f(r['ci_lo'])},\\,{f(r['ci_hi'])}]"  # noqa: E731
    sp = res / "static" / f"static_{split}{tag}.csv"
    if sp.exists():
        df = load_static(cfg, split, tag)
        vals["NsnapTest"] = str(df.snap.nunique())
        d = at_kappa(df[df.budget_ms == B], 1)
        g = d.groupby("method")[["regret_pct", "elapsed_ms", "compute_frac"]].mean()
        vals["B"] = f"{B:g}"
        for m, key in (("anytime", "AS"), ("alns_fixed", "Fixed"), ("alns_stagnation", "Stag"),
                       ("regret_repair", "Repair"), ("oracle_stop", "Oracle")):
            if m in g.index:
                vals[f"{key}Regret"] = f2(g.loc[m, "regret_pct"])
                vals[f"{key}Ms"] = f"{g.loc[m, 'elapsed_ms']:.1f}"
                vals[f"{key}Used"] = f"{g.loc[m, 'compute_frac'] * 100:.0f}"
        for base, key in (("alns_fixed", "Fixed"), ("alns_stagnation", "Stag")):
            r = _pooled(d, "anytime", base, "regret_pct", seed=cfg["seed"])
            vals[f"dRegret{key}"], vals[f"dRegret{key}CI"] = f3(r["diff"]), ci(r, f3)
            r = _pooled(d, "anytime", base, "elapsed_ms", seed=cfg["seed"])
            vals[f"dMs{key}"], vals[f"dMs{key}CI"] = f"{r['diff']:.1f}", ci(r, lambda x: f"{x:.1f}")
        if "alns_fixed" in g.index:
            vals["SavedPct"] = f"{(1 - g.loc['anytime', 'elapsed_ms'] / g.loc['alns_fixed', 'elapsed_ms']) * 100:.0f}"
        kx = max(cfg["kappas"])
        vals["Kmax"] = f"{kx:g}"
        dkx = at_kappa(df[df.budget_ms == B], kx)
        ge = dkx.groupby("method")[f"eff_regret_k{kx}"].mean()
        for m, key in (("anytime", "AS"), ("alns_fixed", "Fixed"), ("alns_stagnation", "Stag"),
                       ("anytime_nodelay", "NoDelay"), ("oracle_stop", "Oracle")):
            if m in ge.index:
                vals[f"{key}EffK"] = f2(ge[m])
        for base, key in (("alns_fixed", "Fixed"), ("alns_stagnation", "Stag"), ("anytime_nodelay", "NoDelay")):
            if base in set(dkx.method):
                r = _pooled(dkx, "anytime", base, f"eff_regret_k{kx}", seed=cfg["seed"])
                vals[f"dEff{key}"], vals[f"dEff{key}CI"] = f3(r["diff"]), ci(r, f3)
        if "anytime_online" in g.index:
            vals["OnlineRegret"], vals["OnlineMs"] = f2(g.loc["anytime_online", "regret_pct"]), f"{g.loc['anytime_online', 'elapsed_ms']:.1f}"
            r = _pooled(d, "anytime", "anytime_online", "regret_pct", seed=cfg["seed"])
            vals["dRegretOnline"], vals["dRegretOnlineCI"] = f3(r["diff"]), ci(r, f3)
        Bs = min(df.budget_ms.unique())
        vals["Bsmall"] = f"{Bs:g}"
        dsm = at_kappa(df[df.budget_ms == Bs], 1)
        gs = dsm.groupby("method").regret_pct.mean()
        if "anytime_noffr" in gs.index:
            vals["ASRegretSmallB"], vals["NoFFRRegretSmallB"] = f2(gs["anytime"]), f2(gs["anytime_noffr"])
            r = _pooled(dsm, "anytime", "anytime_noffr", "regret_pct", seed=cfg["seed"])
            vals["dRegretNoFFRSmallB"], vals["dRegretNoFFRSmallBCI"] = f3(r["diff"]), ci(r, f3)
            r = _pooled(d, "anytime", "anytime_noffr", "regret_pct", seed=cfg["seed"])
            vals["dRegretNoFFR"], vals["dRegretNoFFRCI"] = f3(r["diff"]), ci(r, f3)
            vals["dRegretNoFFRAbs"] = f3(abs(r["diff"]))
        tff = df[(df.method == "anytime") & (df.scale == list(cfg["scales"])[-1])].t_first_feasible_ms
        vals["TffLargePninetyfive"] = f"{np.percentile(tff, 95):.1f}"
        vals["TffLargeMedian"] = f"{np.median(tff):.1f}"
    rp = res / "static" / f"reference_{split}{tag}.csv"
    if rp.exists() and sp.exists() and "J_ortools" in pd.read_csv(rp, nrows=1).columns:
        ref = pd.read_csv(rp).dropna(subset=["J_ortools"])
        W = df.groupby("snap").scale_value.first()
        dlt = (ref.J_ortools - ref.J_alns_ref) / ref.snap.map(W).values * 100
        vals["OrtN"], vals["OrtWithin"] = str(len(ref)), f"{(dlt.abs() < 0.01).mean() * 100:.0f}"
        vals["OrtBetter"] = f"{(dlt > 0.01).mean() * 100:.0f}"
    mp = res / "offline" / f"matched_{split}.csv"
    if mp.exists():
        mm = pd.read_csv(mp)
        kx = max(cfg["kappas"])
        e = mm[(mm.scale == "all") & (mm.kappa == kx) & (mm.metric == f"eff_regret_k{kx}")].set_index("baseline")
        for base, key in (("fixed", "Fixed"), ("stagnation", "Stag"), ("anytime_nodelay", "NoDelay"),
                          ("fixed_ps", "FixedPS"), ("stagnation_ps", "StagPS")):
            if base in e.index:
                vals[f"FrontEff{key}Diff"], vals[f"FrontEff{key}CI"] = f3(e.loc[base, "diff"]), ci(e.loc[base], f3)
        m = mm
        m = m[(m.scale == "all") & (m.kappa == 1) & (m.metric == "regret_pct")].set_index("baseline")
        for base, key in (("fixed", "Fixed"), ("stagnation", "Stag"), ("fixed_ps", "FixedPS"), ("stagnation_ps", "StagPS")):
            if base in m.index:
                r = m.loc[base]
                vals[f"Front{key}Param"] = f"{r.baseline_param:g}"
                vals[f"Front{key}Ms"], vals[f"FrontOursMs"] = f"{r.t_base:.1f}", f"{r.t_ours:.1f}"
                vals[f"Front{key}Diff"], vals[f"Front{key}CI"] = f3(r["diff"]), ci(r, f3)
                vals[f"Front{key}Base"], vals["FrontOursRegret"] = f3(r.mean_b), f3(r.mean_a)
                vals[f"Front{key}Red"] = f"{(1 - r.mean_a / r.mean_b) * 100:.0f}"
                vals[f"Front{key}MoreMs"] = f"{(r.t_base / r.t_ours - 1) * 100:.0f}"
    cp = res / "closed_loop" / f"closed_loop_{split}{tag}.csv"
    if cp.exists():
        cl = pd.read_csv(cp)
        kmax = max(cfg["kappas"])
        for k in sorted(cl.kappa.unique()):
            ck = cl[cl.kappa == k]
            u = ck.groupby("method").utility_rate.mean() * 100
            cl_keys = (("anytime", "AS"), ("alns_fixed", "Fixed"), ("alns_stagnation", "Stag"),
                       (matched[0] if matched else "-", "FixedMatched"), ("regret_repair", "Repair"),
                       ("anytime_nodelay", "NoDelay"), ("alns_fixed@ps", "FixedPS"), ("alns_stagnation@ps", "StagPS"))
            for mth, key in cl_keys:
                if mth in u.index:
                    vals[f"CL{key}Util{k:g}"] = f"{u[mth]:.1f}"
            dr = ck.groupby("method").dropped_by_delay.mean()
            pm = ck.groupby("method").plan_ms_mean.mean()
            for mth, key in cl_keys:
                if mth in dr.index:
                    vals[f"CL{key}Drop{k:g}"] = f2(dr[mth])
                    vals[f"CL{key}PlanMs{k:g}"] = f"{pm[mth]:.1f}"
            cu = ck.assign(utility_rate=ck.utility_rate * 100)
            for base, key in [x for x in cl_keys if x[1] not in ("AS", "Repair")]:
                if "anytime" in u.index and base in u.index and k in (1, kmax):
                    r = _pooled(cu, "anytime", base, "utility_rate", seed=cfg["seed"])
                    suffix = "" if k == kmax else f"{k:g}"
                    vals[f"CLdUtil{key}{suffix}"], vals[f"CLdUtil{key}{suffix}CI"] = f2(r["diff"]), ci(r)
            # per scale at kappa = 1 (the regime in which the full budget is hardest to beat)
            if k == 1 and "anytime" in u.index:
                for sc in cfg["scales"]:
                    cs = cu[cu.scale == sc]
                    for base, key in (("alns_fixed", "Fixed"), ("alns_stagnation@ps", "StagPS"), ("alns_fixed@ps", "FixedPS")):
                        if base in set(cs.method):
                            r = _pooled(cs, "anytime", base, "utility_rate", seed=cfg["seed"])
                            vals[f"CLdUtil{key}One{sc.capitalize()}"] = f2(r["diff"])
                            vals[f"CLdUtil{key}One{sc.capitalize()}CI"] = ci(r)
        vals["NMissions"] = str(cl.scenario.nunique())
        vals["NKappas"] = str(cl.kappa.nunique())
        kc = res / "closed_loop" / f"kappa_curve_{split}{tag}.csv"
        if kc.exists():  # smallest kappa from which AnytimeSwarm beats the full-budget search (CI above zero)
            kk = pd.read_csv(kc)
            a = kk[kk.method == "anytime"].sort_values("kappa")
            win = a[a.ci_lo > 0]
            vals["KappaWin"] = f"{win.kappa.min():g}" if len(win) else "none"
            for r in a.itertuples():
                vals[f"KCdiff{r.kappa:g}"], vals[f"KCdiff{r.kappa:g}CI"] = f2(r.diff), f"[{r.ci_lo:.2f},\\,{r.ci_hi:.2f}]"
    eqp = res / "offline" / f"equal_compute_{split}.csv"
    if eqp.exists():  # absolute values of the equal-computation table (experiments/07)
        eq = pd.read_csv(eqp)
        a, b = eq[eq.proposed], eq[~eq.proposed]
        vals["EqRegretAS"], vals["EqEffAS"] = f3(a.regret.iloc[0]), f3(a.eff.iloc[0])
        vals["EqRegretBaseMin"], vals["EqRegretBaseMax"] = f3(b.regret.min()), f3(b.regret.max())
        vals["EqEffBaseMin"], vals["EqEffBaseMax"] = f3(b.eff.min()), f3(b.eff.max())
        vals["EqRegretRedMin"] = f"{(1 - a.regret.iloc[0] / b.regret.min()) * 100:.0f}"
        vals["EqRegretRedMax"] = f"{(1 - a.regret.iloc[0] / b.regret.max()) * 100:.0f}"
    fpth = res / "offline" / f"frontier_{split}.csv"
    if fpth.exists() and eqp.exists():  # computation each baseline family needs to reach the regret of AnytimeSwarm
        fr = pd.read_csv(fpth)
        g1 = fr[(fr.scale == "all") & (fr.kappa == 1)]
        r_as, t_as = a.regret.iloc[0], a.t.iloc[0]
        for fam, key in (("fixed", "Fixed"), ("stagnation", "Stag")):
            f_ = g1[(g1.family == fam) & (g1.t_ms > 0)].sort_values("t_ms")
            below = np.nonzero(f_.regret_pct.values <= r_as)[0]
            if len(below) and below[0] > 0:
                i = below[0]
                t_need = float(np.exp(np.interp(r_as, [f_.regret_pct.values[i], f_.regret_pct.values[i - 1]],
                                                [np.log(f_.t_ms.values[i]), np.log(f_.t_ms.values[i - 1])])))
                vals[f"Need{key}Ms"], vals[f"Speed{key}"] = f"{t_need:.0f}", f"{t_need / t_as:.1f}"
    if mp.exists():  # relative regret reduction per scale at equal computation (kappa = 1)
        mm2 = pd.read_csv(mp)
        mm2 = mm2[(mm2.kappa == 1) & (mm2.metric == "regret_pct")
                  & mm2.baseline.isin(["fixed", "stagnation", "fixed_ps", "stagnation_ps"])]
        for sc in list(cfg["scales"]):
            s2 = mm2[mm2.scale == sc]
            if len(s2):
                rel = (1 - s2.mean_a / s2.mean_b) * 100
                vals[f"Red{sc.capitalize()}Min"], vals[f"Red{sc.capitalize()}Max"] = f"{rel.min():.0f}", f"{rel.max():.0f}"
    sk = sorted((res / "closed_loop").glob(f"summary_k*_{split}.csv"))
    if cp.exists():
        clr = pd.read_csv(cp)
        kmx = clr.kappa.max()
        dr = clr[clr.kappa == kmx].groupby("method").dropped_by_delay.mean()
        pm1 = clr[clr.kappa == 1].groupby("method").plan_ms_mean.mean()
        if "anytime" in dr.index:
            for mth, key in (("alns_fixed", "Fixed"), ("alns_stagnation", "Stag"), ("anytime_nodelay", "NoDelay")):
                if mth in dr.index:
                    vals[f"DropRed{key}"] = f"{(1 - dr['anytime'] / dr[mth]) * 100:.0f}"
            if "alns_fixed" in pm1.index:
                vals["PlanRatio1"] = f"{pm1['alns_fixed'] / pm1['anytime']:.1f}"
    if sk:
        s_ = pd.read_csv(sk[0])
        bb = s_[~s_.proposed & (s_.label != "w/o delay cost")]
        vals["CLUtilBaseMinK"], vals["CLUtilBaseMaxK"] = f"{bb.u.min():.1f}", f"{bb.u.max():.1f}"
    ap_ = res / "offline" / f"allocation_{split}.csv"
    if ap_.exists():
        al = pd.read_csv(ap_).set_index("family")
        for fam, key in (("anytime", "AS"), ("fixed_ps", "FixedPS"), ("stagnation_ps", "StagPS")):
            if fam in al.index:
                vals[f"Alloc{key}None"], vals[f"Alloc{key}High"] = f"{al.loc[fam, 't_none']:.1f}", f"{al.loc[fam, 't_high']:.1f}"
                vals[f"Alloc{key}Share"] = f"{al.loc[fam, 'share_on_no_gain'] * 100:.0f}"
        vals["AllocNoneShare"] = f"{al.n_none.iloc[0] / (al.n_none.iloc[0] + al.n_pos.iloc[0]) * 100:.0f}"
    pe = res / "predictor_eval.json"
    if pe.exists():
        ev = json.loads(pe.read_text(encoding="utf-8"))
        vals["AUCLearned"], vals["AUCOnline"] = f3(ev["learned_oof"].get("auc", float("nan"))), f3(ev["online"].get("auc", float("nan")))
        vals["PosRate"] = f"{ev['learned_oof'].get('positive_rate', float('nan')) * 100:.1f}"
    if sp.exists():
        g3 = at_kappa(df[df.budget_ms == B], 1).groupby(["method", "scale"]).elapsed_ms.mean()
        for sc in cfg["scales"]:
            if ("anytime", sc) in g3.index:
                vals[f"ASMs{sc.capitalize()}"] = f"{g3[('anytime', sc)]:.0f}"
    wrap = (lambda v: v) if split == "test" else (lambda v: f"\\textcolor{{orange}}{{{v}}}")
    lines = [f"% generated by experiments/08_make_tables.py --split {split} ({cfg['_config_path']}) -- do not edit"]
    # \csname allows digits in the names (e.g. \val{CLASUtil1}); use \val{...} in main.tex
    lines += [f"\\expandafter\\def\\csname v{prefix}{k}\\endcsname{{{wrap(v)}}}" for k, v in vals.items()]
    write(lines, out / (f"numbers_{prefix}.tex" if prefix else "numbers.tex"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--tag", default="")
    ap.add_argument("--budget", type=float, default=250)
    ap.add_argument("--prefix", default="", help="macro prefix + numbers_<prefix>.tex only (e.g. One for test set 1)")
    args = ap.parse_args()
    cfg = load_config(args.config)
    res = rpath(cfg["paths"]["results_dir"])
    out = res / "tables"
    made = []
    if (res / "static" / f"static_{args.split}{args.tag}.csv").exists():
        df = load_static(cfg, args.split, args.tag)
        B = args.budget if args.budget in set(df.budget_ms) else sorted(df.budget_ms.unique())[-1]
        static_table(df, cfg, B, out)
        ablation_table(df, cfg, B, out)
        made += ["static", "ablation"]
    cl_p = res / "closed_loop" / f"closed_loop_{args.split}{args.tag}.csv"
    if cl_p.exists():
        closed_loop_table(pd.read_csv(cl_p), out)
        made.append("closed_loop")
    if (res / "predictor_eval.json").exists():
        predictor_table(res / "predictor_eval.json", out)
        made.append("predictor")
    if args.prefix:  # only the numbers of another test set, copied next to the main ones
        numbers_tex(cfg, args.split, args.tag, res, out, args.budget, args.prefix)
        pt = rpath(cfg["paths"]["paper_dir"]) / "tables"
        shutil.copy(out / f"numbers_{args.prefix}.tex", pt / f"numbers_{args.prefix}.tex")
        print(f"[ok] numbers_{args.prefix}.tex")
        return
    numbers_tex(cfg, args.split, args.tag, res, out, args.budget)
    made.append("numbers")
    if args.split != "test":  # never let a development table look like a final result
        for f in out.glob("*.tex"):
            f.write_text(f.read_text(encoding="utf-8").replace("test seeds", "DEV seeds, not final"), encoding="utf-8")
    pt = rpath(cfg["paths"]["paper_dir"]) / "tables"
    pt.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.tex"):
        shutil.copy(f, pt / f.name)
    print(f"[ok] tables: {', '.join(made) or 'none'} -> {out}")


if __name__ == "__main__":
    main()
