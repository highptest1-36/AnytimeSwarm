# Protocol V7 — Study 7: late-cost model of the cost-aware fallback and errors outside the calibrated model

Written 2026-11-02 before any study-7 held-out run. Frozen with the files listed in `results/frozen_study7_sha256.txt`
(script `tools/p7_freeze.sh`); the held-out runner `tools/run_study7.sh` checks the hashes before it starts.
Motivation: external review of the manuscript (docs/15_PLAN_REVIEW_RESPONSE.md, comments C1 and C5/C6).

## 1. Questions

7a. Studies 5 and 6 ran the cost-aware fallback with the break-even probability of a late cost proportional to the task
reward, theta = lam / (1 + lam), but scored the runs with a fixed cost per late arrival, u_lam = U - lam n_late / n,
i.e. c_j = lam w_bar. Rewards are 1, 2, 3 or 5 (w_bar = 2.1). Does the rule derived for the scored cost,
theta_j = lam w_bar / (w_j + lam w_bar), do better on that score, and does each rule hold against a proportional
buffer tuned for its own score?

7b. Is the advantage of the proposed planning model and of the cost-aware fallback robust when the execution errors
have a structure that the calibrated affine Gaussian model does not describe?

## 2. Seeds and matrix

- Development: seeds 0-9 only (`tools/p7_dev.sh`, results/tier_b/dev7a.csv, dev7b.csv, dev7b_lat.csv).
- Held-out 7a: seeds 13000-13029 (270 missions), exec mid/high, latency high, kappa 10/50/200, windows 1/0.5
  (12 configurations), config experiments/configs/S7a_B.yaml.
- Held-out 7b: seeds 14000-14029 (270 missions), kappa 10/50/200, windows 1/0.5, conditions
  high_gauss (control, draw-for-draw identical to the calibrated high level), high_t3, high_outlier, high_uavbias with
  latency high (S7b_B.yaml), and high_gauss with latency high_pareto (S7b_lat_B.yaml).
- All study 1-6 seeds are used and are not touched.

## 3. Methods

All methods: ALNS 40 ms, periodic trigger 60 s, everything else as in studies 4-6.

7a: cost-aware fallback with the proportional cost model (`z=auto4;lam=x`, study 5) and with the fixed cost model
(`z=auto4;lam=x;cost=fee`, w_bar = 2.1 from the generator) for lam in {0.5, 1, 2}; nominal fallback; nominal model;
the members of the proportional-buffer family (c in {0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1.2}, with the nominal fallback
or without fallback) and of the no-fallback family (z in {-0.5, 0, 0.5, 1, 1.5}) selected in section 4.

7b: nominal model, constant 60 s buffer, proportional buffer (c of study 4), proposed model with the nominal fallback,
proposed model with the cost-aware fallback lam = 1 (proportional cost model, as in studies 5 and 6, and fixed cost
model), moment propagation with the cost-aware fallback lam = 1. Error model, z, c and the moment-propagation
parameters are those of the calibrated high level (no re-calibration).

Shifted conditions (journal_core/study7.py, all on top of the high level):
- high_t3: speed and service errors Student-t (3 d.o.f.) scaled to the same standard deviation; speed error clipped at
  +-0.6 instead of +-0.3, service factor at [0.3, 3].
- high_outlier: as high, plus with probability 0.1 per leg an extra delay ~ Exp(mean 90 s).
- high_uavbias: as high, plus one speed bias per UAV and mission ~ N(0, 0.08), clipped at +-0.2 (total +-0.45).
- high_pareto (latency): Pareto delay with the median of the lognormal high level (2 s), tail index 1.5, cap 300 s,
  same message losses. The planner keeps the expected latency of the lognormal level.
Sizes were fixed a priori; the development runs only check the implementation and that no condition is degenerate.

## 4. Development selection (filled from experiments/analyze_dev7.py before the freeze)

Rule (as in study 5): per score (u_lam "fee", u^w_lam "w"), lam, family and disturbance level, the member with the
best mean score over the development missions and configurations. The selection is stored in
journal_core/study7.TUNED7 and is part of the frozen files.

### 4a. Selection (dev7a.csv, 31 320 runs, 90 missions; experiments/analyze_dev7.py)

| score | lam | Prop mid | Prop high | CCnf mid | CCnf high |
|---|---|---|---|---|---|
| u_lam (fee) | 0.5 | c 0.45, nominal fb | c 0.75, nominal fb | z 1 | z 0 |
| u_lam (fee) | 1 | c 0.3, no fb | c 0.45, no fb | z 1 | z 0.5 |
| u_lam (fee) | 2 | c 0.45, no fb | c 0.75, no fb | z 1 | z 0.5 |
| u^w_lam (w) | 0.5 | c 0.45, nominal fb | c 0.75, nominal fb | z 1 | z 0 |
| u^w_lam (w) | 1 | c 0.3, no fb | c 0.6, no fb | z 1 | z 0.5 |
| u^w_lam (w) | 2 | c 0.45, no fb | c 0.75, no fb | z 1 | z 0.5 |

The u_lam selection equals the study 5 selection (journal_core/study5.TUNED), made on the same development seeds.

Development differences, for information only (pp, mean over 90 missions): at lam = 1, CA-fee minus CA-prop was +0.10
on u_1 (sd over missions 2.88), and -1.04 on u^w_1; CA-fee minus the tuned buffer +1.02 on u_1; CA-prop minus the
tuned buffer +0.46 on u^w_1. With sd 2.9 pp, 270 missions resolve about 0.5 pp at 80% power, so H24 is expected to be
small; it is kept as pre-specified because it is the direct test of the review comment.

### 4b. 7b development check (dev7b.csv, dev7b_lat.csv; seeds 0-4, kappa 50; 2 700 runs)

No condition is degenerate. Mean utility of the nominal model: 41.8% (Gaussian control), 39.2% (rare long delays),
42.7% (Student-t), 43.3% (bias per UAV), 41.3% (Pareto latency); the proposed model with the nominal fallback stays
above the nominal model under every condition (+4.5 to +7.5 pp on these 45 missions). The shift sizes stay as fixed
in section 3; they were not adjusted after this check.

## 5. Primary hypotheses

7a (lam = 1, Holm over three tests):
- H24: CA-fee minus CA-prop on u_1 > 0 (superiority, two-sided bootstrap p).
- H25: CA-fee vs the proportional buffer tuned for u_1: non-inferior at -0.5 pp; superiority tested after NI.
- H26: CA-prop vs the proportional buffer tuned for u^w_1: non-inferior at -0.5 pp; superiority tested after NI.

7b (Holm over ten tests), for each of the five shifted conditions s:
- H27s: proposed model with nominal fallback minus nominal model on U > 0.
- H28s: cost-aware fallback (proportional cost model, lam = 1) minus nominal fallback on u_1 > 0.

## 6. Analysis

experiments/analyze_study7.py: per mission the paired difference averaged over the configurations, paired bootstrap
over missions (10 000 resamples, seed 0), 95% percentile CI. Secondary and descriptive: lam 0.5 and 2, both scores, the
mirror comparison on u^w (CA-prop minus CA-fee), the no-fallback family, regimes, the control condition, every method
minus the nominal model per condition, calibration (ECE, Brier, upper tail) per condition (experiments/paper_calib.py),
seed-cluster bootstrap as sensitivity (experiments/robust_cluster.py style).

## 7. Reporting

All outcomes are reported, including unsupported or reversed hypotheses. Deviations are logged in section 8.

## 8. Deviations

(none yet)
