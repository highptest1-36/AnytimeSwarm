# Calibration of the predicted probability of meeting the deadline

| study | method | level | tasks | ECE pp | on time % | predicted % | tail on time % | tail predicted % | tail share % | Brier |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | proposed | mid | 77158 | 3.08 | 88.8 | 90.2 | 94.7 | 97.3 | 85.5 | nan |
| 4 | proposed | high | 68509 | 6.14 | 76.9 | 71.3 | 94.1 | 93.6 | 46.5 | nan |
| 4 | nominal | mid | 79110 | 2.85 | 81.7 | 80.2 | 96.4 | 97.5 | 62.8 | nan |
| 4 | nominal | high | 70207 | 9.11 | 68.6 | 59.8 | 95.1 | 94.4 | 28.8 | nan |
| 5 | proposed | mid | 75916 | 2.38 | 90.6 | 92.7 | 94.8 | 97.3 | 88.5 | nan |
| 5 | proposed | high | 60300 | 4.85 | 85.0 | 80.5 | 94.3 | 93.6 | 55.1 | nan |
| 5 | nominal | mid | 79224 | 3.22 | 82.0 | 80.2 | 96.3 | 97.4 | 62.6 | nan |
| 5 | nominal | high | 70379 | 9.60 | 69.0 | 59.7 | 95.1 | 94.3 | 28.6 | nan |
| 6 | proposed | mid | 75317 | 2.35 | 90.7 | 92.6 | 94.8 | 97.2 | 88.4 | nan |
| 6 | proposed | high | 60303 | 5.20 | 85.1 | 80.6 | 94.4 | 93.7 | 55.4 | nan |
| 6 | nominal | mid | 78643 | 2.76 | 82.0 | 80.4 | 96.5 | 97.4 | 63.2 | nan |
| 6 | nominal | high | 70111 | 9.28 | 69.1 | 60.2 | 95.3 | 94.5 | 29.3 | nan |

## Study 7b: errors outside the calibrated model (proposed model, cost-aware fallback lam = 1)

| 7b | proposed | Gaussian (calibrated) | 60745 | 4.54 | 84.6 | 80.8 | 94.0 | 93.7 | 55.6 | 0.118 |
| 7b | proposed | Student-$t$ | 61027 | 4.46 | 85.1 | 80.9 | 94.8 | 93.7 | 55.9 | 0.114 |
| 7b | proposed | Rare long delays | 59747 | 3.56 | 82.5 | 80.5 | 92.6 | 93.6 | 54.8 | 0.129 |
| 7b | proposed | Bias per UAV | 60569 | 4.59 | 84.2 | 80.8 | 93.2 | 93.7 | 55.5 | 0.122 |
| 7b | proposed | Pareto latency | 60701 | 4.43 | 84.6 | 80.8 | 94.0 | 93.7 | 55.5 | 0.118 |
