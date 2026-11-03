"""Study 8c: tier B counterpart of the tier C missions (scale "gz": three UAVs, rescaled), with the planner of the tier C
manager journal_ros/study8c.py (journal_core.study8.solve8, explicit options, whole planning call timed). Used for the
pilot that sizes the flights (pilot seeds) and for the tier B prediction of the held-out flights.

Worker as experiments/b4c_gz.py: disturbances, kappa and trigger times rescaled to tier C, tier C error model
models/error_model_tierc_dev4.json, windows tightened as in tier C. Options are separated by ";".

    python experiments/b8c_gz.py --name pilot8c_gz --seeds 19000-19099 --scales gz --exec high --lat none \
        --kappas 50 --windows 0.5 --methods "alns_fixed@40~z=0.5;lam=1;cost=fee+periodic:60,..."
    python experiments/b8c_gz.py --config experiments/configs/S8c_B_gz.yaml --split heldout --resume
"""
import copy
from dataclasses import replace

import b2_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, S_T, S_X, parse_method, run_mission_kin, \
    tighten_windows

from journal_core.study8 import solve8, timing_columns, w_bar

_init0 = b2_grid._init


def _init(ms_per_task):
    _init0(ms_per_task)
    _W["err_gz"] = ErrorModel.load_all(b2_grid.ROOT / "models" / "error_model_tierc_dev4.json")


def _one(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    assert sc.scale == "gz"
    cfg = _W["cfg_gz"]
    err = _W["err_gz"].get(xl, ErrorModel())
    xm = EXEC_LEVELS[xl]
    xm = replace(xm, wind_mps=xm.wind_mps * S_X / S_T, accel_mps2=xm.accel_mps2 * S_X / S_T ** 2)
    base, budget, opt, _ = parse_method(spec.replace(";", ","))
    wb, log = w_bar(cfg), []

    def solver(b, P, old, bud, c, seed=0, predictor=None, kappa=1.0, **_kw):
        return solve8(b, P, old, bud, c, opt, err, wb, seed=seed, predictor=predictor, kappa=kappa, log=log)

    kind, _, pars = trig.partition(":")
    if pars:
        trig = kind + ":" + ":".join(f"{float(x) * S_T:g}" for x in pars.split(":"))
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa * S_T, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solver=solver)
    r.update(timing_columns(log, budget or B))
    r.update(method=spec, kappa=kappa, window=wf, scenario=sc.name, trigger=job[6])
    return r


if __name__ == "__main__":
    b2_grid._init = _init
    b2_grid._one = _one
    b2_grid.main()
