# Protocol V8 — Study 8: planning budget, an independent scenario family, and the cost-aware fallback in tier C

Sections 1-3, 5 (rules) and 6-8 written 2026-11-04 before any study-8 run, development runs included, and committed
before the first one. Sections 4a, 4b and 5a are filled from development and pilot runs before the freeze. Frozen with
the files listed in `results/frozen_study8_sha256.txt` (script `tools/p8_freeze.sh`); the held-out runners
`tools/run_study8.sh` (tier B) and `tools/run_study8c.sh` (tier C) check the hashes before they start.
Motivation: third external review of the manuscript (validation plan: planning budget, scenario family, cost-aware
fallback in PX4 SITL; no field flights).

## 1. Questions

8a. How does the score of the proposed replanner and of its strongest competitors depend on the ALNS planning budget
when the publication delay charges the whole planning call? Does the closed form keep its score at budgets where moment
propagation, which evaluates every leg of a route, loses it?

8b. Do the gains of the proposed model and of the cost-aware fallback hold on a family of missions specified
independently of the conference generator, with every model and tuned parameter transferred without re-tuning?

8c. Does the cost-aware fallback improve on the nominal fallback in PX4 software-in-the-loop flights, as it did in
tier B (studies 5 and 7)?

## 2. Common to all parts

- Planning-call timing. Studies 2-7 charged the search call (repair plus ALNS) to the publication delay; the planning
  model (effective deadlines, fallback, moment propagation, the set of tasks no route can serve) is built before that
  call and moment propagation filters the routes after it. Study 8 charges the whole call from the construction of the
  model to the return of the solver (journal_core/study8.timed), in tier B and in tier C, and records the search time
  separately. The budget B remains the ALNS budget, measured from the start of the repair as before.
- Scores: utility U (share of the total reward served on time) and u_1 = U - n_late / n (a late arrival costs the
  mean task reward, the score of studies 5-7). u_1 is the primary score of every study-8 hypothesis except H34.
- Seeds. Every seed of studies 1-7 is used and is not touched. Development: tier B seeds 0-9, tier C seeds 0-2.
  Pilot seeds 19000-19099: tier B counterpart of tier C missions only, to size study 8c; never used for a
  confirmatory test. Held-out: 15000-15029 (8a), 16000-16029 (8b), 17000-17019 (8c, tier C and its tier B
  counterpart, number from section 5a).
- Machine: the laptop of studies 1-7 (WSL2 Ubuntu 24.04), tier B with 4 workers, machine guard as before
  (tools/run_guarded.py), held-out runs only while no other heavy process runs.

## 3. Study 8a, planning budget

Held-out seeds 15000-15029 (270 missions: 3 scales x 3 profiles x 30 seeds), conference family, exec high, latency
high, kappa 10/50/200, windows 1/0.5 (6 configurations), periodic trigger 60 s. Budgets B in {5, 10, 20, 40, 80, 160,
250} ms. Methods at every budget (config experiments/configs/S8a_B.yaml, 35 method strings):

| key | method string (B = budget) | role |
|---|---|---|
| CAfee | `alns_fixed@B~z=auto4;lam=1;cost=fee+periodic:60` | proposed: closed form, cost-aware fallback, fixed late cost |
| CAprop | `alns_fixed@B~z=auto4;lam=1+periodic:60` | closed form, cost-aware fallback, proportional cost model |
| MPCA | `alns_fixed@B~mp=auto;lam=1+periodic:60` | moment propagation, cost-aware fallback (study 6), proportional cost model |
| Prop | `alns_fixed@B~prop=0.45;fb=none+periodic:60` | proportional buffer tuned for u_1 at high disturbances (TUNED7) |
| Nom | `alns_fixed@B+periodic:60` | nominal model |

The safety factor, the buffer slope and the moment-propagation model are those selected at 40 ms in studies 4-7 and
are not re-tuned per budget, so the study measures how each configured method degrades or gains with the budget.
Only high disturbances are run (the level of studies 4C, 7b and 8c, where the fallback and moment propagation differ
most); one level halves the run time of about 8 h. CAprop and MPCA share the cost model, so their difference isolates
the planning model.

## 4. Study 8b, independent scenario family

