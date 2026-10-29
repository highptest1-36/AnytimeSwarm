"""Study 4 grid: b2_grid with the planning models of journal_core/study4.py.

Options are separated by ";" instead of "," (b2_grid splits the method list at commas), e.g.
alns_fixed@40~prop=0.2;fb=nominal+periodic:60. Extra method options (with fb=nominal as in study 3):
    ~prop=<c|auto>     buffer proportional to the lead time, f + c h <= d
    ~mp=<z|auto>       moment propagation with safety factor z (arc model models/mp_model_dev.json)
    ~online=<n0|auto>  error model refitted online, prior weight n0 pairs, common safety factor ~z (or auto)
~z=auto4 is the safety factor of the proposed model re-selected with the fallback. "auto" takes the value selected on development missions (journal_core.study4). Every run also reports the iterations
per planning millisecond and a reliability check of the error model of its disturbance level: executed tasks binned
by the predicted probability Phi((d - f - m(h)) / s(h)) of meeting the deadline (columns cov_n*, cov_k*, cov_p*).
Everything else (scenarios, seeds, guard, output, --resume) is that of experiments/b2_grid.py, reused unchanged.

    python experiments/b4_grid.py --name dev4_prop --exec mid,high --kappas 10,50,200 --windows 1,0.5 \
        --methods "alns_fixed@40~prop=0.1;fb=nominal+periodic:60" --workers 4
    python experiments/b4_grid.py --config experiments/configs/S4_B.yaml --split heldout --resume
"""
import copy

import numpy as np
from scipy.special import ndtr

import b2_grid
from b2_grid import _W, EXEC_LEVELS, LATENCY_LEVELS, ErrorModel, Z_BY_LEVEL, expected_latency, parse_method, \
    run_mission_kin, tighten_windows

from journal_core import kinematic_executor as kx
from journal_core import study4
from journal_core.study4 import RegisteringExecutor, load_mp, solve4

kx.KinematicExecutor = RegisteringExecutor        # run_mission_kin builds its executor from this module name
COV_BINS = np.linspace(0.0, 1.0, 11)


def _auto(v, table, key):
    if v not in (None, "auto"):
        return float(v)
    x = table[key]
    if x is None:
        raise RuntimeError(f"no development value selected yet for {key}")
    return float(x)


def coverage(ex, err: ErrorModel) -> dict:
    """Executed tasks binned by the predicted probability of meeting the deadline at their last publication."""
    p, ok = [], []
    for (_u, j, _d, _s, fin) in ex.executed:
        if j not in ex.plan_lead:
            continue
        t_pub, f = ex.plan_lead[j]
        h = f - t_pub
        d = ex.tasks[j].deadline
        sd = float(err.sd(h))
        p.append(float(ndtr((d - f - err.mean(h)) / sd)) if sd > 0 else float(d - f - err.mean(h) >= 0))
        ok.append(fin <= d + 1e-9)
    p, ok = np.asarray(p), np.asarray(ok, float)
    b = np.clip(np.digitize(p, COV_BINS[1:-1]), 0, 9)
    out = {}
    for i in range(10):
        s = b == i
        out[f"cov_n{i}"] = int(s.sum())
        out[f"cov_k{i}"] = float(ok[s].sum())
        out[f"cov_p{i}"] = float(p[s].sum())
    return out


def parse4(spec: str):
    """parse_method with ";" between the options."""
    return parse_method(spec.replace(";", ","))


def _one4(job):
    sc, xl, ll, kappa, wf, spec, trig, B = job
    if sc.scale == "gz":
        raise NotImplementedError("study 4 tier B runs the kinematic scales only")
    cfg, xm, errs = _W["cfg"], EXEC_LEVELS[xl], _W["err"]
    base, budget, opt, _ = parse4(spec)
    kw = {"err": errs.get(opt.get("err", xl), ErrorModel()),
          "latency_mean_s": expected_latency(LATENCY_LEVELS[ll]),
          "z": float(opt["z"]) if opt.get("z", "auto") not in ("auto", "auto4") else None,
          "ms_per_task": float(opt.get("ms", _W["ms_per_task"])),
          "buf_s": float(opt["buf"]) if "buf" in opt else None,
          "fb": opt.get("fb")}
    if opt.get("z") == "auto" or (base == "proposed" and "z" not in opt):
        kw["z"] = Z_BY_LEVEL[xl]
    if opt.get("z") == "auto4":                    # safety factor re-selected with the fallback (study 4 dev)
        kw["z"] = _auto(None, study4.Z4_BY_LEVEL, xl)
    if "prop" in opt:
        kw["prop"] = _auto(opt["prop"], study4.PROP_BY_LEVEL, xl)
    if "mp" in opt:
        kw["mp"] = _W.setdefault("mp", load_mp())[xl]
        kw["z_mp"] = _auto(opt["mp"], study4.ZMP_BY_LEVEL, xl)
    if "online" in opt:
        kw["online_n0"] = _auto(opt["online"], study4.ONLINE, "n0")
        kw["z"] = float(opt["z"]) if opt.get("z", "auto") not in ("auto", "auto4") else _auto(None, study4.ONLINE, "z")
    r = run_mission_kin(tighten_windows(copy.deepcopy(sc), wf), cfg, base, budget or B, kappa=kappa, xm=xm,
                        lat=LATENCY_LEVELS[ll], predictor=_W["pred"], seed=sc.seed, trigger=trig, solve_kwargs=kw,
                        solver=solve4, keep_log=True)
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
    b2_grid._one = _one4          # the pool is forked after this assignment, so the workers see the new worker
    b2_grid.main()
