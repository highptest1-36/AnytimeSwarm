#!/usr/bin/env python3
"""Run a conference experiment script under WSL with a machine-idle guard that also works on Linux.

    python tools/run_guarded.py <code_root> <script.py> [script args...]

The conference guard (anytimeswarm.utils.wait_machine_idle) only inspects Windows processes and returns at once on
Linux. This wrapper replaces it, without editing any code, by a guard that blocks while
  * a RAVEN-UAV Python process runs on the Windows host (queried through powershell.exe), or
  * a PX4 SITL / Gazebo simulation runs inside WSL (e.g. the user practising the hands-on guide),
and counts every wait in GUARD_LOG so the registry line of the run reports it. The script is then executed with
runpy exactly as `python script.py args` would.
"""
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
SIM_PATTERNS = ("gz sim", "px4_sitl_default/bin/px4")
_cache = {"t": -1e9, "busy": []}


def _busy(max_age_s: float = 20.0) -> list[str]:
    if time.time() - _cache["t"] < max_age_s:
        return _cache["busy"]
    busy = []
    try:
        out = subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, timeout=30).stdout
        busy += [f"windows: {ln.strip()}" for ln in out.splitlines() if "RAVEN" in ln]
    except Exception:  # noqa: BLE001 - the guard must never crash an experiment
        pass
    try:
        out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True, timeout=10).stdout
        busy += [f"wsl: {ln.strip()}" for ln in out.splitlines()
                 if any(p in ln for p in SIM_PATTERNS) and "run_guarded" not in ln]
    except Exception:  # noqa: BLE001
        pass
    _cache.update(t=time.time(), busy=busy)
    return busy


def main():
    code_root, script, *args = sys.argv[1:]
    sys.path.insert(0, str(Path(code_root).resolve()))
    import anytimeswarm.utils as U

    def wait_machine_idle(latency_only: bool = True, poll_s: float = 30.0) -> float:
        if os.environ.get("ANYTIMESWARM_NO_GUARD"):
            return 0.0
        waited = 0.0
        while True:
            busy = _busy()
            if not busy:
                return waited
            U.GUARD_LOG["concurrent"] += 1
            U.GUARD_LOG["examples"].add(busy[0][:40])
            if waited == 0.0:
                print(f"[guard] machine busy, waiting: {busy[0][:100]}", flush=True)
            time.sleep(poll_s)
            waited += poll_s
            _cache["t"] = -1e9

    U.wait_machine_idle = wait_machine_idle
    sys.argv = [script, *args]
    sys.path.insert(0, str(Path(script).resolve().parent))
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