The family "emergency response" is defined in journal_core/study8.py (module docstring, WORLD8, PROFILES8). It was
specified before any run on it and differs from the conference generator in every structural parameter: a 14 x 7 km
map instead of 10 x 10 km; five incident zones holding 70% of the tasks instead of three holding 50%; 30% urgent
tasks with windows of 90-240 s and the others 240-900 s instead of one class with 180-600 s; service 20-120 s instead
of 30-90 s; release lead 0-60 s instead of 0-120 s; 30% of the tasks known at the start instead of 50%; UAV speeds
8-20 m/s instead of 10-16 m/s; and three new profiles (incidents: eight bursts at front-loaded times with uneven sizes,
each around its own new incident point; attrition: four batches and one, two or three UAV failures from 100 s on;
priorities: four batches and eight deadline cuts). The reward levels and their probabilities are kept, so the mean
reward w_bar = 2.1 used by the fixed-cost rule stays correct, and so are the energy model and the number of UAVs per
scale (5, 10, 20). Random streams are disjoint from those of the conference generator.

### 4a. Load (rule fixed now; value filled from the development run)

Number of tasks per scale = conference number x LOAD8, LOAD8 in {0.6, 0.8, 1.0, 1.25, 1.5}. Rule: run only the nominal
model (`alns_fixed@40+periodic:60`) with nominal execution, no latency, kappa 10, windows 1 on development seeds 0-9 of
both families (90 missions each); choose the LOAD8 whose mean utility U on the new family is closest to the mean U of
the conference family under the same settings. No other method is run before LOAD8 is set.

Result (2026-11-04, tools/p8_dev.sh load, results/tier_b/dev8_load_*.csv, 90 missions each): conference family U 88.67%
(completion 85.99%). New family: LOAD8 0.6 82.86%, 0.8 82.63%, 1.0 83.78%, 1.25 80.89%, 1.5 78.68%. Selected
LOAD8 = 1.0 (|dU| 4.89 pp, the smallest). The utility of the new family hardly changes between 0.6 and 1.0 because a
share of the urgent tasks cannot be reached in time whatever the load; at equal load it is about 5 pp harder.

### 4b. Development check (after 4a)

Every method of the held-out list on development seeds 0-2 (27 missions), exec mid/high, kappa 50, windows 1/0.5, to
check the implementation and that no condition is degenerate. No parameter of the family or of a method is changed
after this check.

Result (tools/p8_dev.sh check, results/tier_b/dev8b_check.csv, 972 runs, no failure): no condition is degenerate.
Mean U of the nominal model 55.5% (mid) and 44.0% (high); halved windows 42.5% against 63.5% with the original
windows (all methods). The other methods range from 37% to 63%; the urgent tasks served on time range from 6% to 30%.
Building the planning model took 0.09 ms per call for the nominal model, 0.25-0.38 ms for the buffers and the model
without fallback, 0.5-1.0 ms for the closed form with a fallback and 0.8-1.4 ms for moment propagation (budget 40 ms).
Nothing was changed after this check.

8a implementation check (tools/p8_dev.sh budget, results/tier_b/dev8a_check.csv, seeds 0-1, exec high, kappa 50,
windows 0.5, 5 and 250 ms; 180 runs, no failure): at 5 ms the whole call took 5.2 ms (nominal) to 6.1 ms (moment
propagation) on average, of which 0.06-1.0 ms was model construction; every call ends slightly above the budget, so
the overrun is reported in milliseconds (over_ms_mean, over_ms_p99) instead of as a share of calls.

### 4c. Held-out matrix

Seeds 16000-16029, scales small8/medium8/large8, profiles incidents/attrition/priorities (270 missions), exec mid/high,
latency high, kappa 10/50/200, windows 1/0.5 (12 configurations), ALNS 40 ms, periodic trigger 60 s. Config
experiments/configs/S8b_B.yaml. Methods, all with parameters transferred from the conference family:

