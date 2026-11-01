"""Study 6: a published task-allocation algorithm as baseline, and the cost-aware fallback for moment propagation.

CBBA. The consensus-based bundle algorithm of Choi, Brunet and How (IEEE T-RO 2009) is the standard auction method for
multi-UAV task allocation. Every agent builds a bundle by adding, one at a time, the task with the largest marginal
score among those on which it can outbid the current winner; the marginal score of task j for agent k is the largest
increase of the route value P.route_value over all feasible insertion positions of j into the path of k. In the
consensus phase, the highest bid wins every task (ties to the lower agent index), and an agent that is outbid on a task
releases it together with every task it added after it. With time windows, the marginal score of a task can grow as
other tasks are added, which breaks the diminishing-marginal-gain property on which the convergence of CBBA rests; the
bids are therefore warped as proposed by Johnson, Choi, Ponda and How (CDC 2012), so that a bid never exceeds the
previous bid of the same bundle, which restores convergence. The two phases alternate until no bundle changes. The network
is fully connected, so one consensus round shares all bids. CBBA is run from scratch at every planning call, as in
its dynamic use, with the plan-stability penalty of the objective in the score; it is not an anytime method and stops
at convergence or at the hard budget of the call, after which the last consensus state (conflict-free, every path a
subsequence of a feasible path) is published. Its planning time is measured like that of every other method.

Moment propagation with the cost-aware fallback. Study 5 replaced the nominal deadline of a given-up task by
min(d, d~(z_lam)) for the closed-form model. Moment propagation has a probability of meeting the deadline too, so the
same rule applies: tasks are protected at z_p = max(z, z_lam), and a task that moment propagation gives up is accepted
if its nominal finish meets the deadline and E[F] + z_lam sd[F] <= d.

The frozen modules of studies 2-5 are not modified; this module wraps them.
"""
from __future__ import annotations

import copy
import math

from anytimeswarm.algorithms.insertion import best_in_route
from anytimeswarm.algorithms.repair import filter_route
from anytimeswarm.simulator.problem import Solution, validate
from anytimeswarm.utils import now_ms

from .risk import ErrorModel
from .study2 import solve2
from .study4 import _ISQ2PI, _SQ2, MPProblem, mp_problem
from .study5 import cost_fallback_problem, solve5, z_of_cost

TIE = 1e-9


# ---------------------------------------------------------------------------------------------- CBBA
def cbba(P, budget_ms: float, clock=now_ms, t0: float | None = None, max_rounds: int = 200):
    """CBBA with a fully connected network on problem P -> (Solution, rounds, stop reason)."""
    t0 = clock() if t0 is None else t0
    M, N = P.M, P.N
    sol = Solution(P, [[] for _ in range(M)])
    bundle = [[] for _ in range(M)]          # tasks in the order of addition
    bid = [dict() for _ in range(M)]         # bid of agent k on each task of its bundle
    win_k, win_y = [-1] * N, [0.0] * N
    free = [j for j in range(N) if j not in P.hopeless]
    rounds, reason = 0, "rounds"
    while rounds < max_rounds:
        rounds += 1
        # bundle construction, given the winning bids of the last consensus
        for k in range(M):
            while True:
                best = None
                cap = bid[k][bundle[k][-1]] if bundle[k] else math.inf
                for j in free:
                    if j in bid[k]:
                        continue
                    o = best_in_route(P, sol, k, j)
                    if o is None or o[0] <= 0.0:
                        continue
                    c = min(o[0], cap)          # bid warping (Johnson et al. 2012): bids never increase in a bundle
                    if c > win_y[j] + TIE or (abs(c - win_y[j]) <= TIE and (win_k[j] < 0 or k < win_k[j])):
                        if best is None or c > best[0]:
                            best = (c, j, o[1], o[2])
                if best is None:
                    break
                c, j, p, d = best
                sol.routes[k].insert(p, j)
                sol.dist[k] = d
                bundle[k].append(j)
                bid[k][j] = c
                if clock() - t0 > budget_ms:
                    break
        # consensus: the highest bid wins; an outbid agent releases the task and every task added after it
        new_k, new_y = [-1] * N, [0.0] * N
        for k in range(M):
            for j, c in bid[k].items():
                if new_k[j] < 0 or c > new_y[j] + TIE or (abs(c - new_y[j]) <= TIE and k < new_k[j]):
                    new_k[j], new_y[j] = k, c
        changed = False
        for k in range(M):
            for i, j in enumerate(bundle[k]):
                if new_k[j] != k:
                    for jj in bundle[k][i:]:
                        del bid[k][jj]
                        sol.routes[k].remove(jj)
                    del bundle[k][i:]
                    sol.dist[k] = P.route_eval(k, sol.routes[k])[1]
                    changed = True
                    break
        win_k, win_y = [-1] * N, [0.0] * N
        for k in range(M):
            for j, c in bid[k].items():
                win_k[j], win_y[j] = k, c
        if not changed:
            reason = "converged"
            break
        if clock() - t0 > budget_ms:
            reason = "budget"
            break
    sol.unassigned = set(range(N)) - {j for r in sol.routes for j in r}
    return sol, rounds, reason


def solve_cbba(P, Q, budget_ms: float, check: bool = True) -> dict:
    clock = now_ms
    t0 = clock()
    sol, rounds, reason = cbba(Q, budget_ms, clock, t0)
    out = {"method": "cbba", "t_first_feasible_ms": clock() - t0, "iters": rounds, "stop_reason": reason,
           "elapsed_ms": clock() - t0, "solution": sol, "J": sol.objective(P), "n_assigned": sol.n_assigned(),
           "trace": None, "J0": None}
    if check:
        errs = validate(Q, sol)
        if errs:
            raise RuntimeError(f"cbba produced an infeasible plan: {errs[:3]}")
    return out


