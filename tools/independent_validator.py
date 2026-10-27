#!/usr/bin/env python3
"""Independent feasibility validator (G0 criterion): re-checks plans WITHOUT using Problem.route_eval / schedule.

    python tools/independent_validator.py [--snapshots repro/data/snapshots_dev.pkl] [--max-iters 300]

For every DEV snapshot, every planner of the registry is run (ALNS variants with a fixed iteration cap, so the
check is deterministic and does not depend on CPU speed) and the returned routes are checked from the raw problem
data with separately written arithmetic:
  * every task index is valid, appears at most once, and is not on two UAVs
  * arrival = previous finish + euclidean distance / speed; start = max(arrival, release); finish = start + service
  * finish <= deadline (1e-6 s tolerance)
  * energy: e0 - flown metres - hover * service - return-to-depot >= reserve (1e-6 m tolerance)
Writes results/g0/validator.txt.
"""
import argparse
import math
import pickle
import sys
from collections import Counter
from pathlib import Path

J = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(J / "repro"))
from anytimeswarm.algorithms.methods import solve  # noqa: E402
from anytimeswarm.controller.improvement_model import LearnedPredictor  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

TOL_T, TOL_E = 1e-6, 1e-6
METHODS = ["greedy_repair", "regret_repair", "ls_fixed", "alns_fixed", "alns_stagnation", "anytime",
           "anytime_online", "anytime_nodelay", "anytime_noffr"]


def check(P, routes) -> list[str]:
    errs, seen = [], Counter()
    depot = P.depot
    for k, route in enumerate(routes):
        x, y = float(P.start_xy[k][0]), float(P.start_xy[k][1])
        t, e = P.ready[k], P.energy[k]
        for j in route:
            if not (0 <= j < P.N):
                errs.append(f"uav {k}: invalid task index {j}")
                continue
            seen[j] += 1
            tx, ty = float(P.task_xy[j][0]), float(P.task_xy[j][1])
            d = math.hypot(tx - x, ty - y)
            arrive = t + d / P.speed[k]
            start = arrive if arrive > P.rel[j] else P.rel[j]
            finish = start + P.sv[j]
            if finish > P.dl[j] + TOL_T:
                errs.append(f"uav {k} task {j}: finish {finish:.3f} > deadline {P.dl[j]:.3f}")
            e -= d + P.hover * P.sv[j]
            x, y, t = tx, ty, finish
        back = math.hypot(depot[0] - x, depot[1] - y)
        if e - back < P.reserve[k] - TOL_E:
            errs.append(f"uav {k}: energy {e - back:.3f} below reserve {P.reserve[k]:.3f}")
    errs += [f"task {j} assigned {n} times" for j, n in seen.items() if n > 1]
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", default=str(J / "repro" / "data" / "snapshots_dev.pkl"))
    ap.add_argument("--max-iters", type=int, default=300)
    args = ap.parse_args()
    cfg = load_config(J / "repro" / "configs" / "frozen_2026-10-24.yaml")
    pred = LearnedPredictor.load(J / "original" / "models" / "improvement_model.json")
    with open(args.snapshots, "rb") as f:
        snaps = pickle.load(f)
    n_plans, bad = 0, []
    per_method = Counter()
    for i, s in enumerate(snaps):
        for m in METHODS:
            kw = {} if m in ("greedy_repair", "regret_repair", "ls_fixed") else {"max_iters": args.max_iters}
            res = solve(m, s["P"], s["old"], 1e9 if kw else 50.0, cfg, seed=i, predictor=pred, kappa=1.0,
                        check=False, **kw)
            errs = check(s["P"], res["solution"].routes)
            n_plans += 1
            per_method[m] += 1
            if errs:
                bad.append((i, m, errs[:3]))
    lines = [f"independent validator: {len(snaps)} snapshots x {len(METHODS)} methods = {n_plans} plans "
             f"(ALNS variants capped at {args.max_iters} iterations)",
             f"infeasible plans: {len(bad)}"]
    lines += [f"  snap {i} {m}: {e}" for i, m, e in bad[:20]]
    out = J / "results" / "g0" / "validator.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
