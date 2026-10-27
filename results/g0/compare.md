# G0 — conference DEV pipeline re-run on Linux vs conference results

Windows = conference run (24/10/2026, Python 3.11.9, Windows 11). Linux = this re-run (WSL2 Ubuntu 24.04, Python 3.11.9, identical package versions, frozen config and frozen predictor).

## 1. Reference solutions (time-limited solvers)

| solver       |   n |   identical |   mean_rel_diff |   max_abs_rel_diff |
|:-------------|----:|------------:|----------------:|-------------------:|
| J_alns_ref   | 531 |    0.992467 |         1.1e-05 |           0.004633 |
| J_ortools    | 351 |    0.988604 |        -0.00035 |           0.073298 |
| best of both | 531 |    0.992467 |         1.1e-05 |           0.004633 |

## 2. Improvement predictor re-trained on Linux traces

Training samples: Windows 52031, Linux 52035. mu rule: Windows mu=1e-05 (mean stop 38.9 ms), Linux mu=1e-05 (mean stop 38.7 ms).

Out-of-fold evaluation:

|               |   Windows |   Linux |
|:--------------|----------:|--------:|
| spearman      |    0.167  |  0.1666 |
| mae_pct       |    0.0113 |  0.0113 |
| auc           |    0.9262 |  0.9215 |
| avg_precision |    0.2489 |  0.2461 |
| positive_rate |    0.0129 |  0.0132 |
| mean_pred     |    0.0068 |  0.0069 |
| mean_true     |    0.0068 |  0.0068 |

Standardised coefficients (cosine similarity 0.997):

|                 |   Windows |   Linux |
|:----------------|----------:|--------:|
| log_elapsed     |   -0.2226 | -0.2265 |
| log_iters       |   -0.5459 | -0.5679 |
| gain_5ms        |   -0.0054 | -0.0182 |
| gain_20ms       |    0.0175 |  0.0208 |
| gain_half       |   -0.0127 |  0.0095 |
| log_since_impr  |   -0.5629 | -0.5249 |
| total_gain      |    0.215  |  0.1993 |
| unassigned_frac |    0.5765 |  0.5426 |
| log_n_tasks     |    0.6937 |  0.7491 |
| log_n_uav       |   -0.0919 | -0.1204 |
| iters_per_ms    |   -0.4845 | -0.4348 |

## 3. Static snapshot benchmark (kappa = 1, mean over 531 snapshots)

Search speed (ALNS iterations per ms, alns_fixed at 500 ms): Windows 8.447, Linux 10.207 (ratio Linux/Windows 1.208).

