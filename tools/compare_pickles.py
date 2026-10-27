#!/usr/bin/env python3
"""Deep comparison of two pickles produced by the AnytimeSwarm pipeline (scenarios / snapshots).

    python tools/compare_pickles.py --code repro A.pkl B.pkl

Walks lists, dicts, dataclasses, plain objects and numpy arrays in parallel. Reports the number of leaves,
how many are bit-identical, and the largest absolute difference among numeric leaves. Exit code 0 when
everything is identical, 1 otherwise. `--code` is the folder whose `anytimeswarm` package unpickles the
objects (classes must be importable).
"""
import argparse
import math
import pickle
import re
import sys
from pathlib import Path

import numpy as np


class Diff:
    def __init__(self, max_examples=10):
        self.leaves = self.equal = 0
        self.max_abs = 0.0
        self.examples = []
        self.by_field = {}
        self.max_examples = max_examples

    def bad(self, path, a, b):
        field = re.sub(r"\[\d+\]", "[i]", path)               # group differences by field, not by index
        self.by_field[field] = self.by_field.get(field, 0) + 1
        if len(self.examples) < self.max_examples:
            self.examples.append(f"{path}: {str(a)[:80]} != {str(b)[:80]}")

    def leaf(self, path, a, b):
        self.leaves += 1
        if isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number)) \
                and not isinstance(a, bool):
            fa, fb = float(a), float(b)
            if fa == fb or (math.isnan(fa) and math.isnan(fb)):
                self.equal += 1
            else:
                d = abs(fa - fb)
                self.max_abs = max(self.max_abs, d if math.isfinite(d) else math.inf)
                self.bad(path, a, b)
        elif a == b:
            self.equal += 1
        else:
            self.bad(path, a, b)

    def walk(self, a, b, path="root"):
        if type(a) is not type(b) and not (isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number))):
            self.leaves += 1
            self.bad(path, f"type {type(a).__name__}", f"type {type(b).__name__}")
            return
        if isinstance(a, np.ndarray):
            if a.shape != b.shape:
                self.leaves += 1
                self.bad(path, a.shape, b.shape)
                return
            self.leaves += a.size
            if a.dtype.kind in "fc":
                eq = (a == b) | (np.isnan(a) & np.isnan(b))
            else:
                eq = a == b
            self.equal += int(np.sum(eq))
            if not np.all(eq):
                if a.dtype.kind in "fiuc":
                    with np.errstate(invalid="ignore"):
                        d = np.nanmax(np.abs(a.astype(float) - b.astype(float)))
                    self.max_abs = max(self.max_abs, float(d))
                self.bad(path, "array", "array")
            return
        if isinstance(a, dict):
            keys = set(a) | set(b)
            for k in sorted(keys, key=str):
                if k not in a or k not in b:
                    self.leaves += 1
                    self.bad(f"{path}[{k!r}]", k in a, k in b)
                else:
                    self.walk(a[k], b[k], f"{path}[{k!r}]")
            return
        if isinstance(a, (list, tuple)):
            if len(a) != len(b):
                self.leaves += 1
                self.bad(path, f"len {len(a)}", f"len {len(b)}")
                return
            for i, (x, y) in enumerate(zip(a, b)):
                self.walk(x, y, f"{path}[{i}]")
            return
        if isinstance(a, (set, frozenset)):
            self.leaf(path, sorted(a, key=str), sorted(b, key=str))
            return
        if hasattr(a, "__dict__") and not isinstance(a, type):
            self.walk(vars(a), vars(b), f"{path}.{type(a).__name__}")
            return
        if hasattr(a, "__slots__"):
            self.walk({s: getattr(a, s, None) for s in a.__slots__}, {s: getattr(b, s, None) for s in b.__slots__}, path)
            return
        self.leaf(path, a, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--code", required=True, help="folder containing the anytimeswarm package")
    args = ap.parse_args()
    sys.path.insert(0, str(Path(args.code).resolve()))
    with open(args.a, "rb") as f:
        A = pickle.load(f)
    with open(args.b, "rb") as f:
        B = pickle.load(f)
    d = Diff()
    d.walk(A, B)
    same = d.equal == d.leaves
    print(f"{Path(args.a).name}: leaves={d.leaves} identical={d.equal} "
          f"({100.0 * d.equal / max(d.leaves, 1):.4f}%) max_abs_diff={d.max_abs:.3e} -> {'IDENTICAL' if same else 'DIFFERENT'}")
    for field, n in sorted(d.by_field.items(), key=lambda kv: -kv[1]):
        print(f"    {n:7d} differing leaves in {field}")
    for e in d.examples[:3]:
        print("   e.g.", e)
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