# ---------------------------------------------------------------------------------------------- moment propagation
class MPCostProblem(MPProblem):
    """Moment propagation in which the given-up tasks (relax) are checked at the safety factor self._zfb."""

    def route_eval(self, k, seq):
        D, N = self.D, self.N
        prev = N + 1 + k
        if not seq:
            return True, D[prev][N]
        t, e, sp = self.ready[k], self.energy[k] - self.reserve[k], self.speed[k]
        rel, dl, sv, hv = self.rel, self.dl, self.sv, self.hover
        a1, c, cv, as1, cvs, z, relax = self._mp
        zfb = self._zfb
        mu, var = t, 0.0
        dist = 0.0
        for j in seq:
            d = D[prev][j]
            tl = d / sp
            t += tl
            mu += a1 * tl + c
            var += (cv * tl) ** 2
            r = rel[j]
            if t < r:
                t = r
            if var > 0.0:
                sd = math.sqrt(var)
                al = (mu - r) / sd
                if al < 8.0:
                    Ph = 0.5 * (1.0 + math.erf(al / _SQ2))
                    ph = _ISQ2PI * math.exp(-0.5 * al * al)
                    m1 = mu * Ph + r * (1.0 - Ph) + sd * ph
                    m2 = (mu * mu + var) * Ph + r * r * (1.0 - Ph) + (mu + r) * sd * ph
                    mu, var = m1, max(m2 - m1 * m1, 0.0)
            elif mu < r:
                mu = r
            s = sv[j]
            t += s
            mu += as1 * s
            var += (cvs * s) ** 2
            if t > dl[j] or mu + (zfb if j in relax else z) * math.sqrt(var) > dl[j]:
                return False, 0.0
            dist += d
            e -= d + hv * s
            prev = j
        d = D[prev][N]
        if e - d < 0.0:
            return False, 0.0
        return True, dist + d


_MPC_CLS = {}


def mp_cost_problem(P, mp: dict, z: float, lam: float):
    """Copy of P with moment propagation and the cost-aware fallback for late cost lam."""
    if lam <= 0.0:
        return mp_problem(P, mp, z, "nominal")
    z_l = z_of_cost(lam)
    z_p = max(z, z_l)
    base_cls = type(P)
    if base_cls not in _MPC_CLS:
        _MPC_CLS[base_cls] = type("MPC" + base_cls.__name__, (MPCostProblem, base_cls),
                                  {"_base_schedule": base_cls.schedule})
    Q = copy.copy(P)
    Q.__class__ = _MPC_CLS[base_cls]
    Q._mp = (1.0 + mp["a"], mp["c"], mp["cv"], 1.0 + mp["a_s"], mp["cv_s"], float(z_p), frozenset())
    Q._zfb = float(z_l)
    Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
    base_hopeless = {j for j in range(P.N) if not any(P.route_eval(k, [j])[0] for k in range(P.M))}
    lost = frozenset(Q.hopeless - base_hopeless)
    n_fb = 0
    if lost and z_l < z_p:
        Q._mp = Q._mp[:-1] + (lost,)
        Q.hopeless = {j for j in range(Q.N) if not any(Q.route_eval(k, [j])[0] for k in range(Q.M))}
        n_fb = len(lost - Q.hopeless)
    Q.n_fallback = n_fb
    return Q


def solve_mp(base, P, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, ms_per_task,
             check=True) -> dict:
    """Search on the moment-propagation problem Q, with the route filter of study 4 before publication."""
    e = err or ErrorModel()
    spread = ErrorModel(e.name, 0.0, 0.0, e.s0, e.s1, e.n)
    out = solve2(base, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, spread, latency_mean_s, None,
                 ms_per_task, None, False)
    sol, n_fix = out["solution"], 0
    if any(not Q.route_eval(k, r)[0] for k, r in enumerate(sol.routes)):
        routes = []
        for k, r in enumerate(sol.routes):
            f = filter_route(Q, k, r)
            n_fix += len(r) - len(f)
            routes.append(f)
        sol = Solution(Q, routes)
    if check:
        errs = validate(Q, sol)
        if errs:
            raise RuntimeError(f"{base} produced an infeasible plan: {errs[:3]}")
    out.update(solution=sol, J=sol.objective(P), n_fallback=Q.n_fallback, n_mp_fix=n_fix, n_assigned=sol.n_assigned())
    return out


# ---------------------------------------------------------------------------------------------- planner
def solve6(base: str, P, old_routes, budget_ms: float, cfg: dict, seed: int = 0, predictor=None,
           kappa: float = 1.0, err: ErrorModel | None = None, latency_mean_s: float = 0.0, z: float | None = None,
           ms_per_task: float | None = None, buf_s: float | None = None, check: bool = True,
           lam: float | None = None, mp: dict | None = None, z_mp: float | None = None, **kw5) -> dict:
    """solve5 extended by
        base "cbba"   CBBA on the nominal model, or with lam (and z) on the proposed model with the cost-aware fallback,
        mp with lam   moment propagation with the cost-aware fallback.
    Everything else is passed to study5.solve5 unchanged."""
    if base == "cbba":
        Q = cost_fallback_problem(P, err or ErrorModel(), z, lam) if lam is not None else P
        return solve_cbba(P, Q, budget_ms, check)
    if mp is not None and lam is not None:
        Q = mp_cost_problem(P, mp, z_mp, lam)
        return solve_mp(base, P, Q, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s,
                        ms_per_task, check)
    if mp is not None:
        kw5.update(mp=mp, z_mp=z_mp)
    return solve5(base, P, old_routes, budget_ms, cfg, seed, predictor, kappa, err, latency_mean_s, z, ms_per_task,
                  buf_s, check, lam=lam, **kw5)
