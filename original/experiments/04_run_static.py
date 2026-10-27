"""Step 4 - static snapshot benchmark: every method x every compute budget on the same snapshots
(H1 solution quality, H2 computation efficiency, scalability, ablations, oracle stop).

    python experiments/04_run_static.py --split dev --quick      # pilot / debugging
    python experiments/04_run_static.py --split test              # FINAL (after freezing the config)
    python experiments/04_run_static.py --split test --only-reference   # just best-known solutions

Per row (one method run on one snapshot): J (objective at publication), elapsed_ms (wall-clock,
includes feasibility-first repair), iterations, stop reason, J_eff_k<kappa> = objective after the
publication delay kappa * elapsed is applied (tasks that become infeasible are lost).
kappa-dependent methods (adaptive controller with delay cost) are run once per kappa.
`oracle_stop` rows: best stopping time in hindsight on the fixed-budget trajectory (upper bound).
Outputs: results/static/static_<split>.csv, results/static/reference_<split>.csv
Runs are appended per budget, so an interrupted run can be resumed with --resume.
"""
import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.algorithms.methods import KAPPA_DEPENDENT, solve  # noqa: E402
from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.problem import Solution, delayed_value  # noqa: E402
from anytimeswarm.utils import GUARD_LOG, append_registry, load_config, rpath, wait_machine_idle  # noqa: E402


_REF = {}


def _ref_init(cfg, snap_path):
    with open(snap_path, "rb") as f:
        _REF.update(cfg=cfg, snaps=pickle.load(f))


def _ref_one(n):
    wait_machine_idle()  # never disturb RAVEN latency measurements
    cfg, s = _REF["cfg"], _REF["snaps"][n]
    ref, P = cfg["reference"], s["P"]
    r = solve("alns_fixed", P, s["old"], ref["alns_ms"], cfg, seed=10_000 + n)
    row = {"snap": n, "J_alns_ref": r["J"]}
    if s["scale"] in ref["ortools_scales"]:
        try:
            from anytimeswarm.algorithms.ortools_ref import solve_ortools
        except ImportError:
            return row
        t = time.perf_counter()
        sol = solve_ortools(P, ref["ortools_s"])
        row["J_ortools"] = sol.objective(P) if sol is not None else np.nan
        row["ortools_s"] = time.perf_counter() - t
    return row


