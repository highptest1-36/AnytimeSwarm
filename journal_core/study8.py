"""Study 8: planning budget, an independently specified scenario family, and the cost-aware fallback in tier C.

Timing of a planning call. In studies 2-7 the publication delay kappa * t / 1000 used the time t of the search call
(study2.solve2: repair plus ALNS). The planning model is built before that call (effective deadlines, fallback,
moment propagation, and the set of tasks no route can serve), and moment propagation filters the routes after it, so
this work was not charged. Study 8 charges the whole call: timed() measures the solver from entry to return, publishes
with that time and keeps the search time separately (search_ms). At 40 ms the difference is small; at budgets of a few
milliseconds it is part of the question.

8a, planning budget. The same methods with ALNS budgets from 5 to 250 ms (experiments/b8_grid.py).

8b, scenario family "emergency response" (generate_scenario8), specified before any study-8 run and independent of
the conference generator in every structural parameter except the reward levels (so the mean reward w_bar = 2.1 of
the fixed-cost rule is unchanged) and the number of UAVs per scale:
    map            14 x 7 km rectangle (conference: 10 x 10 km square), depot at the centre
    tasks          5 incident zones, 70% of the tasks around them, sd 400 m (3 zones, 50%, sd 600 m)
    urgency        30% urgent tasks with a window of 90-240 s, the others 240-900 s (one class, 180-600 s)
    service        20-120 s (30-90 s); release 0-60 s after announcement (0-120 s); 30% known at t = 0 (50%)
    UAV speed      8-20 m/s (10-16 m/s)
    profiles       incidents   8 bursts at times ~ Beta(1.2, 2.5) over the mission, sizes ~ Dirichlet(0.6), each burst
                               around its own new incident point (80% of its tasks, sd 300 m)
                   attrition   4 batches, 1/2/3 UAV failures (small/medium/large) between 100 s and the last 300 s
                   priorities  4 batches, 8 deadline cuts (conference: 6 batches; 3 batches + 2 failures;
                               3 batches + 4 deadline cuts)
The number of tasks per scale is the conference number times LOAD8, set once on development seeds by the rule of
docs/18_PROTOCOL_V8.md (section 4a) with the nominal model only. Every tuned value (safety factor, buffer slope, error
model, moment-propagation model) is transferred from the conference family without re-tuning.

8c, tier C. solve8() routes a method option dict to journal_core.study7.solve7 with explicit values, so the tier C
manager (journal_ros/study8c.py) and its tier B counterpart (experiments/b8c_gz.py) plan identically.

The frozen modules of studies 2-7 and the conference package are not modified; this module wraps them.
"""
from __future__ import annotations

import math

import numpy as np

from . import ORIGINAL  # noqa: F401  (puts the frozen conference package on sys.path)
from anytimeswarm.simulator.entities import UAV, Event, Scenario, Task
from anytimeswarm.utils import now_ms

from .risk import ErrorModel
from .study7 import solve7


# ---------------------------------------------------------------------------------------------- timing
def timed(solver, log: list | None = None):
    """solver with elapsed_ms = whole call (model construction, search, route filter); search time in search_ms.
    Appends (total ms, search ms, repair ms, iterations) of every call to log."""
    def run(*a, **kw):
        t0 = now_ms()
        out = solver(*a, **kw)
        total = now_ms() - t0
        out["search_ms"] = out["elapsed_ms"]
        out["elapsed_ms"] = total
        if log is not None:
            log.append((total, out["search_ms"], float(out.get("t_first_feasible_ms", math.nan)), int(out["iters"])))
        return out
    return run


def timing_columns(log: list, budget_ms: float) -> dict:
    """Per-run summary of the planning calls recorded by timed()."""
    if not log:
        return {}
    a = np.asarray(log, float)
    tot, srch, rep, it = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    return {"call_ms_mean": float(tot.mean()), "call_ms_p50": float(np.percentile(tot, 50)),
            "call_ms_p95": float(np.percentile(tot, 95)), "call_ms_p99": float(np.percentile(tot, 99)),
            "call_ms_max": float(tot.max()), "search_ms_mean": float(srch.mean()),
            "model_ms_mean": float((tot - srch).mean()), "repair_ms_mean": float(np.nanmean(rep)),
            "iters_per_search_ms": float(it.sum() / srch.sum()) if srch.sum() > 0 else 0.0,
            "over_budget_share": float(np.mean(tot > budget_ms)), "n_calls": int(a.shape[0])}


# ---------------------------------------------------------------------------------------------- 8c: explicit options
def w_bar(cfg: dict) -> float:
    """Mean task reward of the generator (2.1), the w_bar of the fixed-cost rule (as experiments/b7_grid.w_bar)."""
    w = cfg["world"]
    return float(sum(a * b for a, b in zip(w["reward_levels"], w["reward_probs"])))


