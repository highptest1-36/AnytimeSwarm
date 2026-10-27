"""Step 10 - quality-vs-compute FRONTIERS of stopping policies, simulated exactly on recorded trajectories
(H2: does the adaptive rule beat simply using a smaller fixed budget or a stagnation stop?).

    python experiments/10_offline_policies.py --split dev          # OOF predictions (honest on dev)
    python experiments/10_offline_policies.py --split test         # trained model, test traces (after freeze)

Families (all on the SAME trajectory per snapshot, see anytimeswarm/offline.py):
    fixed B (12 budgets) | stagnation (patience grid) | adaptive learned (mu grid) | adaptive w/o delay cost |
    adaptive online predictor | oracle stop (hindsight, per mu)
Matched-compute test: for the configured mu, each baseline family is evaluated at the smallest parameter whose
mean compute is >= that of AnytimeSwarm (the baseline gets at least as much computation); scenario-level
paired bootstrap of the regret difference.
Outputs: results/offline/policies_<split>.csv, frontier_<split>.csv, matched_<split>.csv,
         results/figures/fig_frontier.pdf (+ copy to paper/figures/ for the test split)
Not a timing run: no wall-clock measurement happens here.
"""
import argparse
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm import offline as OF  # noqa: E402
from anytimeswarm import plotting as PL  # noqa: E402
from anytimeswarm.analysis import paired_bootstrap  # noqa: E402
from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.utils import append_registry, load_config, rpath  # noqa: E402

FIXED_B = [2, 5, 10, 15, 20, 30, 50, 75, 100, 150, 250, 500]
PATIENCE = [1, 2, 3, 5, 10, 20, 30, 50, 100, 200]
MUS = [0.0, 1e-6, 3e-6, 1e-5, 2e-5, 3e-5, 1e-4, 3e-4, 1e-3]
FAMILY_LABEL = {"fixed": "ALNS (fixed B)", "stagnation": "ALNS (stagnation stop)", "anytime": "AnytimeSwarm (proposed)",
                "anytime_nodelay": "w/o delay cost", "anytime_online": "w/o learned predictor",
                "oracle_stop": "Oracle stop", "fixed_ps": "ALNS (fixed B per scale)",
                "stagnation_ps": "ALNS (stagnation per scale)"}
STYLE_KEY = {"fixed": "alns_fixed", "stagnation": "alns_stagnation", "anytime": "anytime",
             "anytime_nodelay": "anytime_nodelay", "anytime_online": "anytime_online", "oracle_stop": "oracle_stop"}


def best_known(cfg, split, traces):
    bk = {tr["idx"]: max(s[1] for s in tr["snapshots"]) for tr in traces}
    p = rpath(cfg["paths"]["results_dir"]) / "static" / f"reference_{split}.csv"
    if p.exists():
        ref = pd.read_csv(p).set_index("snap")
        for n in bk:
            if n in ref.index:
                bk[n] = np.nanmax([bk[n], ref.J_alns_ref.get(n, np.nan), ref.get("J_ortools", pd.Series()).get(n, np.nan)])
    else:
        print(f"[warn] {p} missing -> regret is measured against the {max(FIXED_B)} ms trajectory only")
    return bk


