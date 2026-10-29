"""Study 4C: tier B counterpart of the tier C missions (scale "gz": three UAVs, rescaled), for the power calculation on
development seeds and for the tier B prediction of the held-out flights.

Same worker as experiments/b3_grid.py (rescaled disturbances, kappa and trigger times), with three differences:
options are separated by ";" (z and fb together), the tier C error model is models/error_model_tierc_dev4.json (the
frozen dev model plus the high level), and windows are tightened as in journal_ros/study4c.py.

    python experiments/b4c_gz.py --name dev4c_gz --split dev --scales gz --exec high --lat none --kappas 50 \
        --windows 0.5 --methods "proposed~z=0.5;fb=nominal+periodic:60,proposed~z=0.5+periodic:60,..."
"""
import copy
from dataclasses import replace

import b2_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, S_T, S_X, expected_latency, parse_method, \
    run_mission_kin, tighten_windows

from journal_core.study3 import solve3

_init0 = b2_grid._init


def _init(ms_per_task):
    _init0(ms_per_task)
    _W["err_gz"] = ErrorModel.load_all(b2_grid.ROOT / "models" / "error_model_tierc_dev4.json")


def _one(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    assert sc.scale == "gz"
    cfg, errs = _W["cfg_gz"], _W["err_gz"]
    xm = EXEC_LEVELS[xl]
    xm = replace(xm, wind_mps=xm.wind_mps * S_X / S_T, accel_mps2=xm.accel_mps2 * S_X / S_T ** 2)
    base, budget, opt, _ = parse_method(spec.replace(";", ","))
    kw = {"err": errs.get(xl, ErrorModel()), "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if "z" in opt else None, "ms_per_task": 1.0, "buf_s": None, "fb": opt.get("fb")}
    if "buf" in opt:
        kw["buf_s"] = float(opt["buf"]) * S_T
    kind, _, pars = trig.partition(":")
    if pars:
        trig = kind + ":" + ":".join(f"{float(x) * S_T:g}" for x in pars.split(":"))
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa * S_T, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve3)
    r.update(method=spec, kappa=kappa, window=wf, scenario=sc.name, trigger=job[6])
    return r


if __name__ == "__main__":
    b2_grid._init = _init
    b2_grid._one = _one
    b2_grid.main()