def solve8_kwargs(opt: dict, err: ErrorModel, w_bar: float) -> dict:
    """solve7 keyword arguments of an option dict with explicit values (no 'auto'):
        z=<z>;lam=<x>[;cost=fee]   cost-aware fallback (proportional or fixed late cost)
        z=<z>;fb=nominal           nominal fallback (study 3)
        prop=<c>;fb=none           proportional buffer without fallback (study 5)
        z=<z>                      proposed model without fallback
        (none)                     nominal model"""
    kw = {"err": err, "z": float(opt["z"]) if "z" in opt else None}
    if "lam" in opt:
        if kw["z"] is None:
            raise ValueError("the cost-aware fallback needs a safety factor z")
        kw.update(lam=float(opt["lam"]), cost=opt.get("cost", "prop"), w_bar=float(w_bar))
    elif "prop" in opt:
        if opt.get("fb") != "none":
            raise ValueError("study 8 runs the proportional buffer without fallback only")
        kw["prop_nofb"] = float(opt["prop"])
    elif "fb" in opt:
        kw["fb"] = opt["fb"]
    unknown = set(opt) - {"z", "lam", "cost", "prop", "fb"}
    if unknown:
        raise ValueError(f"unknown options {sorted(unknown)}")
    return kw


def solve8(base: str, P, old_routes, budget_ms: float, cfg: dict, opt: dict, err: ErrorModel, w_bar: float,
           seed: int = 0, predictor=None, kappa: float = 1.0, latency_mean_s: float = 0.0, check: bool = True,
           log: list | None = None) -> dict:
    """One timed planning call of a study-8c method (tier C manager and its tier B counterpart)."""
    kw = solve8_kwargs(opt, err, w_bar)
    return timed(solve7, log)(base, P, old_routes, budget_ms, cfg, seed=seed, predictor=predictor, kappa=kappa,
                              latency_mean_s=latency_mean_s, ms_per_task=1.0, check=check, **kw)


# ---------------------------------------------------------------------------------------------- 8b: scenario family
WORLD8 = {"map_xy_m": [14000.0, 7000.0], "speed_mps": [8.0, 20.0], "service_s": [20.0, 120.0],
          "announce_lead_s": [0.0, 60.0], "urgent_frac": 0.3, "urgent_window_s": [90.0, 240.0],
          "window_s": [240.0, 900.0], "hotspots": 5, "hotspot_frac": 0.7, "hotspot_std_m": 400.0,
          "initial_frac": 0.3}
SCALES8 = {"small8": "small", "medium8": "medium", "large8": "large"}       # n_uav, n_tasks of the conference scale
PROFILES8 = {"incidents": {"bursts": 8, "beta": (1.2, 2.5), "dirichlet": 0.6, "burst_frac": 0.8, "burst_sd_m": 300.0},
             "attrition": {"batches": 4, "failures": {"small8": 1, "medium8": 2, "large8": 3}},
             "priorities": {"batches": 4, "deadline_cuts": 8}}
LOAD_GRID = (0.6, 0.8, 1.0, 1.25, 1.5)
LOAD8 = None                     # selected on development seeds (docs/18_PROTOCOL_V8.md section 4a)


def _xy(rng, w, hot, centre=None, frac=0.0, sd=0.0):
    Lx, Ly = w["map_xy_m"]
    u = rng.random()
    if centre is not None and u < frac:
        x, y = rng.normal(centre, sd)
    elif hot is not None and rng.random() < w["hotspot_frac"]:
        x, y = rng.normal(hot[rng.integers(len(hot))], w["hotspot_std_m"])
    else:
        x, y = rng.uniform(0.0, Lx), rng.uniform(0.0, Ly)
    return float(np.clip(x, 0.0, Lx)), float(np.clip(y, 0.0, Ly))


def _task8(rng, tid, announce, w, hot, centre=None, frac=0.0, sd=0.0) -> Task:
    x, y = _xy(rng, w, hot, centre, frac, sd)
    release = announce + rng.uniform(*w["announce_lead_s"])
    service = rng.uniform(*w["service_s"])
    win = w["urgent_window_s"] if rng.random() < w["urgent_frac"] else w["window_s"]
    deadline = release + service + rng.uniform(*win)
    reward = float(rng.choice(w["reward_levels"], p=w["reward_probs"]))
    return Task(tid, x, y, float(announce), float(release), float(deadline), float(service), reward)


def world8(cfg: dict) -> dict:
    """World block of the family: the conference world (energy, hover cost, rewards, horizon) with WORLD8 on top."""
    w = dict(cfg["world"])
    w.update({k: (list(v) if isinstance(v, (list, tuple)) else v) for k, v in WORLD8.items()})
    w.pop("map_m", None)
    return w


