"""Study 6 grid: b5_grid with CBBA and moment propagation with the cost-aware fallback (journal_core/study6.py).

Method options (separated by ";" as in b4_grid):
    cbba[+trigger]                      CBBA on the nominal model (Choi, Brunet and How 2009)
    cbba~z=auto4;lam=<x>[+trigger]      CBBA on the proposed model with the cost-aware fallback
    <base>~mp=auto;lam=<x>[+trigger]    moment propagation with the cost-aware fallback
All other options behave as in b5_grid, so every method of studies 4 and 5 can be run unchanged.

    python experiments/b6_grid.py --name dev6 --split dev --exec mid,high --lat high --kappas 10,50,200 \
        --windows 1,0.5 --methods "cbba+periodic:60" --workers 8
    python experiments/b6_grid.py --config experiments/configs/S6_B.yaml --split heldout --resume
"""
import copy

import b2_grid
import b4_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, expected_latency, run_mission_kin, tighten_windows
from b4_grid import RegisteringExecutor, _auto, coverage, parse4

from journal_core import study4
from journal_core.study4 import load_mp
from journal_core.study6 import solve6


def _one6(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    if sc.scale == "gz":
        raise NotImplementedError("study 6 tier B runs the kinematic scales only")
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    base, budget, opt, _ = parse4(spec)
    kw = {"err": errs.get(opt.get("err", xl), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if opt.get("z", "auto") not in ("auto", "auto4") else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None}
    if opt.get("z") == "auto4":
        kw["z"] = _auto(None, study4.Z4_BY_LEVEL, xl)
    if "lam" in opt:
        kw["lam"] = float(opt["lam"])
    if "mp" in opt:
        kw["mp"] = _W.setdefault("mp", load_mp())[xl]
        kw["z_mp"] = _auto(opt["mp"], study4.ZMP_BY_LEVEL, xl)
        if "lam" not in opt:
            kw["fb"] = opt.get("fb")
    elif "lam" in opt and kw["z"] is None:
        raise ValueError(f"{spec}: the cost-aware fallback needs a safety factor ~z")
    elif "lam" not in opt:
        kw["fb"] = opt.get("fb")
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve6, keep_log=True)
    rep = r.pop("_replans")
    for k in [k for k in r if k.startswith("_")]:
        r.pop(k)
    it = sum(x["iters"] for x in rep)
    ms = sum(x["elapsed_ms"] for x in rep)
    r.update(iters_mean=it / max(len(rep), 1), iters_per_ms=it / ms if ms > 0 else 0.0)
    r.update(coverage(RegisteringExecutor.current, errs.get(xl, ErrorModel())))
    r.update(method=spec, kappa=job[3], window=wf, scenario=sc.name, trigger=job[6])
    return r


if __name__ == "__main__":
    assert b4_grid.kx.KinematicExecutor is RegisteringExecutor
    b2_grid._one = _one6
    b2_grid.main()
