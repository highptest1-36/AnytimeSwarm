"""Step 5 - closed-loop missions (H3 dynamic robustness): methods x kappa on whole missions.

    python experiments/05_run_closed_loop.py --split test
    python experiments/05_run_closed_loop.py --split dev --quick --keep-logs 2

Each mission: events trigger replanning, planning time is converted into mission time with kappa,
UAVs wait for the new plan after their committed task. Metrics: completion / utility rate,
deadline misses, tasks dropped by delay, reassignments, planning time, mission objective.
Outputs: results/closed_loop/closed_loop_<split>.csv, results/missions/*.pkl (example logs)
"""
import argparse
import copy
import pickle
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.executor import run_mission  # noqa: E402
from anytimeswarm.utils import GUARD_LOG, append_registry, load_config, rpath, wait_machine_idle  # noqa: E402


def parse_spec(spec: str, B: float, cfg: dict, scale: str):
    """Method spec -> (base method, budget, cfg for this run).
        alns_fixed@40          own budget (ms)
        alns_fixed@ps          budget per scale   (cfg per_scale_baselines.fixed_ms, chosen on dev)
        alns_stagnation@ps     patience per scale (cfg per_scale_baselines.stagnation_ms, chosen on dev)
        alns_stagnation@pat=20 absolute patience (ms)
        anytime@mu=3e-6        another compute price (closed-loop frontier only)"""
    base, _, opt = spec.partition("@")
    c = cfg
    if not opt:
        return base, B, c
    if opt == "ps":
        ps = cfg["per_scale_baselines"]
        if base == "alns_fixed":
            return base, float(ps["fixed_ms"][scale]), c
        opt = f"pat={ps['stagnation_ms'][scale]}"
    key, _, val = opt.partition("=")
    if not val:
        return base, float(key), c
    c = copy.deepcopy(cfg)
    if key == "mu":
        c["controller"]["mu"] = float(val)
    elif key == "pat":  # absolute patience: frac * B = pat
        c["controller"]["stagnation_frac"] = float(val) / B
        c["controller"]["stagnation_min_ms"] = float(val)
    else:
        raise ValueError(spec)
    return base, B, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--methods", default=None, help="comma list, or @<key> for cfg['methods'][key]")
    ap.add_argument("--kappas", default=None, help="comma list, default cfg closed_loop_kappas or kappas")
    ap.add_argument("--tag", default="", help="suffix of the output file")
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--resume", action="store_true", help="skip (kappa, method) pairs already in the output")
    ap.add_argument("--keep-logs", type=int, default=3, help="#missions per method/kappa whose logs are kept")
    args = ap.parse_args()
    cfg = load_config(args.config)
    with open(rpath(cfg["paths"]["data_dir"]) / f"scenarios_{args.split}.pkl", "rb") as f:
        scenarios = pickle.load(f)
    if args.quick:
        s0 = cfg["seeds"][args.split]["start"]
        scenarios = [s for s in scenarios if s.seed < s0 + 2]
    if args.methods and args.methods.startswith("@"):
        methods = cfg["methods"][args.methods[1:]]
    else:
        methods = args.methods.split(",") if args.methods else cfg["methods"]["closed_loop"]
    kappas = ([float(k) for k in args.kappas.split(",")] if args.kappas
              else cfg.get("closed_loop_kappas", cfg["kappas"]))
    B = args.budget or cfg["closed_loop_budget_ms"]
    pred_path = rpath(cfg["paths"]["models_dir"]) / "improvement_model.json"
    predictor = LearnedPredictor.load(pred_path) if pred_path.exists() else None
    if predictor is None:
        print("[warn] no improvement model -> anytime uses the online predictor")
    res = rpath(cfg["paths"]["results_dir"])
    logs_dir = res / "missions"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out = res / "closed_loop" / f"closed_loop_{args.split}{'_quick' if args.quick else ''}{args.tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, done = [], set()
    if args.resume and out.exists():
        rows = pd.read_csv(out).to_dict("records")
        done = {(float(r["kappa"]), r["method"]) for r in rows}
    t0 = time.time()
    for kappa in kappas:
        for m in methods:
            if (float(kappa), m) in done:
                print(f"  [skip] kappa={kappa:g} {m}")
                continue
            kept = 0
            for sc in scenarios:
                wait_machine_idle()  # timing run: never overlap RAVEN-UAV latency measurements
                base_m, Bm, c_run = parse_spec(m, B, cfg, sc.scale)
                keep = kept < args.keep_logs and sc.scale == "medium"
                r = run_mission(sc, c_run, base_m, Bm, kappa=kappa, predictor=predictor, seed=sc.seed, keep_log=keep)
                r["method"] = m
                if keep:
                    with open(logs_dir / f"{sc.name}_{m}_k{kappa:g}.pkl", "wb") as f:
                        pickle.dump({"scenario": sc, "metrics": r}, f)
                    kept += 1
                rows.append({k: v for k, v in r.items() if not k.startswith("_")})
            d = pd.DataFrame([x for x in rows if x["method"] == m and x["kappa"] == kappa])
            print(f"  kappa={kappa:>4g} {m:20s} utility={d.utility_rate.mean():.3f} completion={d.completion_rate.mean():.3f} "
                  f"dropped={d.dropped_by_delay.mean():.2f} plan_ms={d.plan_ms_mean.mean():.1f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)  # checkpoint after every (kappa, method)
    pd.DataFrame(rows).to_csv(out, index=False)
    append_registry(cfg, {"run": out.stem, "script": "05_run_closed_loop", "split": args.split,
                          "method": ",".join(methods), "budget": B, "notes": f"{len(scenarios)} missions, concurrent RAVEN (non-latency) checks "
                                   f"{GUARD_LOG['concurrent']} {sorted(GUARD_LOG['examples'])}"})
    print(f"[ok] -> {out}")


if __name__ == "__main__":
    main()
