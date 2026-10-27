"""Step 3 - learn the improvement predictor E[Delta J_search | h_tau] on DEV snapshots, evaluate it with
scenario-grouped cross-validation, and simulate the stopping rule offline to choose mu (dev only).

    python experiments/03_train_improvement_model.py            # collects traces once, then fits
    python experiments/03_train_improvement_model.py --recollect

Why offline simulation is exact: every ALNS variant uses the same seed and per-iteration cooling, so
an adaptive run follows the same trajectory as the fixed-budget run and simply stops earlier.
Outputs
    results/traces/dev_traces.pkl                 raw anytime traces (+ best solutions)
    models/improvement_model.json                 the predictor used on test (portable JSON)
    results/predictor_eval.json / _deciles.csv    H1-style evidence that h_tau predicts future gain
    results/mu_selection_dev.csv                  offline stopping trade-off per (mu, kappa)
"""
import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.algorithms.methods import solve  # noqa: E402
from anytimeswarm.controller.delay_cost import DelayModel  # noqa: E402
from anytimeswarm.controller.features import FEATURES, TraceView, features_at, target_at  # noqa: E402
from anytimeswarm.controller.improvement_model import LearnedPredictor, OnlinePredictor  # noqa: E402
from anytimeswarm.simulator.problem import Solution, delayed_value  # noqa: E402
from anytimeswarm.utils import append_registry, load_config, rpath, save_json, wait_machine_idle  # noqa: E402


def collect(cfg, snaps, t_max):
    traces = []
    for n, s in enumerate(snaps):
        wait_machine_idle()  # traces are wall-clock timed: never overlap RAVEN-UAV
        r = solve("alns_fixed", s["P"], s["old"], t_max, cfg, seed=n, record_solutions=True)
        traces.append({k: s[k] for k in ("scenario", "scale", "profile", "seed", "call")} | {
            "idx": n, "N": s["P"].N, "M": s["P"].M, "scale_value": s["P"].scale, "J0": r["J_initial"],
            "trace": r["trace"], "snapshots": r["snapshots"], "elapsed": r["elapsed_ms"]})
        if (n + 1) % 50 == 0:
            print(f"  traces {n + 1}/{len(snaps)}", flush=True)
    return traces


