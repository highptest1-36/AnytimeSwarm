# Held-out results (pre-registered analysis)

## H1-H3: tier B primary matrix

270 held-out missions x 16 configurations. Utility differences in percentage points (pp).

Mean over all missions and configurations:

|                                  |   utility |   plan_ms |   replans |   late |
|:---------------------------------|----------:|----------:|----------:|-------:|
| ALNS 250 ms                      |    0.7148 |  250.129  |   15.5178 | 6.1544 |
| ALNS 40 ms                       |    0.7193 |   40.1207 |   15.5104 | 6.6502 |
| ALNS stagnation                  |    0.7197 |   59.9262 |   15.525  | 6.4755 |
| AnytimeSwarm                     |    0.7204 |   48.1692 |   15.5181 | 6.6356 |
| AnytimeSwarm w/o delay cost      |    0.7213 |   54.0941 |   15.487  | 6.3486 |
| AnytimeSwarm-R                   |    0.7225 |   41.0762 |   15.5153 | 6.5562 |
| AnytimeSwarm-R, zero error model |    0.7202 |   48.2452 |   15.5359 | 6.6521 |
| Regret-2 repair                  |    0.6886 |    0.9619 |   15.5752 | 6.6373 |

H1 (pooled, Holm-adjusted):

| baseline | diff pp [95% CI] | p | p Holm |
|---|---|---|---|
| ALNS 40 ms | +0.32 [+0.01, +0.63] | 0.0426 | 0.1278 |
| AnytimeSwarm | +0.21 [-0.08, +0.52] | 0.1538 | 0.3076 |
| ALNS stagnation | +0.28 [-0.11, +0.67] | 0.1632 | 0.3076 |

Secondary pooled comparisons (not part of the H1 family):

| baseline | diff pp [95% CI] | p |
|---|---|---|
| ALNS 250 ms | +0.77 [+0.31, +1.25] | 0.0014 |
| AnytimeSwarm w/o delay cost | +0.12 [-0.20, +0.45] | 0.4878 |
| Regret-2 repair | +3.39 [+2.76, +4.04] | 0.0000 |
| AnytimeSwarm-R, zero error model | +0.23 [-0.06, +0.54] | 0.1298 |

H2 (compute, AnytimeSwarm-R minus AnytimeSwarm, ms per planning call): -7.09 [-7.68, -6.53].

Per-configuration comparisons of AnytimeSwarm-R (count of significant +, 0, -):

| baseline        |   + |   0 |
|:----------------|----:|----:|
| alns_fixed      |   6 |  10 |
| alns_fixed@40   |   2 |  14 |
| alns_stagnation |   1 |  15 |
| anytime         |   0 |  16 |

H3: periodic (60 s) minus event-only replanning, pooled per method:

| method | diff pp [95% CI] |
|---|---|
| ALNS 250 ms | +1.56 [+1.25, +1.86] |
| ALNS 40 ms | +1.47 [+1.19, +1.75] |
| ALNS stagnation | +1.47 [+1.20, +1.73] |
| AnytimeSwarm | +1.51 [+1.25, +1.77] |
| AnytimeSwarm w/o delay cost | +1.42 [+1.15, +1.70] |
| AnytimeSwarm-R | +1.56 [+1.26, +1.84] |
| AnytimeSwarm-R, zero error model | +1.42 [+1.16, +1.68] |
| Regret-2 repair | +1.29 [+1.02, +1.56] |

- trigger event: AnytimeSwarm-R vs ALNS 40 ms +0.27 [-0.07, +0.62]; vs AnytimeSwarm +0.19 [-0.15, +0.55]
- trigger periodic:60: AnytimeSwarm-R vs ALNS 40 ms +0.36 [+0.03, +0.70]; vs AnytimeSwarm +0.24 [-0.07, +0.55]

Mean utility per configuration:

|                                      |   ALNS 250 ms |   ALNS 40 ms |   ALNS stagnation |   AnytimeSwarm |   AnytimeSwarm w/o delay cost |   AnytimeSwarm-R |   AnytimeSwarm-R, zero error model |   Regret-2 repair |
|:-------------------------------------|--------------:|-------------:|------------------:|---------------:|------------------------------:|-----------------:|-----------------------------------:|------------------:|
| ('low', 'high', 10.0, 'event')       |        0.7745 |       0.7735 |            0.7746 |         0.7742 |                        0.7766 |           0.7756 |                             0.7747 |            0.74   |
| ('low', 'high', 10.0, 'periodic:60') |        0.784  |       0.7842 |            0.787  |         0.7879 |                        0.7871 |           0.7889 |                             0.7873 |            0.7507 |
| ('low', 'high', 50.0, 'event')       |        0.7565 |       0.7703 |            0.7697 |         0.7711 |                        0.7708 |           0.7709 |                             0.7725 |            0.7398 |
| ('low', 'high', 50.0, 'periodic:60') |        0.7715 |       0.7836 |            0.7834 |         0.7861 |                        0.7855 |           0.7874 |                             0.7876 |            0.7501 |
| ('low', 'none', 10.0, 'event')       |        0.7771 |       0.7764 |            0.7777 |         0.7776 |                        0.78   |           0.7804 |                             0.7792 |            0.7423 |
| ('low', 'none', 10.0, 'periodic:60') |        0.7903 |       0.7876 |            0.7893 |         0.791  |                        0.79   |           0.7946 |                             0.7899 |            0.7518 |
| ('low', 'none', 50.0, 'event')       |        0.762  |       0.7737 |            0.7731 |         0.7724 |                        0.7736 |           0.7777 |                             0.7718 |            0.7417 |
| ('low', 'none', 50.0, 'periodic:60') |        0.7767 |       0.7876 |            0.7856 |         0.788  |                        0.7864 |           0.7903 |                             0.7882 |            0.752  |
| ('mid', 'high', 10.0, 'event')       |        0.6484 |       0.6492 |            0.6506 |         0.651  |                        0.6529 |           0.6531 |                             0.6488 |            0.6222 |
| ('mid', 'high', 10.0, 'periodic:60') |        0.6675 |       0.6679 |            0.6665 |         0.6674 |                        0.6689 |           0.6703 |                             0.6664 |            0.6375 |
| ('mid', 'high', 50.0, 'event')       |        0.6414 |       0.648  |            0.6466 |         0.6471 |                        0.6507 |           0.6496 |                             0.6478 |            0.6224 |
| ('mid', 'high', 50.0, 'periodic:60') |        0.6607 |       0.6642 |            0.6653 |         0.6656 |                        0.6666 |           0.6686 |                             0.6647 |            0.6382 |
| ('mid', 'none', 10.0, 'event')       |        0.6524 |       0.6523 |            0.6556 |         0.6574 |                        0.6569 |           0.6582 |                             0.6574 |            0.6248 |
| ('mid', 'none', 10.0, 'periodic:60') |        0.6694 |       0.6681 |            0.6736 |         0.6684 |                        0.6735 |           0.6726 |                             0.6689 |            0.6401 |
| ('mid', 'none', 50.0, 'event')       |        0.6436 |       0.6528 |            0.6515 |         0.6517 |                        0.6525 |           0.6523 |                             0.6521 |            0.6239 |
| ('mid', 'none', 50.0, 'periodic:60') |        0.6604 |       0.6703 |            0.666  |         0.6689 |                        0.6692 |           0.6696 |                             0.6652 |            0.6401 |
