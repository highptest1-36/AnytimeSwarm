"""Study 7 grid (journal_core/study7.py): late-cost model of the cost-aware fallback (7a) and execution errors outside
the calibrated model (7b).

Method options (separated by ";" as in b4_grid):
    ~z=auto4;lam=<x>;cost=fee    cost-aware fallback with a fixed late cost per task (theta_j per task)
    ~z=auto4;lam=<x>             cost-aware fallback with a late cost proportional to the reward (study 5)
    ~mp=auto;lam=<x>             moment propagation with the cost-aware fallback (study 6)
    ~prop=<c|auto>;fb=none       proportional buffer without fallback (study 5)
All other options behave as in b4/b5/b6_grid. Execution levels high_gauss, high_t3, high_outlier, high_uavbias and the
latency level high_pareto (study 7b) use the error model, safety factors and expected latency of the calibrated
"high" level. Every run also reports the total, on-time and late reward (score u_prop) and the Brier score of the
predicted probability of meeting the deadline.

    python experiments/b7_grid.py --name dev7a --seeds 0-9 --exec mid,high --lat high --kappas 10,50,200 \
        --windows 1,0.5 --methods "alns_fixed@40~z=auto4;lam=1;cost=fee+periodic:60" --workers 4
    python experiments/b7_grid.py --config experiments/configs/S7a_B.yaml --split heldout --resume
"""
import copy

import b2_grid
import b4_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, Z_BY_LEVEL, expected_latency, run_mission_kin, \
    tighten_windows
from b4_grid import RegisteringExecutor, _auto, coverage, parse4

from journal_core import study4
from journal_core.study4 import load_mp
from journal_core.study7 import brier_columns, reward_columns, shifted_levels, solve7

_ex, _lat = shifted_levels(EXEC_LEVELS, LATENCY_LEVELS)
EXEC_LEVELS.update(_ex)          # same dict objects as in b2_grid, so the grid loop finds the new levels
LATENCY_LEVELS.update(_lat)


def base_level(name: str) -> str:
    """Calibrated level whose error model and tuned parameters a (shifted) level uses."""
    return name.split("_")[0]


def w_bar(cfg) -> float:
    w = cfg["world"]
    return float(sum(a * b for a, b in zip(w["reward_levels"], w["reward_probs"])))


def _one7(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    if sc.scale == "gz":
        raise NotImplementedError("study 7 tier B runs the kinematic scales only")
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    lv = base_level(xl)
    base, budget, opt, _ = parse4(spec)
    fb = opt.get("fb")
    kw = {"err": errs.get(opt.get("err", lv), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[base_level(ll)]),
          "z": float(opt["z"]) if opt.get("z", "auto") not in ("auto", "auto4") else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None}
    if opt.get("z") == "auto" or (base == "proposed" and "z" not in opt):
        kw["z"] = Z_BY_LEVEL[lv]
    if opt.get("z") == "auto4":
        kw["z"] = _auto(None, study4.Z4_BY_LEVEL, lv)
    if "lam" in opt:
        kw["lam"] = float(opt["lam"])
        kw["cost"] = opt.get("cost", "prop")
        kw["w_bar"] = w_bar(cfg)
    if "mp" in opt:
        kw["mp"] = _W.setdefault("mp", load_mp())[lv]
        kw["z_mp"] = _auto(opt["mp"], study4.ZMP_BY_LEVEL, lv)
        if "lam" not in opt:
            kw["fb"] = fb
    elif "lam" in opt:
        if kw["z"] is None and base != "cbba":
            raise ValueError(f"{spec}: the cost-aware fallback needs a safety factor ~z")
    elif "prop" in opt and fb == "none":
        kw["prop_nofb"] = _auto(opt["prop"], study4.PROP_BY_LEVEL, lv)
    else:
        kw["fb"] = fb
        if "prop" in opt:
            kw["prop"] = _auto(opt["prop"], study4.PROP_BY_LEVEL, lv)
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve7, keep_log=True)
    rep = r.pop("_replans")
    for k in [k for k in r if k.startswith("_")]:
        r.pop(k)
    it = sum(x["iters"] for x in rep)
    ms = sum(x["elapsed_ms"] for x in rep)
    r.update(iters_mean=it / max(len(rep), 1), iters_per_ms=it / ms if ms > 0 else 0.0)
    ex, err = RegisteringExecutor.current, errs.get(lv, ErrorModel())
    r.update(coverage(ex, err))
    r.update(brier_columns(ex, err))
    r.update(reward_columns(ex))
    r.update(method=spec, kappa=job[3], window=wf, scenario=sc.name, trigger=job[6], exec_level=xl)
    return r


if __name__ == "__main__":
    assert b4_grid.kx.KinematicExecutor is RegisteringExecutor
    b2_grid._one = _one7
    b2_grid.main()