def build_dataset(traces, c, t_max):
    X, y, g, meta = [], [], [], []
    H = c["horizon_ms"]
    for tr in traces:
        v = TraceView(tr["trace"]["iter_t"], tr["trace"]["imp"], tr["J0"], tr["scale_value"], tr["trace"]["u0"])
        t = max(c["min_ms"], (tr["trace"]["iter_t"][0] if tr["trace"]["iter_t"] else c["min_ms"]))
        while t + H <= t_max:
            X.append(features_at(v, t, tr["N"], tr["M"]))
            y.append(target_at(v, t, H))
            g.append(tr["scenario"])
            meta.append((tr["idx"], t))
            t += c["check_ms"]
    return np.asarray(X), np.asarray(y), np.asarray(g), meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--recollect", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    c = cfg["controller"]
    t_max = float(max(cfg["budgets_ms"]))
    res = rpath(cfg["paths"]["results_dir"])
    tpath = res / "traces" / "dev_traces.pkl"
    with open(rpath(cfg["paths"]["data_dir"]) / "snapshots_dev.pkl", "rb") as f:
        snaps = pickle.load(f)
    if tpath.exists() and not args.recollect:
        with open(tpath, "rb") as f:
            traces = pickle.load(f)
    else:
        print(f"collecting {len(snaps)} dev traces of {t_max:.0f} ms ...")
        traces = collect(cfg, snaps, t_max)
        tpath.parent.mkdir(parents=True, exist_ok=True)
        with open(tpath, "wb") as f:
            pickle.dump(traces, f)

    X, y, groups, meta = build_dataset(traces, c, t_max)
    print(f"dataset: {len(y)} checkpoints from {len(traces)} traces, {len(set(groups))} scenarios, "
          f"positive-gain rate {(y > 0).mean() * 100:.1f}%")

    oof = np.zeros(len(y))
    for tr_i, te_i in GroupKFold(5).split(X, y, groups):
        oof[te_i] = LearnedPredictor(horizon_ms=c["horizon_ms"]).fit(X[tr_i], y[tr_i]).predict_many(X[te_i])
    online = np.array([OnlinePredictor(c["horizon_ms"]).predict(f) for f in X])
    ev = {}
    for name, p in (("learned_oof", oof), ("online", online)):
        # the target is zero at ~99% of checkpoints -> Spearman is dominated by ties; AUC / AP of
        # "any improvement in the next H ms" measure the ranking that matters for stopping
        ev[name] = {"spearman": float(spearmanr(p, y).correlation), "mae_pct": float(np.abs(p - y).mean()),
                    "auc": float(roc_auc_score(y > 0, p)), "avg_precision": float(average_precision_score(y > 0, p)),
                    "positive_rate": float((y > 0).mean()), "mean_pred": float(p.mean()), "mean_true": float(y.mean())}
        print(f"  {name:12s} spearman={ev[name]['spearman']:.3f} AUC={ev[name]['auc']:.3f} "
              f"AP={ev[name]['avg_precision']:.3f} MAE={ev[name]['mae_pct']:.4f}% "
              f"mean pred/true={ev[name]['mean_pred']:.4f}/{ev[name]['mean_true']:.4f}")
    q = pd.qcut(oof, 10, labels=False, duplicates="drop")
    dec = pd.DataFrame({"bin": q, "pred": oof, "true": y, "online": online}).groupby("bin").mean().reset_index()
    dec.to_csv(res / "predictor_deciles.csv", index=False)

    model = LearnedPredictor(horizon_ms=c["horizon_ms"], meta={"n_samples": int(len(y)), "t_max_ms": t_max}).fit(X, y)
    mdir = rpath(cfg["paths"]["models_dir"])
    mdir.mkdir(parents=True, exist_ok=True)
    model.save(mdir / "improvement_model.json")
    coef = dict(zip(FEATURES, model.coef.round(4).tolist()))
    save_json({**ev, "coef_standardised": coef, "n_samples": int(len(y))}, res / "predictor_eval.json")
    print("  standardised coefficients:", coef)

    # ---------------------------------------------------------- offline stopping simulation (dev)
    pred_at = {(i, round(t, 6)): p for (i, t), p in zip(meta, oof)}
    rows = []
    H = c["horizon_ms"]
    sol_cache = {}
    for kappa in cfg["kappas"]:
        for tr in traces:
            P = snaps[tr["idx"]]["P"]
            sols = tr["snapshots"]
            if tr["idx"] not in sol_cache:
                sol_cache[tr["idx"]] = [Solution(P, s_[2]) for s_ in sols]
            objs = sol_cache[tr["idx"]]
            times = [s_[0] for s_ in sols]
            dm = DelayModel(P, kappa)
            t0 = max(c["min_ms"], tr["trace"]["iter_t"][0] if tr["trace"]["iter_t"] else c["min_ms"])
            checks = []  # (t, predicted gain, delay cost) along the trajectory - independent of mu
            t = t0
            while t + H <= t_max:
                k_sol = int(np.searchsorted(times, t, side="right")) - 1
                p = pred_at.get((tr["idx"], round(t, 6)))
                if p is not None:
                    checks.append((t, p * P.scale / 100, dm.cost(objs[k_sol], t, H)))
                t += c["check_ms"]
            Jeff_full = delayed_value(P, objs[-1], kappa * t_max / 1000)[0]
            for mu in [0.0, 1e-5, 3e-5, 1e-4, 3e-4]:
                t_stop = next((t for t, g, dc in checks if g <= dc + mu * P.scale * H), t_max)
                k_end = int(np.searchsorted(times, t_stop, side="right")) - 1
                J_stop = sols[k_end][1]
                Jeff_stop = delayed_value(P, objs[k_end], kappa * t_stop / 1000)[0]
                rows.append({"kappa": kappa, "mu": mu, "scale": tr["scale"], "t_stop": t_stop,
                             "quality_loss_pct": (sols[-1][1] - J_stop) / P.scale * 100,
                             "eff_gain_vs_full_pct": (Jeff_stop - Jeff_full) / P.scale * 100})
    df = pd.DataFrame(rows)
    df.to_csv(res / "mu_selection_dev.csv", index=False)
    summ = df.groupby(["kappa", "mu"]).agg(t_stop=("t_stop", "mean"), loss=("quality_loss_pct", "mean"),
                                          eff_gain=("eff_gain_vs_full_pct", "mean")).round(4)
    print("\noffline stopping on dev (vs fixed %.0f ms):\n" % t_max, summ.to_string())
    ok = summ.xs(1, level="kappa") if 1 in cfg["kappas"] else summ
    cand = ok[ok.loss <= 0.1]  # pre-registered rule: lose at most 0.1% of the reward scale vs fixed B_max
    if len(cand):
        mu_s = float(cand.index.max())
        t_s = float(summ.loc[(1, mu_s), "t_stop"]) if 1 in cfg["kappas"] else float("nan")
        save_json({"mu": mu_s, "mean_t_stop_ms_kappa1": t_s, "rule": "largest mu with loss <= 0.1% at kappa=1",
                   "grid": [0.0, 1e-5, 3e-5, 1e-4, 3e-4]}, res / "mu_suggested.json")
        print(f"\nSuggested mu (largest mu with mean quality loss <= 0.1% of scale at kappa=1): "
              f"{cand.index.max():g}  -> write it into controller.mu BEFORE running test experiments.")
    append_registry(cfg, {"run": "improvement_model", "script": "03_train_improvement_model", "split": "dev",
                          "notes": f"AUC_oof={ev['learned_oof']['auc']:.3f}, online={ev['online']['auc']:.3f}; "
                                   f"spearman_oof={ev['learned_oof']['spearman']:.3f}, online={ev['online']['spearman']:.3f}"})


if __name__ == "__main__":
    main()