| key | method string | transferred parameter |
|---|---|---|
| Forty | `alns_fixed@40+periodic:60` | - |
| CCfb | `alns_fixed@40~z=auto4;fb=nominal+periodic:60` | z of study 4 |
| CAfee | `alns_fixed@40~z=auto4;lam=1;cost=fee+periodic:60` | z of study 4, w_bar 2.1 |
| CAprop | `alns_fixed@40~z=auto4;lam=1+periodic:60` | z of study 4 |
| MPCA | `alns_fixed@40~mp=auto;lam=1+periodic:60` | moment-propagation model and z of studies 4 and 6 |
| Prop (mid / high) | `alns_fixed@40~prop=0.3;fb=none+periodic:60`, `...prop=0.45;fb=none...` | TUNED7, u_1, lam 1 |
| CCnf (mid / high) | `alns_fixed@40~z=1+periodic:60`, `alns_fixed@40~z=0.5+periodic:60` | TUNED7, u_1, lam 1 |

For Prop and CCnf, the analysis uses the member selected for the disturbance level of the configuration (as in 7a).
The error model of each level is the conference development model (models/error_model_dev.json), not refitted.

## 5. Study 8c, cost-aware fallback in tier C

Missions: tier C missions of the conference family (three X500, fifteen tasks, rescaled as in studies 1-4C), exec
high, windows 0.5, kappa_B 50, periodic trigger 60 s (tier B seconds), PX4 speed factor 2, profiles arrivals,
failures, deadlines. Tier C error model models/error_model_tierc_dev4.json (as study 4C). Methods (tier C syntax):

| key | method string | |
|---|---|---|
| CAfee | `alns_fixed@40~z=0.5,lam=1,cost=fee` | proposed (z = study 4 value for high) |
| CCfb | `alns_fixed@40~z=0.5,fb=nominal` | nominal fallback |
| Prop | `alns_fixed@40~prop=0.45,fb=none` | proportional buffer tuned for u_1 (TUNED7) |

Runners: journal_ros/run_batch8.sh / run_mission8.sh with journal_ros/study8c.py (same planner, journal_core.study8.solve8,
as the tier B counterpart experiments/b8c_gz.py). Order: seeds outer, profiles, methods inner (interleaved in time).

### 5a. Pilot and sample size (rule fixed now; numbers filled from the pilot)

Pilot: experiments/b8c_gz.py on pilot seeds 19000-19099 (300 missions), the three methods, exec high, latency none,
kappa 50, windows 0.5. From it: d = mean of CAfee - CCfb on u_1 over missions, s_B = its standard deviation over
missions. Planning values: effect delta = 0.75 d (development estimates overstated the tier C effect in study 4C) and
s_C = 1.3 s_B (in study 4C, tier C intervals were up to 1.27 times as wide as the tier B intervals of the same
missions). Missions n = ceil((1.96 + 0.84)^2 s_C^2 / delta^2) (80% power, two-sided 0.05), rounded up to a multiple of
6 (three profiles, an even number of seeds for the interim look), and bounded to [36, 90] missions (90 missions are
270 flights, about 20 h). If d <= 0 or the bound 90 is reached, 90 missions are flown and the power at delta is stated.

Before the freeze, three smoke flights (development seed 0, profile arrivals, one per method) check the stack; they
are not analysed.

Pilot result (2026-11-04, tools/p8_dev.sh pilot, results/tier_b/pilot8c_gz.csv, 300 missions x 3 methods, no failure):

| CAfee - CCfb, per mission | mean | sd | missions by the rule |
|---|---|---|---|
| u_1 | +2.87 pp | 15.07 pp | 651 (bound: 90; power at 90 missions about 18%) |
| late arrivals | -0.70 | 1.12 | 60 |
| U | -1.82 pp | 10.20 pp | - |

Mean late arrivals per mission: CCfb 2.01, CAfee 1.31, Prop 0.80. With fifteen tasks, one late arrival moves u_1 by
6.7 pp, so the net score of a single mission is coarse and its difference between two methods varies widely. A
powered test of u_1 in tier C would need about 650 missions (about 2 000 flights), which the laptop cannot fly.

Design decision after the pilot, before the freeze and before any held-out flight (deviation 1 in section 9): the
primary endpoint of 8c is the number of late arrivals per mission, the quantity on which the cost-aware fallback acts
and which the pilot sizes at n = 60 missions by the rule above (delta = 0.75 x 0.70, s_C = 1.3 x 1.12; 60 is a
multiple of 6). The net score u_1 is tested second in a fixed sequence (section 6) and reported with its interval and
its tier B prediction whatever the outcome; it is not powered, and the manuscript says so. With 60 missions the planned
look is single: the interim look of study 4C is dropped because stopping early would leave the secondary comparisons
even less precise.

