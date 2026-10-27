"""Seeded scenario generator (task generator + event generator).

The generator is independent of every planning algorithm: it only depends on (scale, profile, seed)
and the `world` block of the config. Same seed -> identical scenario (tested).
"""
from __future__ import annotations

import numpy as np

from .entities import UAV, Event, Scenario, Task


def _task(rng, tid, announce, world, hot):
    m = world["map_m"]
    if hot is not None and rng.random() < 0.5:
        c = hot[rng.integers(len(hot))]
        x, y = np.clip(rng.normal(c, world["hotspot_std_m"]), 0, m)
    else:
        x, y = rng.uniform(0, m, size=2)
    release = announce + rng.uniform(*world["announce_lead_s"])
    service = rng.uniform(*world["service_s"])
    deadline = release + service + rng.uniform(*world["window_s"])
    reward = float(rng.choice(world["reward_levels"], p=world["reward_probs"]))
    return Task(tid, float(x), float(y), float(announce), float(release), float(deadline), float(service), reward)


def generate_scenario(cfg: dict, scale: str, profile: str, seed: int) -> Scenario:
    world, sc, pr = cfg["world"], cfg["scales"][scale], cfg["profiles"][profile]
    # independent stream per (scale, profile, seed); `stream` pins the scale id when a config lists a subset of scales
    stream = sc.get("stream", list(cfg["scales"]).index(scale))
    rng = np.random.default_rng([seed, stream, list(cfg["profiles"]).index(profile)])
    m, H = world["map_m"], world["horizon_s"]
    depot = (m / 2.0, m / 2.0)
    hot = rng.uniform(0.15 * m, 0.85 * m, size=(world["hotspots"], 2)) if world["hotspots"] else None

    uavs = []
    for k in range(sc["n_uav"]):
        jitter = rng.normal(0, 50, size=2)
        uavs.append(UAV(k, depot[0] + jitter[0], depot[1] + jitter[1], float(rng.uniform(*world["speed_mps"])),
                        float(rng.uniform(*world["capacity_m"]))))

    n_init = int(round(sc["n_tasks"] * world["initial_frac"]))
    tasks = [_task(rng, j, 0.0, world, hot) for j in range(n_init)]
    events = []
    n_rest = sc["n_tasks"] - n_init
    nb = max(pr["arrival_batches"], 1) if n_rest > 0 else 0
    if nb:
        times = np.sort(rng.uniform(60, H - 600, size=nb))
        sizes = np.bincount(rng.integers(nb, size=n_rest), minlength=nb)
        tid = n_init
        for t, s in zip(times, sizes):
            if s == 0:
                continue
            new = [_task(rng, tid + i, float(t), world, hot) for i in range(s)]
            tid += s
            tasks += new
            events.append(Event(float(t), "arrival", {"task_ids": [x.id for x in new]}))
    for _ in range(pr["failures"]):
        events.append(Event(float(rng.uniform(200, H - 400)), "failure", {"uav_id": int(rng.integers(sc["n_uav"]))}))
    for _ in range(pr["deadline_changes"]):
        t = float(rng.uniform(120, H - 600))
        known = [x for x in tasks if x.announce <= t and x.deadline > t + 120]
        if not known:
            continue
        x = known[rng.integers(len(known))]
        new_d = max(t + 60.0, x.release + x.service + 30.0, x.deadline - rng.uniform(120, 400))
        events.append(Event(t, "deadline", {"task_id": x.id, "new_deadline": float(new_d)}))
    # a failed UAV fails only once
    seen, ev = set(), []
    for e in sorted(events, key=lambda e: e.time):
        if e.kind == "failure":
            if e.data["uav_id"] in seen:
                continue
            seen.add(e.data["uav_id"])
        ev.append(e)
    return Scenario(f"{scale}-{profile}-{seed}", seed, scale, profile, depot, uavs, tasks, ev, world,
                    cfg["objective"])