def reference(cfg, snap_path, sel, out, workers=1):
    """Best-known solutions (ALNS 3 s + OR-Tools 5 s). Not a timing measurement of any compared method, so
    it may run in parallel (workers > 1); each snapshot has its own fixed seed -> order independent."""
    if workers <= 1:
        _ref_init(cfg, snap_path)
        rows = []
        for i, n in enumerate(sel):
            rows.append(_ref_one(n))
            if (i + 1) % 25 == 0:
                print(f"  reference {i + 1}/{len(sel)}", flush=True)
    else:
        from multiprocessing import Pool
        with Pool(workers, initializer=_ref_init, initargs=(cfg, snap_path)) as pool:
            rows = []
            for i, row in enumerate(pool.imap(_ref_one, sel)):
                rows.append(row)
                if (i + 1) % 25 == 0:
                    print(f"  reference {i + 1}/{len(sel)}", flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    return pd.DataFrame(rows)


def base_tr(s, n, P, r):
    """Same record format as experiments/03_train_improvement_model.collect()."""
    return {k: s[k] for k in ("scenario", "scale", "profile", "seed", "call")} | {
        "idx": n, "N": P.N, "M": P.M, "scale_value": P.scale, "J0": r["J_initial"], "trace": r["trace"],
        "snapshots": r["snapshots"], "elapsed": r["elapsed_ms"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--methods", default="main+ablation")
    ap.add_argument("--budgets", default=None, help="comma list, default = config budgets_ms")
    ap.add_argument("--scales", default=None, help="comma list filter, e.g. small,medium")
    ap.add_argument("--quick", action="store_true", help="2 budgets, first 3 seeds")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--only-reference", action="store_true")
    ap.add_argument("--skip-reference", action="store_true")
    ap.add_argument("--ref-workers", type=int, default=1, help="parallel processes for the reference only")
    args = ap.parse_args()
    cfg = load_config(args.config)
    c = cfg["controller"]
    snap_path = rpath(cfg["paths"]["data_dir"]) / f"snapshots_{args.split}.pkl"
    with open(snap_path, "rb") as f:
        snaps = pickle.load(f)
    scales = args.scales.split(",") if args.scales else None
    seeds0 = cfg["seeds"][args.split]["start"]
    sel = [n for n, s in enumerate(snaps) if (not scales or s["scale"] in scales)
           and (not args.quick or s["seed"] < seeds0 + 3)]
    out_dir = rpath(cfg["paths"]["results_dir"]) / "static"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = "_quick" if args.quick else ""

    ref_path = out_dir / f"reference_{args.split}{tag}.csv"
    if not args.skip_reference and (args.only_reference or not ref_path.exists()):
        print(f"reference solutions for {len(sel)} snapshots ...")
        reference(cfg, snap_path, sel, ref_path, args.ref_workers)
    if args.only_reference:
        return

    groups = {"main": cfg["methods"]["main"], "ablation": cfg["methods"]["ablation"]}
    methods = [m for g in args.methods.split("+") for m in groups.get(g, [g])]
    budgets = [float(b) for b in args.budgets.split(",")] if args.budgets else [float(b) for b in cfg["budgets_ms"]]
    if args.quick:
        budgets = [budgets[1], budgets[3]] if len(budgets) > 3 else budgets
    pred_path = rpath(cfg["paths"]["models_dir"]) / "improvement_model.json"
    predictor = LearnedPredictor.load(pred_path) if pred_path.exists() else None
    if predictor is None and any(m.startswith("anytime") for m in methods):
        print("[warn] no models/improvement_model.json -> 'anytime' falls back to the ONLINE predictor. "
              "Run experiments/03_train_improvement_model.py first for real results.")
    kappas = cfg["kappas"]
    out = out_dir / f"static_{args.split}{tag}.csv"
    done = set()
    if args.resume and out.exists():
        done = set(pd.read_csv(out).budget_ms.unique())
    elif out.exists():
        out.unlink()

    t_start, waited = time.time(), 0.0
    # longest-budget fixed runs = recorded trajectories for experiments/10_offline_policies.py (test split;
    # dev traces come from 03_train_improvement_model.py and are not overwritten)
    trace_path = rpath(cfg["paths"]["results_dir"]) / "traces" / f"{args.split}_traces.pkl"
    save_traces = not args.quick and (args.split == "test" or not trace_path.exists())
    traces = []
    for B in budgets:
        if B in done:
            print(f"[skip] budget {B} already done")
            continue
        rows = []
        for n in sel:
            waited += wait_machine_idle()  # timing run: never overlap RAVEN-UAV
            s = snaps[n]
            P = s["P"]
            base = {k: s[k] for k in ("scenario", "scale", "profile", "seed", "call")} | {
                "snap": n, "N": P.N, "M": P.M, "scale_value": P.scale, "budget_ms": B}
            for m in methods:
                for kappa in (kappas if m in KAPPA_DEPENDENT else [np.nan]):
                    r = solve(m, P, s["old"], B, cfg, seed=n, predictor=predictor,
                              kappa=None if np.isnan(kappa) else kappa, record_solutions=(m == "alns_fixed"))
                    row = base | {"method": m, "kappa": kappa, "J": r["J"], "elapsed_ms": r["elapsed_ms"],
                                  "iters": r["iters"], "stop_reason": r["stop_reason"],
                                  "t_first_feasible_ms": r["t_first_feasible_ms"], "n_assigned": r["n_assigned"],
                                  "unassigned_reward": r["unassigned_reward"]}
                    for k in kappas:
                        row[f"J_eff_k{k}"] = delayed_value(P, r["solution"], k * r["elapsed_ms"] / 1000)[0]
                    rows.append(row)
                    if m == "alns_fixed" and B == max(budgets) and r["snapshots"] and save_traces:
                        traces.append(base_tr(s, n, P, r))
                    if m == "alns_fixed" and r["snapshots"]:
                        sols = [(t, J, Solution(P, rt)) for t, J, rt in r["snapshots"]]
                        for k in kappas:
                            util = [delayed_value(P, so, k * t / 1000)[0] - c["mu"] * P.scale * t for t, J, so in sols]
                            i = int(np.argmax(util))
                            t_o, J_o, so = sols[i]
                            o = base | {"method": "oracle_stop", "kappa": k, "J": J_o, "elapsed_ms": t_o,
                                        "iters": np.nan, "stop_reason": "oracle", "t_first_feasible_ms": np.nan,
                                        "n_assigned": so.n_assigned(),
                                        "unassigned_reward": sum(P.w[j] for j in so.unassigned)}
                            for kk in kappas:
                                o[f"J_eff_k{kk}"] = delayed_value(P, so, kk * t_o / 1000)[0]
                            rows.append(o)
        pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
        if traces:
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            with open(trace_path, "wb") as f:
                pickle.dump(traces, f)
            traces = []
        print(f"  budget {B:.0f} ms done ({len(rows)} rows, {time.time() - t_start:.0f}s elapsed)", flush=True)
    append_registry(cfg, {"run": out.stem, "script": "04_run_static", "split": args.split,
                          "method": ",".join(methods), "budget": ",".join(f"{b:g}" for b in budgets),
                          "notes": f"{len(sel)} snapshots, {time.time() - t_start:.0f}s, guard wait {waited:.0f}s, "
                                   f"concurrent RAVEN (non-latency) checks {GUARD_LOG['concurrent']} {sorted(GUARD_LOG['examples'])}"})
    print(f"[ok] -> {out}")


if __name__ == "__main__":
    main()
