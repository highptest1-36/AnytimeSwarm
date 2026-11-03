#!/usr/bin/env python3
"""Study 8c: tier C nodes with the planners of study 8, without editing the frozen nodes.

    python journal_ros/study8c.py manager  <mission_manager.py arguments>
    python journal_ros/study8c.py executor <uav_executor.py arguments>

The window factor is read from ATSWARM_WINDOW (default 1) and applied to common.gz_scenario before the frozen nodes
are imported, as in journal_ros/study4c.py, so the manager and the executor see the same deadlines. In the manager, a
method with options (~...) is planned by journal_core.study8.solve8 with its explicit options: cost-aware fallback
(z, lam, cost), nominal fallback (z, fb=nominal), proportional buffer without fallback (prop, fb=none). As in tier B
(experiments/b8c_gz.py), the publication delay charges the whole planning call (journal_core.study8.timed).
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
from journal_core.study2 import parse_method, tighten_windows  # noqa: E402

WF = float(os.environ.get("ATSWARM_WINDOW", "1"))
_gz = common.gz_scenario


def gz_scenario(profile, seed):
    return tighten_windows(_gz(profile, seed), WF)


common.gz_scenario = gz_scenario


def _method_from_argv() -> str:
    argv = sys.argv
    return argv[argv.index("--method") + 1] if "--method" in argv else "anytime"


if __name__ == "__main__":
    role = sys.argv.pop(1)
    if role == "manager":
        import mission_manager as mm
        from journal_core.study8 import solve8, solve8_kwargs, w_bar

        opt = parse_method(_method_from_argv())[2]
        if opt:
            def solve_8c(base, P, old, budget, cfg, seed=0, predictor=None, kappa=1.0, err=None, latency_mean_s=0.0,
                         **_kw):
                return solve8(base, P, old, budget, cfg, opt, err, w_bar(cfg), seed=seed, predictor=predictor,
                              kappa=kappa, latency_mean_s=latency_mean_s)
            mm.solve2 = solve_8c
        if os.environ.get("ATSWARM_DRYRUN"):          # self-check: report the planner the manager will call
            cfg = common.tier_c_config()
            kw = {k: v for k, v in solve8_kwargs(opt, None, w_bar(cfg)).items() if k != "err"} if opt else {}
            print(f"window={WF} opt={opt} solve7 kwargs={kw} planner={mm.solve2.__name__} "
                  f"gz={mm.gz_scenario.__module__}")
            sys.exit(0)
        mm.main()
    elif role == "executor":
        import uav_executor as ux
        ux.main()
    else:
        sys.exit(f"unknown role {role}")