def simulate(cfg, traces, snaps, pred_learned, pred_online, t_max):
    c, kappas, H = cfg["controller"], cfg["kappas"], cfg["controller"]["horizon_ms"]
    ck_l = OF.checkpoint_table(traces, snaps, c, t_max, kappas, pred_learned)
    ck_o = OF.checkpoint_table(traces, snaps, c, t_max, kappas, pred_online)
    rows = []
    for tr in traces:
        n, P = tr["idx"], snaps[tr["idx"]]["P"]
        traj = ck_l[n]["traj"]
        W = P.scale
        base = {k: tr[k] for k in ("scenario", "scale", "profile", "seed", "call")} | {
            "snap": n, "scale_value": W, "potential_pct": (traj.J.max() - traj.J[0]) / W * 100}

        def emit(family, param, kappa, t):
            t = max(float(t), traj.t_init)
            i = int(traj.index_at(t))
            r = base | {"family": family, "param": param, "kappa": kappa, "t_ms": t, "J": traj.J[i]}
            for k in kappas:
                r[f"J_eff_k{k}"] = traj.J_eff(i, k * t / 1000.0)
            rows.append(r)

        for B in FIXED_B:
            emit("fixed", B, np.nan, B)
        for p in PATIENCE:
            emit("stagnation", p, np.nan, OF.stagnation_stop(tr, p, t_max))
        ps = cfg.get("per_scale_baselines")
        if ps:  # baselines tuned per scale on DEV (results/per_scale_baselines_dev.json); param 0 = the dev choice
            emit("fixed_ps", 0, np.nan, ps["fixed_ms"][tr["scale"]])
            emit("stagnation_ps", 0, np.nan, OF.stagnation_stop(tr, ps["stagnation_ms"][tr["scale"]], t_max))
        for mu in MUS:
            emit("anytime_nodelay", mu, np.nan, OF.adaptive_stop(ck_l[n], kappas[0], mu, W, H, t_max, use_delay=False))
            for k in kappas:
                emit("anytime", mu, k, OF.adaptive_stop(ck_l[n], k, mu, W, H, t_max))
                emit("anytime_online", mu, k, OF.adaptive_stop(ck_o[n], k, mu, W, H, t_max))
                # oracle: best stop time in hindsight among improvement times for objective J_eff - mu W t
                cand = [(t_, i) for i, t_ in enumerate(traj.times) if t_ <= t_max]
                util = [traj.J_eff(i, k * t_ / 1000.0) - mu * W * t_ for t_, i in cand]
                emit("oracle_stop", mu, k, cand[int(np.argmax(util))][0])
    return pd.DataFrame(rows)


def add_metrics(df, bk, cfg):
    df["best_known"] = df.snap.map(bk)
    df["regret_pct"] = (df.best_known - df.J) / df.scale_value * 100
    for k in cfg["kappas"]:
        df[f"eff_regret_k{k}"] = (df.best_known - df[f"J_eff_k{k}"]) / df.scale_value * 100
    return df


def rows_at_kappa(df, k):
    return df[df.kappa.isna() | np.isclose(df.kappa.fillna(-1), k)]


def frontier(df, cfg):
    out = []
    for k in cfg["kappas"]:
        dk = rows_at_kappa(df, k)
        for scale, g in [("all", dk)] + list(dk.groupby("scale")):
            s = g.groupby(["family", "param"]).agg(t_ms=("t_ms", "mean"), regret_pct=("regret_pct", "mean"),
                                                   eff_regret=(f"eff_regret_k{k}", "mean"), n=("snap", "size"))
            out.append(s.reset_index().assign(kappa=k, scale=scale))
    return pd.concat(out, ignore_index=True)


def matched(df, cfg, mu, metric_by_kappa):
    """Ours at mu vs each baseline family at the smallest parameter with mean compute >= ours (pooled)."""
    rows = []
    for k in cfg["kappas"]:
        metric = metric_by_kappa(k)
        dk = rows_at_kappa(df, k)
        ours = dk[(dk.family == "anytime") & np.isclose(dk.param, mu)]
        t_ours = ours.t_ms.mean()
        for fam in ["fixed", "stagnation", "fixed_ps", "stagnation_ps", "anytime_nodelay", "anytime_online"]:
            g = dk[dk.family == fam]
            if not len(g):
                continue
            mt = g.groupby("param").t_ms.mean()
            ok = mt[mt >= t_ours]
            if fam.startswith("anytime"):  # ablations: same mu (they are variants of the rule, not tuned baselines)
                ok = mt[np.isclose(mt.index, mu)]
            if fam.endswith("_ps"):  # one dev-chosen configuration, compared as it is
                ok = mt
            if not len(ok):
                continue
            p = ok.idxmin() if not (fam.startswith("anytime") or fam.endswith("_ps")) else ok.index[0]
            base = g[np.isclose(g.param, p)]
            for scale, (o, b) in [("all", (ours, base))] + [(s, (ours[ours.scale == s], base[base.scale == s]))
                                                            for s in cfg["scales"]]:
                a = o.groupby("scenario")[[metric, "t_ms"]].mean()
                bb = b.groupby("scenario")[[metric, "t_ms"]].mean()
                j = a.add_suffix("_ours").join(bb.add_suffix("_base")).dropna()
                r = paired_bootstrap(j[f"{metric}_ours"], j[f"{metric}_base"], seed=cfg["seed"])
                rows.append({"kappa": k, "scale": scale, "metric": metric, "baseline": fam, "baseline_param": p,
                             "t_ours": j.t_ms_ours.mean(), "t_base": j.t_ms_base.mean(), **r,
                             "significant_better": r["ci_hi"] < 0})
    return pd.DataFrame(rows)