def n_tasks8(cfg: dict, scale: str, load: float) -> int:
    return int(round(cfg["scales"][SCALES8[scale]]["n_tasks"] * load))


def generate_scenario8(cfg: dict, scale: str, profile: str, seed: int, load: float | None = None) -> Scenario:
    """Scenario of the emergency-response family (module docstring); same (scale, profile, seed, load) -> same
    scenario. Random streams [seed, 80 + scale index, 90 + profile index] are disjoint from the conference ones."""
    load = LOAD8 if load is None else load
    if load is None:
        raise RuntimeError("LOAD8 not selected yet")
    w = world8(cfg)
    H = w["horizon_s"]
    Lx, Ly = w["map_xy_m"]
    n_uav = cfg["scales"][SCALES8[scale]]["n_uav"]
    n_tasks = n_tasks8(cfg, scale, load)
    pr = PROFILES8[profile]
    rng = np.random.default_rng([seed, 80 + list(SCALES8).index(scale), 90 + list(PROFILES8).index(profile)])
    depot = (Lx / 2.0, Ly / 2.0)
    hot = np.c_[rng.uniform(0.1 * Lx, 0.9 * Lx, w["hotspots"]), rng.uniform(0.1 * Ly, 0.9 * Ly, w["hotspots"])]
    uavs = []
    for k in range(n_uav):
        jx, jy = rng.normal(0.0, 50.0, size=2)
        uavs.append(UAV(k, depot[0] + jx, depot[1] + jy, float(rng.uniform(*w["speed_mps"])),
                        float(rng.uniform(*w["capacity_m"]))))
    n_init = int(round(n_tasks * w["initial_frac"]))
    tasks = [_task8(rng, j, 0.0, w, hot) for j in range(n_init)]
    events = []
    n_rest = n_tasks - n_init
    tid = n_init
    if profile == "incidents":
        K = pr["bursts"]
        times = np.sort(60.0 + (H - 660.0) * rng.beta(*pr["beta"], size=K))
        sizes = rng.multinomial(n_rest, rng.dirichlet(np.full(K, pr["dirichlet"])))
        for t, s in zip(times, sizes):
            centre = np.array([rng.uniform(0.1 * Lx, 0.9 * Lx), rng.uniform(0.1 * Ly, 0.9 * Ly)])
            if s == 0:
                continue
            new = [_task8(rng, tid + i, float(t), w, hot, centre, pr["burst_frac"], pr["burst_sd_m"])
                   for i in range(s)]
            tid += s
            tasks += new
            events.append(Event(float(t), "arrival", {"task_ids": [x.id for x in new]}))
    else:
        nb = pr["batches"]
        times = np.sort(rng.uniform(60.0, H - 600.0, size=nb))
        sizes = np.bincount(rng.integers(nb, size=n_rest), minlength=nb)
        for t, s in zip(times, sizes):
            if s == 0:
                continue
            new = [_task8(rng, tid + i, float(t), w, hot) for i in range(s)]
            tid += s
            tasks += new
            events.append(Event(float(t), "arrival", {"task_ids": [x.id for x in new]}))
    if profile == "attrition":
        nf = min(pr["failures"][scale], n_uav - 1)
        for u in rng.choice(n_uav, size=nf, replace=False):
            events.append(Event(float(rng.uniform(100.0, H - 300.0)), "failure", {"uav_id": int(u)}))
    if profile == "priorities":
        for _ in range(pr["deadline_cuts"]):
            t = float(rng.uniform(120.0, H - 600.0))
            known = [x for x in tasks if x.announce <= t and x.deadline > t + 120.0]
            if not known:
                continue
            x = known[rng.integers(len(known))]
            new_d = max(t + 60.0, x.release + x.service + 30.0, x.deadline - rng.uniform(120.0, 400.0))
            events.append(Event(t, "deadline", {"task_id": x.id, "new_deadline": float(new_d)}))
    events.sort(key=lambda e: e.time)
    return Scenario(f"{scale}-{profile}-{seed}", seed, scale, profile, depot, uavs, tasks, events, w, cfg["objective"])


def scenarios8(cfg: dict, seeds: dict, scales, load: float | None = None) -> list:
    return [generate_scenario8(cfg, sc, p, s, load) for sc in scales for p in PROFILES8
            for s in range(seeds["start"], seeds["start"] + seeds["n"])]


def is_urgent(task, window_factor: float = 1.0) -> bool:
    """Urgency class of a family-8 task from its generated window (the two window ranges are disjoint; tasks of the
    scenario object keep their generated deadlines, deadline cuts are events)."""
    return task.deadline - task.release - task.service < window_factor * WORLD8["urgent_window_s"][1]
