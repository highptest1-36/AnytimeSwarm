"""Study 8 grid (journal_core/study8.py): planning budget (8a) and the emergency-response scenario family (8b).

Worker: experiments/b7_grid._one7, unchanged, with two additions. The solver is timed over the whole planning call
(study8.timed: the publication delay runs from the construction of the planning model to the return of the solver,
the search time is kept separately), and every run reports the timing of its calls (call_ms_mean/p50/p95/p99/max,
search_ms_mean, model_ms_mean, repair_ms_mean, iters_per_search_ms, over_ms_mean/p99 = time above the budget,
n_calls). The scales small8, medium8 and large8 are missions of the emergency-response family (study8.generate_scenario8, tasks per scale x LOAD8;
the environment variable ATSWARM_LOAD8 overrides LOAD8 for the load selection on development seeds only); runs on
them also report the urgent tasks served on time and late (n_urgent, urgent_on_time, urgent_late). The conference
scales and everything else (method grammar, seeds, guard, output, --resume) are those of b7_grid / b2_grid.

    ATSWARM_LOAD8=1.0 python experiments/b8_grid.py --name dev8_load_1.0 --seeds 0-9 --scales small8,medium8,large8 \
        --exec nominal --lat none --kappas 10 --windows 1 --methods "alns_fixed@40+periodic:60" --workers 4
    python experiments/b8_grid.py --config experiments/configs/S8a_B.yaml --split heldout --resume
"""
import os

import b2_grid
import b7_grid
from b4_grid import RegisteringExecutor, parse4

from journal_core.study7 import solve7
from journal_core.study8 import SCALES8, is_urgent, scenarios8, timed, timing_columns

_LOG = []
b7_grid.solve7 = timed(solve7, _LOG)      # _one7 looks the solver up by this module name at call time
_scen0 = b2_grid.scenarios
LOAD = float(os.environ["ATSWARM_LOAD8"]) if os.environ.get("ATSWARM_LOAD8") else None


def scenarios(cfg, split, scales, seeds_override=None):
    """Conference scales as before; small8/medium8/large8 from the emergency-response family."""
    fam = [s for s in scales if s in SCALES8]
    rest = [s for s in scales if s not in SCALES8]
    out = _scen0(cfg, split, rest, seeds_override) if rest else []
    if fam:
        out += scenarios8(cfg, seeds_override or cfg["seeds"][split], fam, LOAD)
    return out


def urgent_columns(ex, wf: float) -> dict:
    urg = {t.id for t in ex.sc.tasks if is_urgent(t, wf)}
    return {"n_urgent": len(urg), "urgent_on_time": len(urg & set(ex.served)), "urgent_late": len(urg & ex.late)}


def _one8(job):
    sc, wf, spec, B = job[0], job[4], job[5], job[7]
    _LOG.clear()
    r = b7_grid._one7(job)
    r.update(timing_columns(_LOG, parse4(spec)[1] or B))
    if sc.scale in SCALES8:
        r.update(urgent_columns(RegisteringExecutor.current, wf))
    return r


if __name__ == "__main__":
    b2_grid.scenarios = scenarios
    b2_grid._one = _one8
    b2_grid.main()