|                            |   ('regret_pct', 'Windows') |   ('regret_pct', 'Linux') |   ('elapsed_ms', 'Windows') |   ('elapsed_ms', 'Linux') |   ('iters', 'Windows') |   ('iters', 'Linux') |
|:---------------------------|----------------------------:|--------------------------:|----------------------------:|--------------------------:|-----------------------:|---------------------:|
| ('alns_fixed', 20.0)       |                      0.1797 |                    0.1547 |                     20.1168 |                   20.087  |               146.058  |             218.026  |
| ('alns_fixed', 50.0)       |                      0.1276 |                    0.1174 |                     50.1131 |                   50.0776 |               394.797  |             552.395  |
| ('alns_fixed', 100.0)      |                      0.0961 |                    0.093  |                    100.099  |                  100.089  |               850.902  |            1041.51   |
| ('alns_fixed', 250.0)      |                      0.0524 |                    0.0486 |                    250.098  |                  250.129  |              2133.89   |            2508.17   |
| ('alns_fixed', 500.0)      |                      0.0318 |                    0.0275 |                    500.137  |                  500.101  |              4224.21   |            5104.13   |
| ('alns_stagnation', 20.0)  |                      0.2742 |                    0.2195 |                      6.4562 |                    6.3177 |                38.7269 |              57.6798 |
| ('alns_stagnation', 50.0)  |                      0.2062 |                    0.1852 |                     12.2506 |                   11.9219 |                82.7853 |             114.778  |
| ('alns_stagnation', 100.0) |                      0.1345 |                    0.126  |                     23.2715 |                   23.1734 |               176.06   |             214.488  |
| ('alns_stagnation', 250.0) |                      0.1094 |                    0.0985 |                     55.9347 |                   55.9692 |               437.631  |             515.288  |
| ('alns_stagnation', 500.0) |                      0.0762 |                    0.0749 |                    110.698  |                  109.77   |               869.774  |            1033.1    |
| ('anytime', 20.0)          |                      0.1824 |                    0.1588 |                     15.6244 |                   14.1195 |                86.29   |             106.486  |
| ('anytime', 50.0)          |                      0.1343 |                    0.1218 |                     25.3164 |                   22.2069 |               118.478  |             135.885  |
| ('anytime', 100.0)         |                      0.1084 |                    0.1021 |                     29.829  |                   27.9473 |               133.166  |             142.448  |
| ('anytime', 250.0)         |                      0.0732 |                    0.0762 |                     36.1939 |                   33.7938 |               139.164  |             145.81   |
| ('anytime', 500.0)         |                      0.0743 |                    0.0738 |                     38.1422 |                   35.5535 |               140.648  |             147.721  |
| ('anytime_nodelay', 20.0)  |                      0.1832 |                    0.1575 |                     15.4688 |                   14.1064 |                85.9548 |             106.345  |
| ('anytime_nodelay', 50.0)  |                      0.134  |                    0.1226 |                     25.1321 |                   22.1228 |               118.508  |             136.219  |
| ('anytime_nodelay', 100.0) |                      0.1094 |                    0.1047 |                     29.7328 |                   27.6298 |               133.699  |             143.198  |
| ('anytime_nodelay', 250.0) |                      0.0759 |                    0.0743 |                     35.9766 |                   33.6055 |               140.235  |             146.215  |
| ('anytime_nodelay', 500.0) |                      0.0742 |                    0.0713 |                     37.9609 |                   35.3266 |               141.435  |             148.486  |
| ('anytime_noffr', 20.0)    |                      0.2851 |                    0.248  |                     15.5687 |                   14.0562 |                83.8663 |             104.277  |
| ('anytime_noffr', 50.0)    |                      0.1781 |                    0.1531 |                     24.9463 |                   22.0587 |               115.252  |             131.55   |
| ('anytime_noffr', 100.0)   |                      0.1183 |                    0.1049 |                     29.3747 |                   27.5802 |               128.177  |             137.957  |
| ('anytime_noffr', 250.0)   |                      0.0766 |                    0.0776 |                     36.4377 |                   34.3291 |               135.473  |             141.508  |
| ('anytime_noffr', 500.0)   |                      0.0708 |                    0.0742 |                     39.6167 |                   36.8596 |               137.403  |             144.011  |
| ('anytime_online', 20.0)   |                      0.3611 |                    0.2311 |                      5.2004 |                    5.5119 |                24.5179 |              38.9209 |
| ('anytime_online', 50.0)   |                      0.2733 |                    0.207  |                      6.8076 |                    7.0224 |                30.1977 |              44.9058 |
| ('anytime_online', 100.0)  |                      0.2274 |                    0.214  |                      7.5753 |                    7.5529 |                34.8606 |              41.8719 |
| ('anytime_online', 250.0)  |                      0.2302 |                    0.2051 |                      8.0521 |                    8.3133 |                36.2467 |              42.2222 |
| ('anytime_online', 500.0)  |                      0.2298 |                    0.2129 |                      8.2921 |                    8.0588 |                35.9341 |              41.8851 |
| ('greedy_repair', 20.0)    |                      1.2976 |                    1.2984 |                      0.5073 |                    0.4159 |                 0      |               0      |
| ('greedy_repair', 50.0)    |                      1.2976 |                    1.2984 |                      0.5778 |                    0.4823 |                 0      |               0      |
| ('greedy_repair', 100.0)   |                      1.2976 |                    1.2984 |                      0.5216 |                    0.5088 |                 0      |               0      |
| ('greedy_repair', 250.0)   |                      1.2976 |                    1.2984 |                      0.5087 |                    0.5764 |                 0      |               0      |
| ('greedy_repair', 500.0)   |                      1.2976 |                    1.2984 |                      0.512  |                    0.5442 |                 0      |               0      |
| ('ls_fixed', 20.0)         |                      0.8565 |                    0.8574 |                      1.6604 |                    1.3039 |                 0.2957 |               0.2957 |
| ('ls_fixed', 50.0)         |                      0.8565 |                    0.8574 |                      1.8227 |                    1.355  |                 0.2957 |               0.2957 |
| ('ls_fixed', 100.0)        |                      0.8565 |                    0.8574 |                      1.686  |                    1.3451 |                 0.2957 |               0.2957 |
| ('ls_fixed', 250.0)        |                      0.8565 |                    0.8574 |                      1.6721 |                    1.4155 |                 0.2957 |               0.2957 |
| ('ls_fixed', 500.0)        |                      0.8565 |                    0.8574 |                      1.6587 |                    1.4177 |                 0.2957 |               0.2957 |
| ('oracle_stop', 20.0)      |                      0.1798 |                    0.1547 |                      2.1846 |                    2.0206 |               nan      |             nan      |
| ('oracle_stop', 50.0)      |                      0.1278 |                    0.1177 |                      4.0026 |                    3.4479 |               nan      |             nan      |
| ('oracle_stop', 100.0)     |                      0.0967 |                    0.0935 |                      6.3637 |                    6.0394 |               nan      |             nan      |
| ('oracle_stop', 250.0)     |                      0.0537 |                    0.05   |                     12.0993 |                   11.5581 |               nan      |             nan      |
| ('oracle_stop', 500.0)     |                      0.0346 |                    0.0311 |                     17.4838 |                   17.2203 |               nan      |             nan      |
| ('regret_repair', 20.0)    |                      0.891  |                    0.8919 |                      0.4929 |                    0.4    |                 0      |               0      |
| ('regret_repair', 50.0)    |                      0.891  |                    0.8919 |                      0.5441 |                    0.4045 |                 0      |               0      |
| ('regret_repair', 100.0)   |                      0.891  |                    0.8919 |                      0.4993 |                    0.4214 |                 0      |               0      |
| ('regret_repair', 250.0)   |                      0.891  |                    0.8919 |                      0.4911 |                    0.4456 |                 0      |               0      |
| ('regret_repair', 500.0)   |                      0.891  |                    0.8919 |                      0.4952 |                    0.4217 |                 0      |               0      |