def frontier_fig(fr, cfg, out, mu):
    plt = PL.plt
    scales = list(cfg["scales"])
    kmax = max(cfg["kappas"])
    fig, axes = plt.subplots(1, len(scales) + 1, figsize=(PL.LNCS_WIDTH_IN, 2.2))
    panels = [(s, 1, "regret_pct", s) for s in scales] + [("all", kmax, "eff_regret", rf"all, $\kappa$={kmax:g}")]
    for ax, (scale, k, ycol, title) in zip(axes, panels):
        g = fr[(fr.scale == scale) & np.isclose(fr.kappa, k)]
        for fam in ["fixed", "stagnation", "anytime_online", "anytime", "oracle_stop"]:
            d = g[g.family == fam].sort_values("t_ms")
            d = d[d.t_ms > 0]
            if not len(d):
                continue
            st = PL.style(STYLE_KEY[fam])
            ax.plot(d.t_ms, d[ycol], color=st["color"], ls=st.get("ls", "-"), marker=st["marker"], ms=2.5,
                    lw=0.9, label=FAMILY_LABEL[fam], zorder=st.get("z", 2))
            if fam == "anytime":
                sel = d[np.isclose(d.param, mu)]
                ax.plot(sel.t_ms, sel[ycol], marker="*", ms=7, color=st["color"], markeredgecolor="black",
                        markeredgewidth=0.4, ls="none", zorder=5)
        for fam, mk in (("fixed_ps", "s"), ("stagnation_ps", "^")):  # single dev-tuned points
            d = g[g.family == fam]
            if len(d):
                st = PL.style(STYLE_KEY[fam.replace("_ps", "")])
                ax.plot(d.t_ms, d[ycol], marker=mk, ms=5, color="white", markeredgecolor=st["color"],
                        markeredgewidth=1.1, ls="none", label=FAMILY_LABEL[fam], zorder=4)
        ax.set_xscale("log")
        ax.set_title(title, fontsize=7)
        ax.set_xlabel("mean compute (ms)", fontsize=6.5)
        ax.tick_params(labelsize=6)
    axes[0].set_ylabel("regret to best known (%)", fontsize=6.5)
    axes[-1].set_ylabel("regret after delay (%)", fontsize=6.5)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=4, fontsize=5.8, bbox_to_anchor=(0.5, 0.0), frameon=False)
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    PL.save(fig, out / "fig_frontier")


