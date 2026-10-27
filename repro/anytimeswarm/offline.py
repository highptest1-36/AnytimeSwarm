"""Exact offline simulation of stopping policies on recorded anytime trajectories.

Why it is exact: every ALNS variant uses the same seed and per-ITERATION cooling, so any stopping policy
follows the trajectory of the fixed-budget run and only stops earlier. Given a trace of the longest budget
(iteration timestamps + every new best solution), the plan a policy would publish is the incumbent at its
stop time. This makes it possible to compare whole quality-vs-compute FRONTIERS of
    fixed budget B (dense grid) | stagnation stop (patience grid) | adaptive rule (mu grid, variants)
on identical trajectories. Controller overhead is NOT included here; the online runs of
experiments/04_run_static.py measure it.

Predictions used for the adaptive rule on dev are OUT-OF-FOLD (scenario-grouped), so the offline frontier
of the learned rule is not optimistically biased.
"""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import GroupKFold

from .controller.delay_cost import DelayModel
from .controller.features import TraceView, features_at, target_at
from .controller.improvement_model import LearnedPredictor, OnlinePredictor
from .simulator.problem import Solution, delayed_value


def first_check(tr, c) -> float:
    it = tr["trace"]["iter_t"]
    return max(c["min_ms"], it[0] if it else c["min_ms"])


def build_dataset(traces, c, t_max, feature_fn=features_at, horizon_ms=None):
    """Checkpoints every check_ms along each trace: features, future gain over H (% of scale), groups."""
    X, y, g, meta = [], [], [], []
    H = c["horizon_ms"] if horizon_ms is None else horizon_ms
    for tr in traces:
        v = TraceView(tr["trace"]["iter_t"], tr["trace"]["imp"], tr["J0"], tr["scale_value"], tr["trace"]["u0"])
        t = first_check(tr, c)
        while t + c["horizon_ms"] <= t_max:
            X.append(feature_fn(v, t, tr["N"], tr["M"]))
            y.append(target_at(v, t, H))
            g.append(tr["scenario"])
            meta.append((tr["idx"], t))
            t += c["check_ms"]
    return np.asarray(X, float), np.asarray(y, float), np.asarray(g), meta


def oof_predictions(X, y, groups, make_model=None, n_splits=5):
    make_model = make_model or (lambda: LearnedPredictor())
    oof = np.zeros(len(y))
    for tr_i, te_i in GroupKFold(n_splits).split(X, y, groups):
        oof[te_i] = make_model().fit(X[tr_i], y[tr_i]).predict_many(X[te_i])
    return oof


class Trajectory:
    """Incumbent of one recorded run as a step function of time + lazily built Solution objects."""

    def __init__(self, tr, P):
        self.tr, self.P = tr, P
        self.snaps = tr["snapshots"]                       # [(t_ms, J, routes)], first = FFR plan
        self.times = np.array([s[0] for s in self.snaps])
        self.J = np.array([s[1] for s in self.snaps])
        self.t_init = float(self.times[0])
        self._sol = {}

    def index_at(self, t):
        return np.maximum(np.searchsorted(self.times, t, side="right") - 1, 0)

    def solution(self, i) -> Solution:
        if i not in self._sol:
            self._sol[i] = Solution(self.P, self.snaps[i][2])
        return self._sol[i]

    def J_eff(self, i, delay_s) -> float:
        return delayed_value(self.P, self.solution(int(i)), delay_s)[0]


def stagnation_stop(tr, patience_ms, t_cap):
    """Stop when no improvement for `patience_ms` (checked continuously), capped at t_cap."""
    last = tr["snapshots"][0][0]
    for t_imp, *_ in tr["trace"]["imp"]:
        if t_imp - last >= patience_ms:
            break
        last = t_imp
    return min(last + patience_ms, t_cap)


def checkpoint_table(traces, snaps, c, t_max, kappas, pred_at):
    """Per trace: checkpoint times, predicted gain (reward units) and delay cost C_delay(t, H) per kappa."""
    out = {}
    H = c["horizon_ms"]
    for tr in traces:
        P = snaps[tr["idx"]]["P"]
        traj = Trajectory(tr, P)
        ts, gs = [], []
        t = first_check(tr, c)
        while t + H <= t_max:
            p = pred_at.get((tr["idx"], round(t, 6)))
            if p is not None:
                ts.append(t)
                gs.append(p * P.scale / 100.0)
            t += c["check_ms"]
        ts = np.asarray(ts)
        idx = traj.index_at(ts) if len(ts) else np.zeros(0, int)
        dcs = {}
        for k in kappas:
            dm = DelayModel(P, k)
            dcs[k] = np.array([dm.cost(traj.solution(int(i)), t_, H) for i, t_ in zip(idx, ts)])
        out[tr["idx"]] = {"t": ts, "gain": np.asarray(gs), "dc": dcs, "traj": traj}
    return out


def adaptive_stop(ck, kappa, mu, scale, H, t_cap, use_delay=True):
    thr = mu * scale * H + (ck["dc"][kappa] if use_delay else 0.0)
    hit = np.nonzero(ck["gain"] <= thr)[0]
    return min(float(ck["t"][hit[0]]), t_cap) if len(hit) else t_cap


def online_gains(traces, c, t_max, feature_fn=features_at):
    """Predictions of the untrained online-rate predictor at every checkpoint (for the ablation)."""
    X, _, _, meta = build_dataset(traces, c, t_max, feature_fn)
    op = OnlinePredictor(c["horizon_ms"])
    return {(i, round(t, 6)): op.predict(f) for (i, t), f in zip(meta, X)}