## 4. Bootstrap conclusions — static_dev.csv

405 AnytimeSwarm-vs-baseline comparisons on the main metric: sign agrees in 89.6%, significance verdict agrees in 96.0%.

Comparisons whose significance verdict changed:

|   kappa | scale   |   budget_ms | baseline        | metric     |   diff_win |   ci_lo_win |   ci_hi_win |   diff_lin |   ci_lo_lin |   ci_hi_lin |
|--------:|:--------|------------:|:----------------|:-----------|-----------:|------------:|------------:|-----------:|------------:|------------:|
|       1 | large   |          20 | alns_fixed      | regret_pct |     0.0076 |      0.0001 |      0.0203 |     0.0053 |     -0.0006 |      0.0139 |
|       1 | large   |          50 | anytime_noffr   | regret_pct |    -0.0953 |     -0.207  |      0.0038 |    -0.0901 |     -0.191  |     -0.0072 |
|       1 | large   |         500 | anytime_nodelay | regret_pct |     0.0036 |      0      |      0.0108 |     0.0075 |      0.0007 |      0.0163 |
|       1 | medium  |         250 | oracle_stop     | regret_pct |     0.0181 |     -0.0001 |      0.0465 |     0.0287 |      0.0005 |      0.0602 |
|      10 | large   |          50 | alns_fixed      | regret_pct |     0.0101 |      0.0005 |      0.0233 |     0.0042 |     -0.0017 |      0.0123 |
|      10 | large   |          50 | anytime_noffr   | regret_pct |    -0.0986 |     -0.2133 |      0.0034 |    -0.094  |     -0.195  |     -0.0108 |
|      10 | large   |         100 | oracle_stop     | regret_pct |     0.0274 |      0.0082 |      0.0532 |     0.0217 |     -0.0003 |      0.0485 |
|      10 | large   |         500 | anytime_nodelay | regret_pct |     0.0038 |      0      |      0.0113 |     0.0072 |      0.0007 |      0.0153 |
|      10 | medium  |          50 | alns_fixed      | regret_pct |     0.0109 |      0      |      0.0318 |     0.0103 |      0      |      0.0308 |
|      10 | medium  |         100 | alns_fixed      | regret_pct |     0.0094 |      0.0002 |      0.0271 |     0.0143 |     -0.0093 |      0.0433 |
|      10 | medium  |         100 | alns_stagnation | regret_pct |    -0.0167 |     -0.0399 |     -0.0009 |    -0.0067 |     -0.0383 |      0.0241 |
|      50 | large   |          50 | alns_fixed      | regret_pct |     0.0109 |     -0.0003 |      0.0255 |     0.0104 |      0.0012 |      0.0219 |
|      50 | large   |          50 | anytime_noffr   | regret_pct |    -0.1093 |     -0.2268 |     -0.0057 |    -0.0798 |     -0.183  |      0.0063 |
|      50 | large   |         100 | oracle_stop     | regret_pct |     0.0228 |      0.0046 |      0.0456 |     0.0219 |     -0.0021 |      0.0483 |
|      50 | large   |         250 | anytime_noffr   | regret_pct |    -0.0209 |     -0.0635 |      0.0218 |    -0.0641 |     -0.1296 |     -0.0106 |
|      50 | medium  |          50 | alns_fixed      | regret_pct |     0.0109 |      0      |      0.0318 |     0.0103 |      0      |      0.0308 |

