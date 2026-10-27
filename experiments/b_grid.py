#!/usr/bin/env python3
"""Tier B experiment runner: closed-loop missions over a grid of execution level x latency x kappa x trigger x method.

    python experiments/b_grid.py --name explore_theta --exec mid --lat none --kappas 10 \
        --triggers event,deviation:30,deviation:60 --methods alns_fixed@40,anytime --workers 4
    python experiments/b_grid.py --config experiments/configs/<frozen>.yaml      # every option from a YAML file

Seeds: --split dev (0-9, development) or --split heldout (journal held-out seeds, ONLY with a frozen config whose
`frozen: true` flag is set). Scales: --scales (default small,medium,large; xl = 40 UAVs / 280 tasks).
Planner: the frozen conference planner + predictor; `anytime_risk` uses the dev-fitted error model of the execution
level (models/error_model_dev.json) and the expected latency of the latency level. `anytime_risk~<level>` uses the
error model of another level (misspecification study), `anytime_risk~zero` the zero model (no execution error).
Timing: missions are distributed over --workers processes; inside one (configuration) all missions run before the
next configuration starts, so methods are interleaved in time and share the same machine load. The machine-idle
guard (RAVEN on Windows, PX4/Gazebo in WSL) is checked before each configuration.
Output: results/tier_b/<name>.csv (checkpoint after every configuration; --resume continues).
"""
import argparse
import copy
import os
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402
from journal_core.risk import ErrorModel, expected_latency  # noqa: E402
from run_guarded import _busy  # noqa: E402

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import env_info, load_config  # noqa: E402

FROZEN_CFG = ORIGINAL / "configs" / "frozen_2026-10-24.yaml"
FROZEN_MODEL = ORIGINAL / "models" / "improvement_model.json"
XL = {"n_uav": 40, "n_tasks": 280, "stream": 3}   # conference xlarge definition (own RNG stream)
_W = {}


def _init():
    _W["cfg"] = load_config(FROZEN_CFG)
    _W["pred"] = LearnedPredictor.load(FROZEN_MODEL)
    _W["err"] = ErrorModel.load_all(ROOT / "models" / "error_model_dev.json")
    os.environ.setdefault("OMP_NUM_THREADS", "1")


def _one(job):
    sc, xl, ll, kappa, trig, method, B = job
    cfg = _W["cfg"]
    base, _, opt = method.partition("@")
    budget = float(opt) if opt else B
    base, _, err_level = base.partition("~")
    kw = {}
    if base == "anytime_risk":
        lv = err_level or xl
        kw = {"err": _W["err"].get(lv, ErrorModel()), "latency_mean_s": expected_latency(LATENCY_LEVELS[ll])}
    r = run_mission_kin(copy.deepcopy(sc), cfg, base, budget, kappa=kappa, xm=EXEC_LEVELS[xl], lat=LATENCY_LEVELS[ll],
                        predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw)
    r["method"] = method
    return r


def scenarios(cfg, split, scales, seeds_override=None):
    s = seeds_override or cfg["seeds"][split]
    out = []
    for scale in scales:
        c = cfg
        if scale == "xl":
            c = copy.deepcopy(cfg)
            c["scales"]["xl"] = XL
        for profile in cfg["profiles"]:
            for seed in range(s["start"], s["start"] + s["n"]):
                out.append(generate_scenario(c, scale, profile, seed))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="YAML with any of the options below (overrides defaults)")
    ap.add_argument("--name", default="grid")
    ap.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ap.add_argument("--scales", default="small,medium,large")
    ap.add_argument("--exec", default="low,mid")
    ap.add_argument("--lat", default="none,high")
    ap.add_argument("--kappas", default="1,10,50")
    ap.add_argument("--triggers", default="event")
    ap.add_argument("--methods", default="alns_fixed@40,alns_fixed,alns_stagnation,anytime,anytime_risk,anytime_nodelay")
    ap.add_argument("--quick", action="store_true", help="first 2 seeds only")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    seeds_override = None
    if args.config:
        y = yaml.safe_load(Path(args.config).read_text())
        for k, v in y.get("grid", {}).items():
            setattr(args, k, ",".join(map(str, v)) if isinstance(v, list) else v)
        if args.split == "heldout":
            if not y.get("frozen"):
                sys.exit("held-out seeds need a config with `frozen: true`")
            seeds_override = y["heldout_seeds"]
    elif args.split == "heldout":
        sys.exit("held-out seeds need --config <frozen yaml>")

    cfg = load_config(FROZEN_CFG)
    B = float(cfg["closed_loop_budget_ms"])
    scen = scenarios(cfg, args.split, args.scales.split(","), seeds_override)
    if args.quick:
        s0 = min(s.seed for s in scen)
        scen = [s for s in scen if s.seed < s0 + 2]
    out = ROOT / "results" / "tier_b" / f"{args.name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, done = [], set()
    if args.resume and out.exists():
        rows = pd.read_csv(out).to_dict("records")
        done = {(r["exec_level"], r["latency_level"], float(r["kappa"]), r["trigger"], r["method"]) for r in rows}
    grid = [(xl, ll, float(k), tr, m) for xl in args.exec.split(",") for ll in args.lat.split(",")
            for k in args.kappas.split(",") for tr in args.triggers.split(",") for m in args.methods.split(",")]
    print(f"[grid] {args.name}: {len(scen)} missions x {len(grid)} configurations, workers={args.workers}")
    print(f"[grid] env {env_info()}", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(args.workers, initializer=_init) as pool:
        for (xl, ll, k, tr, m) in grid:
            if (xl, ll, k, tr, m) in done:
                continue
            waited = 0
            while _busy():
                if not waited:
                    print(f"[guard] machine busy, waiting: {_busy()[0][:90]}", flush=True)
                time.sleep(30)
                waited += 30
            batch = pool.map(_one, [(sc, xl, ll, k, tr, m, B) for sc in scen], chunksize=1)
            for r in batch:
                r["workers"] = args.workers
            rows += batch
            d = pd.DataFrame(batch)
            print(f"  exec={xl:7s} lat={ll:4s} k={k:>3g} {tr:13s} {m:16s} U={d.utility_rate.mean():.4f} "
                  f"late={d.late_served.mean():5.2f} dropD={d.dropped_by_delay.mean():4.2f} "
                  f"dropX={d.dropped_in_exec.mean():5.2f} replans={d.n_replans.mean():5.1f} "
                  f"ms={d.plan_ms_mean.mean():6.1f} ({time.time() - t0:.0f}s)", flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[ok] {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
