#!/usr/bin/env python3
"""Study 4, part 1: structure of the finish-time error on DEVELOPMENT missions only (seeds 0-9).

    python experiments/b4_error_structure.py collect [--levels mid,high] [--workers 4]
    python experiments/b4_error_structure.py analyse
    python experiments/b4_error_structure.py legs [--levels mid,high]

collect: the 90 dev missions per level are flown exactly as in experiments/b2_calibrate_errors.py (ALNS 40 ms, event
trigger, kappa = 1, no latency), but every pair (lead time h, error e) keeps its mission, so that the error can be
decomposed into a mission effect and a within-mission part. Output: results/tier_b/dev4_errpairs.csv.

analyse: Gaussian maximum likelihood with the mean b0 + b1 h for three spread models
    affine     sd(h) = s0 + s1 h                    (planning model of the proposed replanner)
    sqrt       sd(h) = sqrt(q0 + q1 h)              (independent increments, moment propagation)
    hybrid     sd(h) = sqrt(q0 + q1 h + q2 h^2)     (mission effect + independent increments)
compared by AIC and by the out-of-sample log-likelihood of a 5-fold cross-validation grouped by mission, plus a
random-effects decomposition (per-mission least-squares slope). Output: results/tier_b/dev4_errstructure.json and
dev4_errbins.csv (binned spread against the three fits).
"""
import argparse
import copy
import json
import sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from journal_core import ORIGINAL  # noqa: E402
from journal_core.execution import EXEC_LEVELS  # noqa: E402
from journal_core import kinematic_executor as kx  # noqa: E402
from journal_core.kinematic_executor import run_mission_kin  # noqa: E402

from anytimeswarm.simulator.scenario import generate_scenario  # noqa: E402
from anytimeswarm.utils import load_config  # noqa: E402

CFG = load_config(ORIGINAL / "configs" / "frozen_2026-10-24.yaml")
OUT = ROOT / "results" / "tier_b"


def _pairs_with_uav(self):
    """calibration_pairs of the executor, with the UAV and its cruise airspeed (the frozen file is not modified)."""
    out = []
    for (u, j, _d, _s, fin) in self.executed:
        if j in self.plan_lead:
            t_pub, p = self.plan_lead[j]
            out.append((p - t_pub, fin - p, u, self.uav[u]["speed"], t_pub, p))
    return out


def _fly(job):
    sc, lv = job
    m = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 40.0, kappa=1.0, xm=EXEC_LEVELS[lv], seed=sc.seed,
                        keep_log=True)
    return [{"level": lv, "mission": sc.name, "scale": sc.scale, "uav": f"{sc.name}/{u}", "speed": v, "t_pub": tp,
             "f_plan": f, "h": h, "e": e} for h, e, u, v, tp, f in m["_calib"]]


def collect(levels, workers):
    s = CFG["seeds"]["dev"]
    scen = [generate_scenario(CFG, sc, pr, seed) for sc in CFG["scales"] for pr in CFG["profiles"]
            for seed in range(s["start"], s["start"] + s["n"])]
    kx.KinematicExecutor.calibration_pairs = _pairs_with_uav
    rows = []
    with get_context("fork").Pool(workers) as pool:
        for lv in levels:
            for r in pool.map(_fly, [(sc, lv) for sc in scen], chunksize=1):
                rows += r
            print(f"[collect] {lv}: {sum(r['level'] == lv for r in rows)} pairs", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "dev4_errpairs.csv", index=False)


def _fly_legs(job):
    """Per-leg data of the same dev flights: nominal and actual flight time, waiting, nominal and actual service."""
    sc, lv = job
    m = run_mission_kin(copy.deepcopy(sc), CFG, "alns_fixed", 40.0, kappa=1.0, xm=EXEC_LEVELS[lv], seed=sc.seed,
                        keep_log=True)
    speed = {u.id: u.speed for u in sc.uavs}
    task = {x.id: x for x in sc.tasks}
    rows = []
    for (u, j, x0, y0, x1, y1, dep, arr, start, fin) in m["_trajectory"]:
        tk = task[j]
        rows.append({"level": lv, "mission": sc.name, "uav": f"{sc.name}/{u}", "t_nom": np.hypot(x1 - x0, y1 - y0)
                     / speed[u], "t_act": arr - dep, "wait": start - arr, "s_nom": tk.service, "s_act": fin - start})
    return rows