### 5b. Held-out flights

Seeds 17000-17019 (20 seeds x 3 profiles = 60 missions, 180 flights), one analysis after all flights, two-sided level
0.05. Valid real-time factor [1.6, 2.2]; a run outside is repeated once with the same seed and replaces the original
(sensitivity analysis with the originals). A flight that ends without a result (stack failure) is retried by the
runner (twice per pass, and once more in the pass that repeats the invalid runs), as in study 4C. A mission enters
the analysis when all three methods have a valid run. Tier B counterpart on the same held-out seeds
(experiments/configs/S8c_B_gz.yaml), run before the flights. Order of the held-out runs (tools/run_study8.sh): tier B
counterpart of 8c, tier C flights, 8b, 8a.

## 6. Primary hypotheses

8a (Holm over fourteen tests; two-sided superiority on u_1):
- H29_B for each budget B: CAprop - MPCA differs from zero. Outcome per budget: closed form better, moment propagation
  better, or no significant difference.
- H30_B for each budget B: CAfee - Prop differs from zero (same outcomes).

8b (Holm over four tests):
- H31: CAfee - Forty on u_1 > 0 (superiority).
- H32: CAfee - CCfb on u_1 > 0 (superiority).
- H33: CAfee vs Prop (tuned) on u_1: non-inferior at -0.5 pp; superiority tested after non-inferiority.
- H34: CCfb - Forty on U > 0 (superiority; the planning-model gain without late cost).

8c (fixed sequence at two-sided 0.05; H36 is tested only if H35 is supported):
- H35: CAfee - CCfb on the number of late arrivals per mission in tier C differs from zero; supported if the
  difference is negative and p < 0.05.
- H36: CAfee - CCfb on u_1 in tier C differs from zero; supported if positive and p < 0.05 (not powered, see 5a).

## 7. Analysis

experiments/analyze_study8.py (8a, 8b) and experiments/analyze_study8c.py (8c). As in studies
2-7: per mission the paired difference averaged over the configurations, paired bootstrap over missions (10 000
resamples, seed 0), 95% percentile interval, two-sided p (non-inferiority: one-sided share at or below the margin),
Holm within each family. Secondary and descriptive:
- 8a: U and u_1 per budget, method and kappa; the nominal model; iterations per search millisecond; whole-call time
  (mean, 99th percentile and maximum, time above the budget) and model-construction time per method; the smallest
  budget at which each method comes within 0.5 pp of its best mean u_1.
- 8b: U and u_1 of every method per disturbance level and per profile; CAprop, MPCA and CCnf; urgent tasks served on
  time; calibration of the transferred error model (expected calibration error, upper tail p >= 0.8); comparison of
  the effect sizes with the conference family (study 7a), descriptive.
- 8c: CAfee - Prop (secondary), every tier C comparison against its tier B prediction on the same missions, late
  arrivals, planning time, RTF sensitivity.
- Sensitivity: seed-cluster bootstrap for 8a and 8b (as experiments/robust_cluster.py).
- Peak memory of a planning call (tracemalloc), measured afterwards on development missions because tracemalloc slows
  the planner; descriptive only (experiments/paper_profile8.py, not frozen).
- Figures: experiments/paper_s8fig.py, not frozen, presentation only (same paired bootstrap as the analyses; it adds
  no statistic). The analysis scripts were run on the development files (results/study8/report_dev.md,
  report_c_dev.md) before the freeze to check that they run as specified.

## 8. Reporting

All outcomes are reported, including unsupported or reversed hypotheses and a negative or inconclusive tier C result.
The manuscript states that the family of study 8b is synthetic (a generalisation across mission structures, not a field
validation) and that tier C is software-in-the-loop simulation. Deviations are logged in section 9.

## 9. Deviations

1. (2026-11-04, after the pilot of section 5a, before the freeze and before any held-out run) The rule of section 5a
   gave 651 missions for the u_1 endpoint of 8c, above the bound of 90, where the power would have been about 18%.
   The primary endpoint of 8c was changed from u_1 to the number of late arrivals per mission (H35, n = 60 by the same
   rule), u_1 became the second test of a fixed sequence (H36), and the interim look was dropped. The commit of the
   first version of this protocol (198154b) records the original rule.
