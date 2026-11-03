# Study 8 analysis (development)

Files: dev8a_check.csv, dev8b_check.csv; NI margin 0.5 pp.

## 8a primary family (Holm over the budgets x 2): H29_B CAprop - MPCA, H30_B CAfee - Prop, u_1

| H | test | diff pp [95% CI] | p | p Holm | outcome | seed-cluster CI | p Holm (cluster) | outcome (cluster) |
|---|---|---|---|---|---|---|---|---|
| HTwentyNineAtFive | sup | +2.24 [-0.55, +5.06] | 0.1234 | 0.3702 | no significant difference | [+0.46, +4.02] | 0.0000 | first better |
| HThirtyAtFive | sup | +2.08 [-1.98, +6.04] | 0.3088 | 0.6176 | no significant difference | [+1.12, +3.05] | 0.0000 | first better |
| HTwentyNineAtTwoFifty | sup | +4.16 [+0.46, +8.22] | 0.0242 | 0.0968 | no significant difference | [+3.56, +4.76] | 0.0000 | first better |
| HThirtyAtTwoFifty | sup | +1.61 [-2.51, +5.29] | 0.4126 | 0.6176 | no significant difference | [+1.32, +1.90] | 0.0000 | first better |

Seed-cluster bootstrap changed 4 of 4 outcomes.

## 8a means per method and budget

| method | B ms | U % | u_1 % | late | call ms | p99 ms | max ms | model ms | over ms | it/ms |
|---|---|---|---|---|---|---|---|---|---|---|
| CAfee | 5 | 31.96 | 24.19 | 5.39 | 5.86 | 7.75 | 13.9 | 0.79 | 0.86 | 16.6 |
| CAfee | 250 | 31.41 | 23.93 | 5.44 | 251.45 | 254.45 | 265.2 | 1.33 | 1.45 | 13.3 |
| CAprop | 5 | 31.19 | 23.92 | 5.17 | 6.11 | 8.89 | 17.0 | 1.04 | 1.11 | 14.1 |
| CAprop | 250 | 31.85 | 24.97 | 5.28 | 251.21 | 253.62 | 261.2 | 1.13 | 1.21 | 14.2 |
| MPCA | 5 | 27.14 | 21.68 | 3.33 | 6.16 | 8.61 | 16.5 | 1.09 | 1.16 | 15.2 |
| MPCA | 250 | 27.06 | 20.81 | 3.78 | 251.63 | 255.21 | 266.6 | 1.52 | 1.63 | 13.8 |
| Prop | 5 | 29.94 | 22.11 | 5.94 | 5.37 | 5.89 | 7.8 | 0.31 | 0.37 | 14.8 |
| Prop | 250 | 30.02 | 22.32 | 5.67 | 250.48 | 251.12 | 252.9 | 0.40 | 0.48 | 13.7 |
| Nom | 5 | 30.74 | 9.51 | 14.39 | 5.17 | 6.06 | 13.6 | 0.06 | 0.17 | 12.1 |
| Nom | 250 | 28.17 | 9.01 | 12.94 | 250.20 | 250.50 | 252.2 | 0.11 | 0.20 | 11.6 |

## 8a mean u_1 per kappa

| method | B | kappa 10 | kappa 50 | kappa 200 |
|---|---|---|---|---|
| CAfee | 5 | - | 24.19 | - |
| CAfee | 250 | - | 23.93 | - |
| CAprop | 5 | - | 23.92 | - |
| CAprop | 250 | - | 24.97 | - |
| MPCA | 5 | - | 21.68 | - |
| MPCA | 250 | - | 20.81 | - |
| Prop | 5 | - | 22.11 | - |
| Prop | 250 | - | 22.32 | - |
| Nom | 5 | - | 9.51 | - |
| Nom | 250 | - | 9.01 | - |

## 8b primary family (Holm over four): H31 CAfee - Forty (u_1), H32 CAfee - CCfb (u_1), H33 CAfee vs tuned Prop (u_1, NI), H34 CCfb - Forty (U)