def legs(levels, workers):
    """Arc-level calibration of the moment-propagation baseline (journal_core/study4.MPModel), dev missions only:
    flight time = (1 + a) t + c + N(0, (cv t)^2), service = (1 + a_s) s + N(0, (cv_s s)^2)."""
    s = CFG["seeds"]["dev"]
    scen = [generate_scenario(CFG, sc, pr, seed) for sc in CFG["scales"] for pr in CFG["profiles"]
            for seed in range(s["start"], s["start"] + s["n"])]
    rows = []
    with get_context("fork").Pool(workers) as pool:
        for lv in levels:
            for r in pool.map(_fly_legs, [(sc, lv) for sc in scen], chunksize=1):
                rows += r
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "dev4_legs.csv", index=False)
    models = {}
    for lv, g in df.groupby("level"):
        g = g[g.t_nom > 1.0]
        t, y = g.t_nom.to_numpy(), g.t_act.to_numpy()
        A = np.c_[np.ones_like(t), t]
        c, a1 = np.linalg.lstsq(A, y, rcond=None)[0]
        r = np.abs(y - c - a1 * t) * np.sqrt(np.pi / 2)
        cv = float(np.sum(r * t) / np.sum(t * t))              # sd = cv t through the origin
        s_nom, s_act = g.s_nom.to_numpy(), g.s_act.to_numpy()
        a_s = float(np.sum(s_act * s_nom) / np.sum(s_nom ** 2)) - 1.0
        rs = np.abs(s_act - (1 + a_s) * s_nom) * np.sqrt(np.pi / 2)
        cv_s = float(np.sum(rs * s_nom) / np.sum(s_nom ** 2))
        models[lv] = {"a": float(a1 - 1.0), "c": float(c), "cv": cv, "a_s": a_s, "cv_s": cv_s, "n_legs": int(t.size),
                      "share_wait": float(np.mean(g.wait > 0.5))}
        print(lv, {k: round(v, 4) for k, v in models[lv].items()}, flush=True)
    (ROOT / "models" / "mp_model_dev.json").write_text(json.dumps(models, indent=2))


# ------------------------------------------------------------------------------------------------ spread models
def sd_of(kind, p, h):
    if kind == "affine":
        return np.maximum(p[0] + p[1] * h, 1e-3)
    if kind == "sqrt":
        return np.sqrt(np.maximum(p[0] + p[1] * h, 1e-6))
    return np.sqrt(np.maximum(p[0] + p[1] * h + p[2] * h * h, 1e-6))


def nll(theta, kind, h, e):
    b0, b1, *p = theta
    sd = sd_of(kind, np.abs(p) if kind != "affine" else p, h)
    r = (e - b0 - b1 * h) / sd
    return float(np.sum(0.5 * r * r + np.log(sd)) + 0.5 * h.size * np.log(2 * np.pi))


def fit(kind, h, e):
    A = np.c_[np.ones_like(h), h]
    b = np.linalg.lstsq(A, e, rcond=None)[0]
    r = e - A @ b
    v = float(np.var(r))
    x0 = {"affine": [np.std(r) / 2, np.std(r) / (2 * h.mean())],
          "sqrt": [v / 2, v / (2 * h.mean())],
          "hybrid": [v / 3, v / (3 * h.mean()), v / (3 * h.mean() ** 2)]}[kind]
    best = None
    for scale in (1.0, 0.3, 3.0):
        res = minimize(nll, np.r_[b, np.array(x0) * scale], args=(kind, h, e), method="Nelder-Mead",
                       options={"maxiter": 20000, "maxfev": 20000, "xatol": 1e-8, "fatol": 1e-6})
        if best is None or res.fun < best.fun:
            best = res
    th = best.x.copy()
    if kind != "affine":
        th[2:] = np.abs(th[2:])
    return th, best.fun


