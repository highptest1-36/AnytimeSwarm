# Study 8c analysis (development): 1 complete missions, 3 flights in dev8c_smoke

## Primary (fixed sequence, CAfee - CCfb)

| H | metric | diff [95% CI] | p | outcome |
|---|---|---|---|---|
| H35 | late arrivals per mission | +0.000 [+nan, +nan] | nan | not supported |
| H36 | u_1 (pp) | -17.39 [+nan, +nan] | nan | not tested (H35 not supported) |

## All comparisons: tier C and the tier B prediction on the same missions

| comparison | metric | tier C [95% CI] | p | tier B prediction [95% CI] |
|---|---|---|---|---|
| CAfee - CCfb | late | +0.00 [+0.00, +0.00] | 1.0000 |  |
| CAfee - CCfb | u1 | -17.39 [-17.39, -17.39] | 0.0000 |  |
| CAfee - CCfb | U | -17.39 [-17.39, -17.39] | 0.0000 |  |
| CAfee - Prop | late | +0.00 [+0.00, +0.00] | 1.0000 |  |
| CAfee - Prop | u1 | +0.00 [+0.00, +0.00] | 1.0000 |  |
| CAfee - Prop | U | +0.00 [+0.00, +0.00] | 1.0000 |  |
| CCfb - Prop | late | +0.00 [+0.00, +0.00] | 1.0000 |  |
| CCfb - Prop | u1 | +17.39 [+17.39, +17.39] | 0.0000 |  |
| CCfb - Prop | U | +17.39 [+17.39, +17.39] | 0.0000 |  |

## Means (tier C)

| method | U % | u_1 % | late | plan ms | p95 ms | RTF |
|---|---|---|---|---|---|---|
| CAfee | 30.43 | 30.43 | 0.00 | 41.0 | 42.0 | 1.64 |
| CCfb | 47.83 | 47.83 | 0.00 | 40.5 | 41.1 | 1.77 |
| Prop | 30.43 | 30.43 | 0.00 | 40.4 | 41.0 | 1.64 |