| H | test | diff pp [95% CI] | p | p Holm | outcome | seed-cluster CI | p Holm (cluster) | outcome (cluster) |
|---|---|---|---|---|---|---|---|---|
| HThirtyOne | sup | +15.54 [+13.03, +18.31] | 0.0000 | 0.0000 | first better | [+14.63, +17.13] | 0.0000 | first better |
| HThirtyTwo | sup | +3.49 [+2.21, +4.89] | 0.0000 | 0.0000 | first better | [+1.25, +4.92] | 0.0000 | first better |
| HThirtyThree | ni | +1.64 [-0.37, +3.71] | 0.0194 | 0.0194 | supported (NI) | [+0.39, +2.81] | 0.0000 | supported (NI) |
| HThirtyFour | sup | +6.33 [+4.95, +7.83] | 0.0000 | 0.0000 | first better | [+5.11, +7.07] | 0.0000 | first better |

Seed-cluster bootstrap changed 0 of 4 outcomes.

## 8b contrasts: new family vs conference family (study 7a)

| contrast | family | diff pp [95% CI] |
|---|---|---|
| CAfeeForty | new | +15.54 [+13.03, +18.31] |
| CAfeeForty | Conf | +12.12 [+11.24, +12.97] |
| CAfeeCCfb | new | +3.49 [+2.21, +4.89] |
| CAfeeCCfb | Conf | +2.45 [+1.95, +2.96] |
| CAfeeProp | new | +1.64 [-0.37, +3.71] |
| CAfeeProp | Conf | +1.34 [+0.77, +1.90] |
| CCfbForty | new | +6.33 [+4.95, +7.83] |
| CCfbForty | Conf | +5.03 [+4.53, +5.52] |
| CAfeeCCnf | new | +2.22 [+0.75, +3.76] |
| CAfeeCCnf | Conf | +1.97 [+1.46, +2.50] |
| MPCACAprop | new | +0.55 [-0.97, +2.04] |
| CAfeeCAprop | new | +0.34 [-0.90, +1.63] |
| CAfeeCAprop | Conf | +0.24 [-0.20, +0.67] |
| CAfeeFortyU | new | +5.89 [+4.09, +7.90] |
| CAfeeFortyU | Conf | +3.68 [+3.06, +4.28] |

## 8b means

| method | U mid | u_1 mid | U high | u_1 high | U | u_1 | late | urgent on time % | call ms | model ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Forty | 55.54 | 42.93 | 43.96 | 26.07 | 49.75 | 34.50 | 10.49 | 26.4 | 40.2 | 0.09 |
| CCfb | 62.62 | 56.38 | 49.54 | 36.72 | 56.08 | 46.55 | 6.14 | 24.7 | 40.7 | 0.54 |
| CAfee | 61.66 | 56.34 | 49.62 | 43.74 | 55.64 | 50.04 | 3.55 | 21.2 | 40.7 | 0.60 |
| CAprop | 61.57 | 56.04 | 49.34 | 43.37 | 55.45 | 49.70 | 3.50 | 22.4 | 41.0 | 0.80 |
| MPCA | 61.15 | 57.64 | 46.70 | 42.85 | 53.92 | 50.25 | 2.33 | 22.3 | 41.4 | 1.08 |
| Prop | 59.73 | 56.56 | 47.00 | 40.25 | 53.36 | 48.40 | 3.10 | 20.7 | 40.4 | 0.29 |
| CCnf | 59.66 | 56.92 | 42.75 | 38.71 | 51.21 | 47.82 | 2.06 | 17.3 | 40.4 | 0.29 |

## 8b calibration of the transferred error model (CAfee runs)

| family | level | ECE pp | on time % | predicted % | tail on time % | tail predicted % |
|---|---|---|---|---|---|---|
| new | mid | 1.4 | 92.8 | 93.2 | 96.6 | 97.4 |
| new | high | 6.7 | 89.2 | 82.6 | 95.8 | 94.4 |
| conference | mid | 2.6 | 90.9 | 92.8 | 94.8 | 97.2 |
| conference | high | 4.6 | 83.9 | 80.1 | 93.9 | 93.6 |

