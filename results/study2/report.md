# Study 2: pre-registered held-out analysis (docs/08_PROTOCOL_V2.md)

## H1: proposed vs. six baselines (periodic trigger), pooled, Holm

| baseline | diff pp [95% CI] | p | p Holm |
|---|---|---|---|
| ALNS, fixed 40 ms | +2.87 [+2.29, +3.45] | 0.0000 | 0.0000 |
| ALNS, size-scaled budget | +2.57 [+1.99, +3.17] | 0.0000 | 0.0000 |
| Online performance prediction | +2.70 [+2.13, +3.28] | 0.0000 | 0.0000 |
| Performance profile | +2.62 [+2.04, +3.19] | 0.0000 | 0.0000 |
| AnytimeSwarm-R | +2.49 [+1.92, +3.06] | 0.0000 | 0.0000 |
| Constant 60 s buffer | +1.35 [+0.93, +1.77] | 0.0000 | 0.0000 |

## H2 and secondary pooled comparisons (proposed minus method)

| method | diff pp [95% CI] | p |
|---|---|---|
| Conventional (40 ms, event-only) | +4.44 [+3.82, +5.05] | 0.0000 |
| ALNS, fixed 250 ms | +5.92 [+5.41, +6.44] | 0.0000 |
| ALNS, stagnation stop | +3.11 [+2.54, +3.69] | 0.0000 |
| AnytimeSwarm | +2.84 [+2.29, +3.40] | 0.0000 |
| Regret-2 repair (no search) | +4.21 [+3.57, +4.84] | 0.0000 |
| Proposed, event-only trigger | +0.22 [+0.06, +0.38] | 0.0062 |
| Proposed model, fixed 40 ms stop | +0.22 [+0.07, +0.37] | 0.0030 |
| Proposed, mean correction only | +0.18 [$-$0.06, +0.41] | 0.1418 |

H3 TOST (margin 0.5 pp): proposed minus fixed-40-ms stop on the proposed model, 90% CI +0.22 [+0.09, +0.35] -> equivalent

## H4: tier C (PX4 SITL + Gazebo)

1 missions, 1 runs, RTF 1.95 (min 1.95), repeated for RTF: 0, failed attempts: 0

| baseline | diff pp [95% CI] | p | p Holm |
|---|---|---|---|