## 4. Bootstrap conclusions — closed_loop_dev.csv

45 AnytimeSwarm-vs-baseline comparisons on the main metric: sign agrees in 91.1%, significance verdict agrees in 93.3%.

Comparisons whose significance verdict changed:

|   kappa | scale   | baseline        | metric       |   diff_win |   ci_lo_win |   ci_hi_win |   diff_lin |   ci_lo_lin |   ci_hi_lin |
|--------:|:--------|:----------------|:-------------|-----------:|------------:|------------:|-----------:|------------:|------------:|
|      10 | medium  | alns_fixed      | utility_rate |     0.0111 |      0.0018 |      0.0211 |     0.0074 |     -0.0022 |      0.0174 |
|      10 | medium  | alns_stagnation | utility_rate |     0.0085 |      0.0021 |      0.0164 |     0.0083 |     -0.0011 |      0.019  |
|      50 | large   | alns_stagnation | utility_rate |     0.0042 |     -0.0012 |      0.0096 |     0.0077 |      0.0024 |      0.013  |

## 5. Closed-loop missions (90 DEV missions)

|                         |   ('utility_rate', 'Windows') |   ('utility_rate', 'Linux') |   ('plan_ms_mean', 'Windows') |   ('plan_ms_mean', 'Linux') |
|:------------------------|------------------------------:|----------------------------:|------------------------------:|----------------------------:|
| (1, 'alns_fixed')       |                        0.8971 |                      0.8978 |                      250.097  |                    250.108  |
| (1, 'alns_fixed@40')    |                        0.8889 |                      0.8891 |                       40.1023 |                     40.1023 |
| (1, 'alns_stagnation')  |                        0.8958 |                      0.8947 |                       62.362  |                     62.2013 |
| (1, 'anytime')          |                        0.8973 |                      0.8961 |                       44.81   |                     44.4814 |
| (1, 'anytime_nodelay')  |                        0.8973 |                      0.8976 |                       44.5183 |                     43.5817 |
| (1, 'regret_repair')    |                        0.8484 |                      0.8484 |                        1.3463 |                      0.9133 |
| (10, 'alns_fixed')      |                        0.8902 |                      0.891  |                      250.086  |                    250.111  |
| (10, 'alns_fixed@40')   |                        0.8858 |                      0.886  |                       40.0945 |                     40.1077 |
| (10, 'alns_stagnation') |                        0.8913 |                      0.8903 |                       61.9243 |                     62.7749 |
| (10, 'anytime')         |                        0.8933 |                      0.8936 |                       38.4865 |                     37.2326 |
| (10, 'anytime_nodelay') |                        0.8929 |                      0.893  |                       45.1599 |                     43.8977 |
| (10, 'regret_repair')   |                        0.8482 |                      0.8483 |                        1.2613 |                      1.0643 |
| (50, 'alns_fixed')      |                        0.8557 |                      0.8548 |                      250.111  |                    250.103  |
| (50, 'alns_fixed@40')   |                        0.8811 |                      0.8827 |                       40.1349 |                     40.1066 |
| (50, 'alns_stagnation') |                        0.8815 |                      0.8836 |                       61.7754 |                     62.7557 |
| (50, 'anytime')         |                        0.8889 |                      0.8899 |                       35.5117 |                     31.9005 |
| (50, 'anytime_nodelay') |                        0.8801 |                      0.8788 |                       47.4591 |                     44.7106 |
| (50, 'regret_repair')   |                        0.8485 |                      0.8483 |                        1.1987 |                      0.9818 |

