"""Study 3 grid: b2_grid with the fallback planning model (journal_core/study3.py).

Method specs accept the extra option fb=<nominal|seconds>, e.g. proposed~fb=nominal+periodic:60. Everything else
(scenarios, seeds, error models, guard, output format, --resume) is that of experiments/b2_grid.py, which is frozen
for study 2 and therefore reused unchanged: only its per-mission worker is replaced.

    python experiments/b3_grid.py --name dev3 --exec mid,high --kappas 10,50,200 --windows 1,0.5 \
        --methods "proposed+periodic:60,proposed~fb=nominal+periodic:60"
    python experiments/b3_grid.py --config experiments/configs/S3_B.yaml --split heldout --name s3_heldout_B
"""
import copy
from dataclasses import replace

import b2_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, S_T, S_X, Z_BY_LEVEL, expected_latency, \
    parse_method, run_mission_kin, tighten_windows

from journal_core.study3 import solve3


def _one3(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    if sc.scale == "gz":
        cfg, errs = _W["cfg_gz"], _W["err_gz"]
        xm = replace(xm, wind_mps=xm.wind_mps * S_X / S_T, accel_mps2=xm.accel_mps2 * S_X / S_T ** 2)
        kappa = kappa * S_T
    base, budget, opt, _ = parse_method(spec)
    kw = {"err": errs.get(opt.get("err", xl), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if opt.get("z", "auto") != "auto" else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None,
          "fb": opt.get("fb")}
    if opt.get("z") == "auto" or (base == "proposed" and "z" not in opt):
        kw["z"] = Z_BY_LEVEL[xl]
    if sc.scale == "gz":
        if kw["buf_s"] is not None:
            kw["buf_s"] *= S_T
        if kw["fb"] not in (None, "nominal"):
            kw["fb"] = f"{float(kw['fb']) * S_T:g}"
        kind, _, pars = trig.partition(":")
        if pars:
            trig = kind + ":" + ":".join(f"{float(x) * S_T:g}" for x in pars.split(":"))
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve3)
    r.update(method=spec, kappa=job[3], window=wf, scenario=sc.name, trigger=job[6])
    return r


if __name__ == "__main__":
    b2_grid._one = _one3          # the pool is forked after this assignment, so the workers see the new worker
    b2_grid.main()