def allocation(df, mu, out):
    """Why adaptive stopping helps: computation spent per snapshot vs the improvement still available on it.
    Snapshots are grouped by the improvement that the 500 ms search finds over the repaired plan."""
    plt = PL.plt
    d1 = rows_at_kappa(df, 1)
    sel = {"anytime": d1[(d1.family == "anytime") & np.isclose(d1.param, mu)],
           "stagnation_ps": d1[d1.family == "stagnation_ps"], "fixed_ps": d1[d1.family == "fixed_ps"]}
    pot = sel["anytime"].set_index("snap").potential_pct
    bins = pd.Series("none", index=pot.index)
    pos = pot[pot > 1e-9]
    if len(pos) >= 3:
        q = pd.qcut(pos, 3, labels=["low", "mid", "high"])
        bins.loc[q.index] = q.astype(str)
    order = ["none", "low", "mid", "high"]
    rows = []
    for fam, d in sel.items():
        if not len(d):
            continue
        g = d.set_index("snap").t_ms.groupby(bins).mean().reindex(order)
        tot = d.t_ms.sum()
        share_none = d.set_index("snap").t_ms[bins == "none"].sum() / tot if tot else np.nan
        rows.append({"family": fam, **{f"t_{b}": g[b] for b in order}, "share_on_no_gain": share_none,
                     "n_none": int((bins == "none").sum()), "n_pos": int((bins != "none").sum())})
    tab = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(PL.LNCS_WIDTH_IN * 0.62, 2.0))
    w = 0.8 / max(len(tab), 1)
    for i, r in tab.reset_index(drop=True).iterrows():
        st = PL.style(STYLE_KEY[r.family.replace("_ps", "")] if r.family != "anytime" else "anytime")
        ax.bar(np.arange(len(order)) + i * w, [r[f"t_{b}"] for b in order], w * 0.92, color=st["color"],
               alpha=1.0 if r.family == "anytime" else 0.75, label=FAMILY_LABEL[r.family])
    ax.set_xticks(np.arange(len(order)) + w * (len(tab) - 1) / 2)
    ax.set_xticklabels(["no gain", "low", "medium", "high"])
    ax.set_xlabel("improvement available to a 500 ms search", fontsize=6.5)
    ax.set_ylabel("mean compute (ms)", fontsize=6.5)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.8, frameon=False)
    fig.tight_layout()
    PL.save(fig, out / "fig_allocation")
    return tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    args = ap.parse_args()
    cfg = load_config(args.config)
    c = cfg["controller"]
    res = rpath(cfg["paths"]["results_dir"])
    t_max = float(max(cfg["budgets_ms"]))
    with open(res / "traces" / f"{args.split}_traces.pkl", "rb") as f:
        traces = pickle.load(f)
    with open(rpath(cfg["paths"]["data_dir"]) / f"snapshots_{args.split}.pkl", "rb") as f:
        snaps = pickle.load(f)

    X, y, groups, meta = OF.build_dataset(traces, c, t_max)
    if args.split == "dev":
        pred = OF.oof_predictions(X, y, groups)
    else:
        pred = LearnedPredictor.load(rpath(cfg["paths"]["models_dir"]) / "improvement_model.json").predict_many(X)
    pred_learned = {(i, round(t, 6)): p for (i, t), p in zip(meta, pred)}
    pred_online = OF.online_gains(traces, c, t_max)
    print(f"{len(traces)} trajectories, {len(y)} checkpoints; simulating policies ...", flush=True)

    df = add_metrics(simulate(cfg, traces, snaps, pred_learned, pred_online, t_max), best_known(cfg, args.split, traces), cfg)
    out_dir = res / "offline"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / f"policies_{args.split}.csv", index=False)
    fr = frontier(df, cfg)
    fr.to_csv(out_dir / f"frontier_{args.split}.csv", index=False)
    mu = c["mu"]
    m = pd.concat([matched(df, cfg, mu, lambda k: "regret_pct"),
                   matched(df, cfg, mu, lambda k: f"eff_regret_k{k}")], ignore_index=True)
    m.to_csv(out_dir / f"matched_{args.split}.csv", index=False)

    pd.set_option("display.width", 200)
    for k in cfg["kappas"]:
        g = fr[(fr.scale == "all") & (fr.kappa == k)]
        print(f"\n--- frontier, all scales, kappa={k} (mean ms / regret % / regret after delay %) ---")
        for fam in ["fixed", "stagnation", "anytime", "anytime_nodelay", "anytime_online", "oracle_stop"]:
            d = g[g.family == fam].sort_values("t_ms")
            print(f"{fam:16s} " + "  ".join(f"[{p:g}] {t:.1f}/{r:.3f}/{e:.3f}" for p, t, r, e in
                                            zip(d.param, d.t_ms, d.regret_pct, d.eff_regret)))
    show = m[(m.scale == "all")][["kappa", "metric", "baseline", "baseline_param", "t_ours", "t_base", "diff",
                                   "ci_lo", "ci_hi", "significant_better"]]
    print(f"\n--- matched compute (ours mu={mu:g}; diff = ours - baseline, negative = ours better) ---")
    print(show.round(4).to_string(index=False))

    PL.setup()
    frontier_fig(fr, cfg, res / "figures", mu)
    alloc = allocation(df, mu, res / "figures")
    alloc.to_csv(out_dir / f"allocation_{args.split}.csv", index=False)
    print("\n--- compute allocation (mean ms per group of available improvement) ---")
    print(alloc.round(3).to_string(index=False))
    if args.split == "test":
        pf = rpath(cfg["paths"]["paper_dir"]) / "figures"
        for name in ("fig_frontier.pdf", "fig_allocation.pdf"):
            shutil.copy(res / "figures" / name, pf / name)
    append_registry(cfg, {"run": f"offline_policies_{args.split}", "script": "10_offline_policies", "split": args.split,
                          "notes": f"{len(traces)} trajectories, mu={mu:g}"})
    print(f"[ok] -> {out_dir}")


if __name__ == "__main__":
    main()
