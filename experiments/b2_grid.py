#!/usr/bin/env python3
"""Tier B runner of study 2: literature baselines, the proposed replanner and the regime sweep.

    python experiments/b2_grid.py --name dev_x --exec mid --lat high --kappas 50 --windows 1,0.5 \
        --methods "alns_fixed@40+event,online_curve+event,proposed~z=0.5+hybrid:30:60" --workers 4
    python experiments/b2_grid.py --config experiments/configs/<frozen v2>.yaml

Method grammar: journal_core.study2 (<base>[@B][~k=v,...][+trigger]); a method without "+trigger" is crossed with
--triggers. --windows multiplies every time window (1 = original scenarios, 0.5 = tight windows).
Seeds: --split dev (0-9) or --split heldout (only with a config whose `frozen: true` flag is set; seeds from the
config). Error models (dev): models/error_model_dev.json, chosen by the execution level of the configuration.
Timing and guard as experiments/b_grid.py: one configuration at a time, missions spread over the workers.
Output: results/tier_b/<name>.csv (checkpoint after every configuration; --resume continues).
"""
import argparse
import copy
import os
import sys
import time
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "experiments"))

from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402
from journal_core.risk import ErrorModel, expected_latency  # noqa: E402
from journal_core.study2 import Z_BY_LEVEL, parse_method, solve2, tighten_windows  # noqa: E402
from run_guarded import _busy  # noqa: E402
from b_grid import FROZEN_CFG, FROZEN_MODEL, scenarios  # noqa: E402
sys.path.insert(0, str(ROOT / "journal_ros"))
from common import S_T, S_X, tier_c_config  # noqa: E402

from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.utils import env_info, load_config  # noqa: E402

_W = {}
DEFAULT_MS_PER_TASK = 1.0


def _init(ms_per_task):
    _W["cfg"] = load_config(FROZEN_CFG)
    _W["pred"] = LearnedPredictor.load(FROZEN_MODEL)
    _W["err"] = ErrorModel.load_all(ROOT / "models" / "error_model_dev.json")
    fc = ROOT / "models" / "error_model_tierc_dev.json"
    _W["err_gz"] = ErrorModel.load_all(fc) if fc.exists() else {}
    _W["cfg_gz"] = tier_c_config()
    _W["ms_per_task"] = ms_per_task
    os.environ.setdefault("OMP_NUM_THREADS", "1")


def _one(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    if sc.scale == "gz":                               # tier B counterpart of a tier C mission (see b_grid.py)
        cfg, errs = _W["cfg_gz"], _W["err_gz"]
        xm = replace(xm, wind_mps=xm.wind_mps * S_X / S_T, accel_mps2=xm.accel_mps2 * S_X / S_T ** 2)
        kappa = kappa * S_T
    base, budget, opt, _ = parse_method(spec)
    kw = {"err": errs.get(opt.get("err", xl), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if opt.get("z", "auto") != "auto" else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None}
    if opt.get("z") == "auto" or (base == "proposed" and "z" not in opt):
        kw["z"] = Z_BY_LEVEL[xl]
    if sc.scale == "gz":                               # buffer and trigger times are given in tier B seconds
        if kw["buf_s"] is not None:
            kw["buf_s"] *= S_T
        kind, _, pars = trig.partition(":")
        if pars:
            trig = kind + ":" + ":".join(f"{float(x) * S_T:g}" for x in pars.split(":"))
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve2)
    r.update(method=spec, kappa=job[3], window=wf, scenario=sc.name, trigger=job[6])   # unscaled spec for --resume
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None)
    ap.add_argument("--name", default="b2")
    ap.add_argument("--split", default="dev", choices=["dev", "heldout"])
    ap.add_argument("--scales", default="small,medium,large")
    ap.add_argument("--exec", default="mid")
    ap.add_argument("--lat", default="high")
    ap.add_argument("--kappas", default="50")
    ap.add_argument("--windows", default="1")
    ap.add_argument("--triggers", default="event")
    ap.add_argument("--methods", default="alns_fixed@40,proposed")
    ap.add_argument("--ms-per-task", type=float, default=DEFAULT_MS_PER_TASK)
    ap.add_argument("--seeds", default=None, help="dev subset, e.g. 0-4")
    ap.add_argument("--quick", action="store_true", help="first 2 seeds only")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    seeds_override = None
    if args.config:
        y = yaml.safe_load(Path(args.config).read_text())
        for k, v in y.get("grid", {}).items():
            setattr(args, k.replace("-", "_"), ",".join(map(str, v)) if isinstance(v, list) else v)
        if args.split == "heldout":
            if not y.get("frozen"):
                sys.exit("held-out seeds need a config with `frozen: true`")
            seeds_override = y["heldout_seeds"]
    elif args.split == "heldout":
        sys.exit("held-out seeds need --config <frozen yaml>")
    if args.seeds and not seeds_override:
        a, _, b = args.seeds.partition("-")
        seeds_override = {"start": int(a), "n": int(b or a) - int(a) + 1}

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
        done = {(r["exec_level"], r["latency_level"], float(r["kappa"]), float(r["window"]), r["method"],
                 r["trigger"]) for r in rows}
    grid = []
    for xl in args.exec.split(","):
        for ll in args.lat.split(","):
            for k in args.kappas.split(","):
                for wf in args.windows.split(","):
                    for m in args.methods.split(","):
                        own = parse_method(m)[3]
                        for tr in ([own] if own else args.triggers.split(",")):
                            grid.append((xl, ll, float(k), float(wf), m, tr))
    print(f"[grid] {args.name}: {len(scen)} missions x {len(grid)} configurations, workers={args.workers}")
    print(f"[grid] env {env_info()}", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(args.workers, initializer=_init, initargs=(args.ms_per_task,)) as pool:
        for (xl, ll, k, wf, m, tr) in grid:
            if (xl, ll, k, wf, m, tr) in done:
                continue
            waited = 0
            while _busy():
                if not waited:
                    print(f"[guard] machine busy, waiting: {_busy()[0][:90]}", flush=True)
                time.sleep(30)
                waited += 30
            batch = pool.map(_one, [(sc, xl, ll, k, wf, m, tr, B) for sc in scen], chunksize=1)
            for r in batch:
                r["workers"] = args.workers
            rows += batch
            d = pd.DataFrame(batch)
            print(f"  {xl:4s} {ll:4s} k={k:>3g} w={wf:g} {m:34s} {tr:16s} U={d.utility_rate.mean():.4f} "
                  f"late={d.late_served.mean():5.2f} dropD={d.dropped_by_delay.mean():5.2f} "
                  f"dropX={d.dropped_in_exec.mean():5.2f} calls={d.n_replans.mean():5.1f} "
                  f"ms={d.plan_ms_mean.mean():6.1f} ({time.time() - t0:.0f}s)", flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    print(f"[ok] {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
