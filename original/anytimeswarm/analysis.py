"""Derived metrics shared by bootstrap / figures / tables.

best_known(snapshot) = max(J over every method, budget and reference solver on that snapshot)
regret_pct           = (best_known - J) / scale * 100                (solution quality, H1)
net_k<kappa>         = J_eff(kappa) - mu * scale * elapsed_ms        (what the controller optimises)
net_regret_k<kappa>  = (best_known - net_k) / scale * 100            (H2 + H3 trade-off; lower = better)
eff_regret_k<kappa>  = (best_known - J_eff(kappa)) / scale * 100     (regret after the publication delay, mu-free)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import rpath


def load_static(cfg: dict, split: str = "test", tag: str = "") -> pd.DataFrame:
    d = rpath(cfg["paths"]["results_dir"]) / "static"
    df = pd.read_csv(d / f"static_{split}{tag}.csv")
    bk = df.groupby("snap").J.max().rename("bk_methods")
    df = df.join(bk, on="snap")
    ref_p = d / f"reference_{split}{tag}.csv"
    df["best_known"] = df.bk_methods
    if ref_p.exists():
        ref = pd.read_csv(ref_p).set_index("snap")
        cols = [c for c in ("J_alns_ref", "J_ortools") if c in ref]
        df = df.join(ref[cols], on="snap")
        df["best_known"] = df[["bk_methods"] + cols].max(axis=1)
    mu = cfg["controller"]["mu"]
    df["regret_pct"] = (df.best_known - df.J) / df.scale_value * 100
    for k in cfg["kappas"]:
        df[f"net_k{k}"] = df[f"J_eff_k{k}"] - mu * df.scale_value * df.elapsed_ms
        df[f"net_regret_k{k}"] = (df.best_known - df[f"net_k{k}"]) / df.scale_value * 100
        df[f"eff_regret_k{k}"] = (df.best_known - df[f"J_eff_k{k}"]) / df.scale_value * 100  # mu-free
    df["compute_frac"] = df.elapsed_ms / df.budget_ms
    return df


def at_kappa(df: pd.DataFrame, kappa) -> pd.DataFrame:
    """Rows valid for a given kappa: kappa-independent methods (NaN) + rows run with that kappa."""
    return df[df.kappa.isna() | np.isclose(df.kappa.fillna(-1), kappa)]


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n: int = 2000, seed: int = 0) -> dict:
    """Mean difference a - b over paired units (scenarios / missions) with a 95% percentile CI."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n, len(d)))
    bs = d[idx].mean(1)
    return {"mean_a": float(a.mean()), "mean_b": float(b.mean()), "diff": float(d.mean()),
            "ci_lo": float(np.percentile(bs, 2.5)), "ci_hi": float(np.percentile(bs, 97.5)),
            "p_gt_0": float((bs > 0).mean()), "n_pairs": int(len(d))}
