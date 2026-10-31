"""Study 5 grid: b4_grid with the cost-aware fallback of journal_core/study5.py.

Extra method options (separated by ";" as in b4_grid):
    ~z=auto4;lam=<x>        proposed model with the cost-aware fallback for a late cost of x task rewards
    ~prop=<c|auto>;fb=none  proportional buffer without fallback
All other options behave as in b4_grid (and b2_grid), so every method of study 4 can be run unchanged. Scoring with a
late cost is done in the analysis, u_lam = utility_rate - lam * late_served / n_tasks.

    python experiments/b5_grid.py --name dev5 --seeds 0-9 --exec mid,high --kappas 10,50,200 --windows 1,0.5 \
        --methods "alns_fixed@40~z=auto4;lam=1+periodic:60" --workers 4
    python experiments/b5_grid.py --config experiments/configs/S5_B.yaml --split heldout --resume
"""
import copy

import b2_grid
import b4_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, Z_BY_LEVEL, expected_latency, run_mission_kin, \
    tighten_windows
from b4_grid import RegisteringExecutor, _auto, coverage, parse4

from journal_core import study4
from journal_core.study4 import load_mp
from journal_core.study5 import solve5


def _one5(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    if sc.scale == "gz":
        raise NotImplementedError("study 5 tier B runs the kinematic scales only")
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    base, budget, opt, _ = parse4(spec)
    fb = opt.get("fb")
    kw = {"err": errs.get(opt.get("err", xl), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if opt.get("z", "auto") not in ("auto", "auto4") else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None}
    if opt.get("z") == "auto" or (base == "proposed" and "z" not in opt):
        kw["z"] = Z_BY_LEVEL[xl]
    if opt.get("z") == "auto4":
        kw["z"] = _auto(None, study4.Z4_BY_LEVEL, xl)
    if "lam" in opt:
        kw["lam"] = float(opt["lam"])
        if kw["z"] is None:
            raise ValueError(f"{spec}: the cost-aware fallback needs a safety factor ~z")
    elif "prop" in opt and fb == "none":
        kw["prop_nofb"] = _auto(opt["prop"], study4.PROP_BY_LEVEL, xl)
    else:
        kw["fb"] = fb
        if "prop" in opt:
            kw["prop"] = _auto(opt["prop"], study4.PROP_BY_LEVEL, xl)
        if "mp" in opt:
            kw["mp"] = _W.setdefault("mp", load_mp())[xl]
            kw["z_mp"] = _auto(opt["mp"], study4.ZMP_BY_LEVEL, xl)
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve5, keep_log=True)
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
    b2_grid._one = _one5
    b2_grid.main()
