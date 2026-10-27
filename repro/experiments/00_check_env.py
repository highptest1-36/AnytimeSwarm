"""Step 0 - environment check + unit tests.   python experiments/00_check_env.py"""
import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ok = True
print(f"Python {sys.version.split()[0]}  |  CPU threads: {os.cpu_count()}")
for mod in ["numpy", "scipy", "pandas", "sklearn", "matplotlib", "yaml", "pytest", "ortools"]:
    try:
        m = importlib.import_module(mod)
        print(f"  [ok] {mod:12s} {getattr(m, '__version__', '')}")
    except ImportError:
        opt = mod == "ortools"
        print(f"  [{'--' if opt else 'MISSING'}] {mod}{' (optional: reference solver only)' if opt else ''}")
        ok = ok and opt
r = subprocess.run([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT, capture_output=True, text=True)
print(r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr)
ok = ok and r.returncode == 0
print("ENVIRONMENT OK" if ok else "ENVIRONMENT HAS PROBLEMS")
print("Timing tip: close other heavy programs, plug in the laptop charger, and do NOT run RAVEN-UAV "
      "GPU benchmarks at the same time as timing experiments.")
