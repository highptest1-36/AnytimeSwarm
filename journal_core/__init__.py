"""Journal extensions of AnytimeSwarm (tier B: continuous-time execution with disturbances and latency).

The frozen conference package `anytimeswarm` is imported from ../original so that every journal experiment runs the
exact planner, predictor and baselines of the conference version. Nothing in ../original is modified.
"""
import sys
from pathlib import Path

JOURNAL_ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = JOURNAL_ROOT / "original"
if str(ORIGINAL) not in sys.path:
    sys.path.insert(0, str(ORIGINAL))
