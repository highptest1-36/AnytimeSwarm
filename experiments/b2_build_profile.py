#!/usr/bin/env python3
"""Static performance profile for the ProfileStop baseline (journal_core.study2), from DEVELOPMENT seeds only.

    python experiments/b2_build_profile.py            # -> models/performance_profile_dev.json

Every planning call of the 90 development missions (seeds 0-9, three scales, three profiles, mid disturbances,
kappa_B = 10, event trigger) is run with the full 250 ms budget. The profile is the mean improvement of the best
objective over the next H = 10 ms, in fractions of the reward scale, per elapsed time (5 ms grid) and per size class of
the number of open tasks. The same frozen ALNS as all other methods is used.
"""
import copy
import json
import sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402
from journal_core.study2 import PROFILE_FILE, solve2  # noqa: E402

from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

FROZEN_CFG = ORIGINAL / "configs" / "frozen_2026-10-24.yaml"
T_GRID = np.arange(0.0, 250.0 + 1e-9, 5.0)
N_EDGES = [0, 10, 20, 40, 80]                       # size classes: [0,10), [10,20), [20,40), [40,80), [80,inf)
H = 10.0


def _calls(sc):
    cfg = load_config(FROZEN_CFG)
    rec = []

    def solver(method, P, old, budget_ms, cfg_, **kw):
        kw.pop("predictor", None)
        r = solve2("alns_fixed", P, old, budget_ms, cfg_, seed=kw.get("seed", 0), kappa=kw.get("kappa", 1.0))
        if r["trace"] is not None and P.N > 0:
            imp = [(t, J) for (t, _it, J, _u) in r["trace"]["imp"]]
            rec.append((P.N, P.scale, r["J0"], imp))
        return r

    run_mission_kin(copy.deepcopy(sc), cfg, "alns_fixed", 250.0, kappa=10.0, xm=EXEC_LEVELS["mid"],
                    lat=LATENCY_LEVELS["none"], seed=sc.seed, solver=solver)
    return rec


def main():
    cfg = load_config(FROZEN_CFG)
    scen = [generate_scenario(cfg, s, p, seed) for s in ("small", "medium", "large") for p in cfg["profiles"]
            for seed in range(cfg["seeds"]["dev"]["start"], cfg["seeds"]["dev"]["start"] + cfg["seeds"]["dev"]["n"])]
    with get_context("fork").Pool(4) as pool:
        calls = [c for r in pool.map(_calls, scen, chunksize=1) for c in r]
    gain = np.zeros((len(N_EDGES), T_GRID.size))
    count = np.zeros(len(N_EDGES))
    for n, scale, J0, imp in calls:
        ts = np.array([0.0] + [t for t, _ in imp])
        Js = np.array([J0] + [J for _, J in imp])

        def J_at(t):
            return Js[np.searchsorted(ts, t, side="right") - 1]

        row = int(np.searchsorted(N_EDGES, n, side="right")) - 1
        gain[row] += (np.array([J_at(t + H) for t in T_GRID]) - np.array([J_at(t) for t in T_GRID])) / scale
        count[row] += 1
    gain /= np.maximum(count, 1)[:, None]
    PROFILE_FILE.write_text(json.dumps({"t_ms": T_GRID.tolist(), "n_edges": N_EDGES, "horizon_ms": H,
                                        "gain_frac": gain.tolist(), "calls_per_class": count.tolist(),
                                        "source": "dev seeds 0-9, small/medium/large, mid, kappa_B 10, event"},
                                       indent=1))
    print(f"{len(calls)} planning calls; per size class {count.tolist()} -> {PROFILE_FILE}")
    for r, n in zip(gain, N_EDGES):
        print(f"  N>={n:3d}: gain at 0/20/50/100/200 ms = " +
              " ".join(f"{r[int(t / 5)]:.2e}" for t in (0, 20, 50, 100, 200)))


if __name__ == "__main__":
    main()