def analyse():
    df = pd.read_csv(OUT / "dev4_errpairs.csv")
    out, bins = {}, []
    rng = np.random.default_rng(0)
    for lv, g in df.groupby("level"):
        h, e = g.h.to_numpy(float), g.e.to_numpy(float)
        res = {"n_pairs": int(h.size), "n_missions": int(g.mission.nunique())}
        fits = {}
        for kind in ("affine", "sqrt", "hybrid"):
            th, f = fit(kind, h, e)
            k = th.size
            fits[kind] = th
            res[kind] = {"theta": th.tolist(), "nll": f, "aic": 2 * f + 2 * k}
        # out-of-sample log-likelihood, 5 folds grouped by mission
        miss = g.mission.unique()
        rng.shuffle(miss)
        fold = {m: i % 5 for i, m in enumerate(miss)}
        f_id = g.mission.map(fold).to_numpy()
        for kind in ("affine", "sqrt", "hybrid"):
            ll = 0.0
            for i in range(5):
                tr, te = f_id != i, f_id == i
                th, _ = fit(kind, h[tr], e[tr])
                ll -= nll(th, kind, h[te], e[te])
            res[kind]["cv_loglik"] = ll
            res[kind]["cv_loglik_per_pair"] = ll / h.size
        # random-effects decomposition: per-mission least-squares line, slope variance between missions
        slopes, w_res = [], []
        for _m, gm in g.groupby("mission"):
            if len(gm) < 5 or gm.h.std() < 1e-6:
                continue
            A = np.c_[np.ones(len(gm)), gm.h.to_numpy()]
            c = np.linalg.lstsq(A, gm.e.to_numpy(), rcond=None)[0]
            slopes.append(c)
            w_res += list(gm.e.to_numpy() - A @ c)
        slopes = np.array(slopes)
        A = np.c_[np.ones_like(h), h]
        pooled = e - A @ np.linalg.lstsq(A, e, rcond=None)[0]
        res["re"] = {"n_missions_fit": int(len(slopes)), "slope_mean": float(slopes[:, 1].mean()),
                     "slope_sd_between": float(slopes[:, 1].std(ddof=1)),
                     "intercept_sd_between": float(slopes[:, 0].std(ddof=1)),
                     "resid_var_pooled": float(np.var(pooled)), "resid_var_within": float(np.var(w_res)),
                     "share_between": float(1 - np.var(w_res) / np.var(pooled))}
        # Pearson correlation of the residuals of two tasks of the same mission (pairs drawn at random)
        r_all = pd.Series(pooled, index=g.index)
        cs = []
        for _m, gm in g.groupby("mission"):
            if len(gm) < 2:
                continue
            idx = gm.index.to_numpy()
            a = rng.choice(idx, size=min(40, len(idx)), replace=True)
            b = rng.choice(idx, size=a.size, replace=True)
            keep = a != b
            cs += list(zip(r_all[a[keep]], r_all[b[keep]]))
        cs = np.array(cs)
        res["re"]["within_mission_corr"] = float(np.corrcoef(cs[:, 0], cs[:, 1])[0, 1])
        out[lv] = res
        q = np.quantile(h, np.linspace(0, 1, 11))
        for a, b in zip(q[:-1], q[1:]):
            sel = (h >= a) & (h <= b)
            hm = float(h[sel].mean())
            row = {"level": lv, "h_lo": a, "h_hi": b, "n": int(sel.sum()), "h_mean": hm,
                   "sd_emp": float(np.std(e[sel] - fits["affine"][0] - fits["affine"][1] * h[sel]))}
            for kind in ("affine", "sqrt", "hybrid"):
                p = fits[kind][2:]
                row[f"sd_{kind}"] = float(sd_of(kind, p, np.array([hm]))[0])
            bins.append(row)
        print(f"{lv}: n={h.size} affine AIC={res['affine']['aic']:.0f} sqrt AIC={res['sqrt']['aic']:.0f} "
              f"hybrid AIC={res['hybrid']['aic']:.0f} | cv/pair affine={res['affine']['cv_loglik_per_pair']:.4f} "
              f"sqrt={res['sqrt']['cv_loglik_per_pair']:.4f} hybrid={res['hybrid']['cv_loglik_per_pair']:.4f} | "
              f"between share={res['re']['share_between']:.2f} corr={res['re']['within_mission_corr']:.2f}",
              flush=True)
    (OUT / "dev4_errstructure.json").write_text(json.dumps(out, indent=2))
    pd.DataFrame(bins).to_csv(OUT / "dev4_errbins.csv", index=False)
    print(pd.DataFrame(bins).round(2).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["collect", "analyse", "legs"])
    ap.add_argument("--levels", default="mid,high")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.levels.split(","), a.workers)
    elif a.cmd == "legs":
        legs(a.levels.split(","), a.workers)
    else:
        analyse()
