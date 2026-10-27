"""Print a few tier B missions side by side (deterministic planner, kappa = 0) - sanity check, not an experiment."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS, LATENCY_LEVELS  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402

from anytimeswarm.simulator.executor import run_mission  # noqa: E402
from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
DET = {"max_iters": 60}
KEYS = ["n_replans", "served", "utility_rate", "late_served", "dropped_by_delay", "dropped_in_exec",
        "finish_err_mean_s", "finish_err_p95_s", "energy_violations", "latency_s_mean"]

for scale, profile, seed in [("medium", "arrivals", 1), ("medium", "deadlines", 4)]:
    sc = generate_scenario(CFG, scale, profile, seed)
    a = run_mission(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs=DET)
    print(f"\n{sc.name}  conference executor: served={a['served']} utility={a['utility_rate']:.3f} "
          f"late={a['late_served']} dropped_by_delay={a['dropped_by_delay']}")
    for lv in ["nominal", "low", "mid", "high"]:
        for lt in (["none"] if lv == "nominal" else ["none", "high"]):
            m = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 1e9, kappa=0.0, seed=seed, solve_kwargs=DET,
                                xm=EXEC_LEVELS[lv], lat=LATENCY_LEVELS[lt])
            print(f"  exec={lv:7s} lat={lt:4s} " + " ".join(
                f"{k}={m[k]:.3f}" if isinstance(m[k], float) else f"{k}={m[k]}" for k in KEYS))
