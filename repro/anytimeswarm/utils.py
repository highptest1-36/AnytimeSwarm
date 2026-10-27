"""Config, run directories, result registry, timing."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path=None) -> dict:
    path = Path(path) if path else ROOT / "configs" / "default.yaml"
    if not path.is_absolute():
        path = ROOT / path
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_config_path"] = str(path)
    return cfg


def rpath(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def now_ms() -> float:
    return time.perf_counter() * 1000.0


_GUARD = {"t": -1e9, "procs": []}
GUARD_LOG = {"concurrent": 0, "examples": set()}   # guard checks that saw a (non-latency) RAVEN process
# RAVEN-UAV (same laptop) runs `python scripts/NN_*.py`; these scripts measure GPU latency
RAVEN_LATENCY = ("03_sanity_detector", "04_build_cache", "08_profile_latency", "09_sahi_reference")


def _raven_processes(max_age_s: float = 20.0) -> list[str]:
    """Command lines of RAVEN-UAV Python processes (cached for max_age_s; Windows only, else [])."""
    if time.time() - _GUARD["t"] < max_age_s:
        return _GUARD["procs"]
    procs = []
    if os.name == "nt":
        import subprocess
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | ForEach-Object { $_.CommandLine }"],
                capture_output=True, text=True, timeout=30).stdout
            procs = [ln.strip() for ln in out.splitlines()
                     if ln.strip() and ("RAVEN" in ln or " scripts/" in ln or " scripts\\" in ln)]
        except Exception:  # noqa: BLE001 - the guard must never crash an experiment
            procs = []
    _GUARD.update(t=time.time(), procs=procs)
    return procs


def wait_machine_idle(latency_only: bool = True, poll_s: float = 30.0) -> float:
    """Machine rule (root README): RAVEN-UAV latency measurements and AnytimeSwarm timing never run at the
    same time. Blocks while RAVEN runs a latency-measuring script (latency_only=False: while ANY RAVEN
    script runs). Non-latency RAVEN processes seen during a run are counted in GUARD_LOG["concurrent"] so
    that the registry can report them. Returns the seconds waited. Disable with ANYTIMESWARM_NO_GUARD=1."""
    if os.environ.get("ANYTIMESWARM_NO_GUARD"):
        return 0.0
    waited = 0.0
    while True:
        procs = _raven_processes()
        if procs:
            GUARD_LOG["concurrent"] += 1
            GUARD_LOG["examples"].add(procs[0].split("scripts")[-1][:40])
        if latency_only:
            procs = [p for p in procs if any(k in p for k in RAVEN_LATENCY)]
        if not procs:
            return waited
        if waited == 0.0:
            print(f"[guard] waiting for RAVEN-UAV to finish: {procs[0][-80:]}", flush=True)
        time.sleep(poll_s)
        waited += poll_s
        _GUARD["t"] = -1e9


def env_info() -> dict:
    info = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(), "cpu_count": os.cpu_count()}
    for mod in ("numpy", "sklearn", "ortools"):
        try:
            info[mod] = __import__(mod).__version__
        except ImportError:
            pass
    return info


def make_run_dir(cfg: dict, name: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    d = rpath(cfg["paths"]["results_dir"]) / "runs" / f"{stamp}_{name}"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(cfg["_config_path"], d / "config.yaml")
    save_json(env_info(), d / "env.json")
    return d


def _default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def save_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=_default)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_registry(cfg: dict, row: dict) -> None:
    """Append one line to results/registry.csv - the master index of every experiment run."""
    path = rpath(cfg["paths"]["results_dir"]) / "registry.csv"
    row = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"), **row}
    rows, header = [], list(row)
    if path.exists():
        with open(path, "r", encoding="utf-8", newline="") as f:
            rd = csv.DictReader(f)
            rows = list(rd)
            header = list(rd.fieldnames or []) + [k for k in row if k not in (rd.fieldnames or [])]
    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})
