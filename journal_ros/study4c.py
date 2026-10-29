#!/usr/bin/env python3
"""Study 4C: tier C nodes with the nominal fallback (study 3) and tightened time windows, without editing the frozen
study-2 nodes.

    python journal_ros/study4c.py manager  <mission_manager.py arguments>
    python journal_ros/study4c.py executor <uav_executor.py arguments>

The window factor is read from ATSWARM_WINDOW (default 1). Before the frozen node is imported, common.gz_scenario is
replaced by the same scenario with every time window multiplied by that factor (journal_core.study2.tighten_windows,
as in tier B), so the manager and the executor see the same deadlines. In the manager, a method with the option
fb=<nominal|s> is planned by journal_core.study3.solve3 (fallback model); every other method runs unchanged.
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
        from journal_core.study3 import solve3

        fb = parse_method(_method_from_argv())[2].get("fb")
        if fb is not None:
            def solve_fb(base, P, old, budget, cfg, **kw):
                if kw.get("buf_s") is None and fb != "nominal":
                    fb_s = f"{float(fb) * common.S_T:g}"   # fallback buffer given in tier B seconds
                else:
                    fb_s = fb
                return solve3(base, P, old, budget, cfg, fb=fb_s, **kw)
            mm.solve2 = solve_fb
        if os.environ.get("ATSWARM_DRYRUN"):          # self-check: report the planner the manager will call
            print(f"window={WF} fb={fb} planner={mm.solve2.__name__} gz={mm.gz_scenario.__module__}")
            sys.exit(0)
        mm.main()
    elif role == "executor":
        import uav_executor as ux
        ux.main()
    else:
        sys.exit(f"unknown role {role}")