## 6. Offline matched-compute test (scale = all)

|   kappa | scale   | metric         | baseline        |   t_ours_win |   t_ours_lin |   diff_win |   diff_lin | significant_better_win   | significant_better_lin   |
|--------:|:--------|:---------------|:----------------|-------------:|-------------:|-----------:|-----------:|:-------------------------|:-------------------------|
|       1 | all     | regret_pct     | fixed           |      39.2898 |      39.087  |    -0.0469 |    -0.0462 | True                     | True                     |
|       1 | all     | regret_pct     | stagnation      |      39.2898 |      39.087  |    -0.0307 |    -0.0363 | True                     | True                     |
|       1 | all     | regret_pct     | anytime_nodelay |      39.2898 |      39.087  |     0      |     0      | False                    | False                    |
|       1 | all     | regret_pct     | anytime_online  |      39.2898 |      39.087  |    -0.2044 |    -0.2065 | True                     | True                     |
|      10 | all     | regret_pct     | fixed           |      39.188  |      38.9759 |    -0.0469 |    -0.0462 | True                     | True                     |
|      10 | all     | regret_pct     | stagnation      |      39.188  |      38.9759 |    -0.0307 |    -0.0363 | True                     | True                     |
|      10 | all     | regret_pct     | anytime_nodelay |      39.188  |      38.9759 |     0      |     0      | False                    | False                    |
|      10 | all     | regret_pct     | anytime_online  |      39.188  |      38.9759 |    -0.2044 |    -0.2065 | True                     | True                     |
|      50 | all     | regret_pct     | fixed           |      38.1658 |      37.5465 |    -0.046  |    -0.0404 | True                     | True                     |
|      50 | all     | regret_pct     | stagnation      |      38.1658 |      37.5465 |    -0.0298 |    -0.0305 | True                     | True                     |
|      50 | all     | regret_pct     | anytime_nodelay |      38.1658 |      37.5465 |     0.0008 |     0.0058 | False                    | False                    |
|      50 | all     | regret_pct     | anytime_online  |      38.1658 |      37.5465 |    -0.2036 |    -0.2023 | True                     | True                     |
|       1 | all     | eff_regret_k1  | fixed           |      39.2898 |      39.087  |    -0.0469 |    -0.0462 | True                     | True                     |
|       1 | all     | eff_regret_k1  | stagnation      |      39.2898 |      39.087  |    -0.0307 |    -0.0363 | True                     | True                     |
|       1 | all     | eff_regret_k1  | anytime_nodelay |      39.2898 |      39.087  |     0      |     0      | False                    | False                    |
|       1 | all     | eff_regret_k1  | anytime_online  |      39.2898 |      39.087  |    -0.2044 |    -0.2065 | True                     | True                     |
|      10 | all     | eff_regret_k10 | fixed           |      39.188  |      38.9759 |    -0.0469 |    -0.0462 | True                     | True                     |
|      10 | all     | eff_regret_k10 | stagnation      |      39.188  |      38.9759 |    -0.0328 |    -0.0363 | True                     | True                     |
|      10 | all     | eff_regret_k10 | anytime_nodelay |      39.188  |      38.9759 |    -0.0048 |    -0.0048 | False                    | False                    |
|      10 | all     | eff_regret_k10 | anytime_online  |      39.188  |      38.9759 |    -0.2044 |    -0.2065 | True                     | True                     |
|      50 | all     | eff_regret_k50 | fixed           |      38.1658 |      37.5465 |    -0.1682 |    -0.1632 | True                     | True                     |
|      50 | all     | eff_regret_k50 | stagnation      |      38.1658 |      37.5465 |    -0.1595 |    -0.1534 | True                     | True                     |
|      50 | all     | eff_regret_k50 | anytime_nodelay |      38.1658 |      37.5465 |    -0.0303 |    -0.0365 | True                     | True                     |
|      50 | all     | eff_regret_k50 | anytime_online  |      38.1658 |      37.5465 |    -0.2014 |    -0.2002 | True                     | True                     |
