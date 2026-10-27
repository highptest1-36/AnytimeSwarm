"""Replanning snapshot (`Problem`), route evaluation, objective and delayed execution.

Model (centralised, written in the paper's "Problem Definition"):
  * UAV k becomes ready at time ready_k, at position start_k, with energy e_k (metres of flight).
    Its committed (in-progress) task is NOT part of the problem: it is already folded into
    (ready_k, start_k, e_k).
  * Route of UAV k: sequence of open tasks, then return to the depot.
      arrival = previous finish + dist / speed_k;  start = max(arrival, r_j);  finish = start + s_j
      constraint: finish <= d_j                                   (hard deadline)
      energy:     e_k - sum(dist) - hover * sum(s_j) - dist(last, depot) >= reserve_k
  * Objective  J = alpha * sum(w_j served) - gamma * distance_km - delta * #reassigned
"""
from __future__ import annotations

import numpy as np


class Problem:
    def __init__(self, t0, depot, uav_ids, start_xy, ready, energy, speed, reserve,
                 task_ids, task_xy, release, deadline, service, reward, prev_assign, objective, hover):
        self.t0 = float(t0)
        self.uav_ids = list(uav_ids)
        self.task_ids = list(task_ids)
        self.M, self.N = len(self.uav_ids), len(self.task_ids)
        self.depot = tuple(depot)
        self.start_xy = np.asarray(start_xy, float).reshape(-1, 2)
        self.task_xy = np.asarray(task_xy, float).reshape(-1, 2)
        coords = np.vstack([self.task_xy, np.asarray(depot, float)[None, :], self.start_xy])
        D = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
        self.Dn = D
        self.D = D.tolist()                     # python lists are faster in the inner loops
        self.ready = [float(v) for v in ready]
        self.energy = [float(v) for v in energy]
        self.speed = [float(v) for v in speed]
        self.reserve = [float(v) for v in reserve]
        self.rel = [float(v) for v in release]
        self.dl = [float(v) for v in deadline]
        self.sv = [float(v) for v in service]
        self.w = [float(v) for v in reward]
        self.prev = [int(v) for v in prev_assign]  # local uav index previously assigned, -1 = none
        self.alpha = float(objective["alpha"])
        self.gamma = float(objective["gamma"]) / 1000.0  # per metre
        self.delta = float(objective["delta"])
        self.hover = float(hover)
        self.scale = self.alpha * sum(self.w) if self.N else 1.0   # reward scale (normaliser)
        self.hopeless = {j for j in range(self.N) if not any(self.route_eval(k, [j])[0] for k in range(self.M))}

    # ------------------------------------------------------------------ evaluation
    def route_eval(self, k: int, seq) -> tuple[bool, float]:
        """(feasible, distance incl. return). The empty route is always allowed."""
        D, N = self.D, self.N
        prev = N + 1 + k
        if not seq:
            return True, D[prev][N]
        t, e, sp = self.ready[k], self.energy[k] - self.reserve[k], self.speed[k]
        rel, dl, sv, hv = self.rel, self.dl, self.sv, self.hover
        dist = 0.0
        for j in seq:
            d = D[prev][j]
            t += d / sp
            if t < rel[j]:
                t = rel[j]
            t += sv[j]
            if t > dl[j]:
                return False, 0.0
            dist += d
            e -= d + hv * sv[j]
            prev = j
        d = D[prev][N]
        if e - d < 0.0:
            return False, 0.0
        return True, dist + d

    def task_value(self, j: int, k: int) -> float:
        """Reward of serving task j with UAV k, minus the plan-stability penalty."""
        return self.alpha * self.w[j] - (self.delta if (self.prev[j] >= 0 and self.prev[j] != k) else 0.0)

    def route_value(self, k: int, seq, dist: float) -> float:
        return sum(self.task_value(j, k) for j in seq) - self.gamma * dist

    def schedule(self, k: int, seq, start_time: float | None = None, skip_infeasible: bool = False):
        """Detailed timing of a route. With skip_infeasible, tasks that would violate their deadline or
        the energy reserve are skipped (used for execution with a delayed start).
        Returns (entries[(j, depart, arrive, start, finish)], skipped, distance incl. return, energy_left)."""
        D, N = self.D, self.N
        prev = N + 1 + k
        t = self.ready[k] if start_time is None else max(self.ready[k], start_time)
        e = self.energy[k]
        entries, skipped, dist = [], [], 0.0
        for j in seq:
            d = D[prev][j]
            arrive = t + d / self.speed[k]
            start = max(arrive, self.rel[j])
            finish = start + self.sv[j]
            e_after = e - d - self.hover * self.sv[j]
            if finish > self.dl[j] or e_after - D[j][N] < self.reserve[k]:
                if skip_infeasible:
                    skipped.append(j)
                    continue
                raise ValueError(f"infeasible route for uav {k} at task {j}")
            entries.append((j, t, arrive, start, finish))
            dist += d
            e = e_after
            t = finish
            prev = j
        dist += D[prev][N]
        return entries, skipped, dist, e - D[prev][N]


class Solution:
    """Routes (local task indices per local UAV) + cached distances + unassigned set."""
    __slots__ = ("routes", "dist", "unassigned")

    def __init__(self, P: Problem, routes, unassigned=None, dist=None):
        self.routes = [list(r) for r in routes]
        if dist is None:
            dist = []
            for k, r in enumerate(self.routes):
                ok, d = P.route_eval(k, r)
                if not ok:
                    raise ValueError(f"infeasible route {k}: {r}")
                dist.append(d)
        self.dist = list(dist)
        if unassigned is None:
            assigned = {j for r in self.routes for j in r}
            unassigned = set(range(P.N)) - assigned
        self.unassigned = set(unassigned)

    def copy(self) -> "Solution":
        s = Solution.__new__(Solution)
        s.routes = [r[:] for r in self.routes]
        s.dist = self.dist[:]
        s.unassigned = set(self.unassigned)
        return s

    def objective(self, P: Problem) -> float:
        return sum(P.route_value(k, r, d) for k, (r, d) in enumerate(zip(self.routes, self.dist)))

    def n_assigned(self) -> int:
        return sum(len(r) for r in self.routes)


def empty_solution(P: Problem) -> Solution:
    return Solution(P, [[] for _ in range(P.M)])


def validate(P: Problem, sol: Solution) -> list[str]:
    """Independent feasibility checker (used by tests and before publishing any plan)."""
    errors = []
    seen = set()
    for k, r in enumerate(sol.routes):
        for j in r:
            if j in seen:
                errors.append(f"task {j} assigned twice")
            seen.add(j)
        try:
            P.schedule(k, r)
        except ValueError as ex:
            errors.append(str(ex))
    if seen & sol.unassigned:
        errors.append("task both assigned and unassigned")
    if seen | sol.unassigned != set(range(P.N)):
        errors.append("task set mismatch")
    return errors


def delayed_value(P: Problem, sol: Solution, delay_s: float) -> tuple[float, int]:
    """J of `sol` if it is published `delay_s` mission-seconds after t0: UAVs that are already ready
    must wait, tasks that become infeasible are skipped. Returns (J_eff, #tasks lost)."""
    J, lost = 0.0, 0
    t_pub = P.t0 + delay_s
    for k, r in enumerate(sol.routes):
        if delay_s <= 0 or P.ready[k] >= t_pub:
            J += P.route_value(k, r, sol.dist[k])
            continue
        entries, skipped, dist, _ = P.schedule(k, r, start_time=t_pub, skip_infeasible=True)
        J += sum(P.task_value(e[0], k) for e in entries) - P.gamma * dist
        lost += len(skipped)
    return J, lost
