# Study 5, tier B held-out

## Primary family, lambda = 1, Holm (H16 nominal fallback, H17 tuned proportional buffer NI, H18 tuned no-fallback NI, H19 nominal model)

| comparison | test | diff pp [95% CI] | p | p Holm |
|---|---|---|---|---|
| CA(1) - CCfb | sup | +2.42 [+1.81, +3.02] | 0.0000 | 0.0000 |
| CA(1) - Prop | ni | +0.90 [+0.38, +1.44] | 0.0000 | 0.0000 |
| CA(1) - Prop | sup (fixed sequence) | +0.90 [+0.38, +1.44] | 0.0006 | tested |
| CA(1) - CCnf | ni | +1.78 [+1.25, +2.31] | 0.0000 | 0.0000 |
| CA(1) - CCnf | sup (fixed sequence) | +1.78 [+1.25, +2.31] | 0.0000 | tested |
| CA(1) - Forty | sup | +11.75 [+10.88, +12.57] | 0.0000 | 0.0000 |

## Secondary: CA(lambda) minus competitor, scored at the same lambda

| competitor | lambda 0.5 | lambda 1 | lambda 2 |
|---|---|---|---|
| CCfb | +0.63 [+0.30, +0.96] | +2.42 [+1.81, +3.02] | +7.25 [+6.40, +8.11] |
| Prop | +0.21 [$-$0.22, +0.64] | +0.90 [+0.38, +1.44] | $-$1.02 [$-$1.58, $-$0.47] |
| CCnf | +1.65 [+1.12, +2.18] | +1.78 [+1.25, +2.31] | $-$0.02 [$-$0.47, +0.42] |
| MP | +0.35 [$-$0.07, +0.77] | +2.09 [+1.50, +2.69] | +6.84 [+6.03, +7.66] |
| MPnf | +5.50 [+4.85, +6.12] | +2.88 [+2.21, +3.53] | $-$1.10 [$-$1.84, $-$0.41] |
| Buf | +3.84 [+3.27, +4.40] | +4.83 [+4.21, +5.44] | +8.08 [+7.29, +8.86] |
| Forty | +7.64 [+6.96, +8.30] | +11.75 [+10.88, +12.57] | +21.21 [+20.13, +22.26] |
| Conv | +8.93 [+8.20, +9.64] | +12.54 [+11.65, +13.38] | +21.01 [+19.92, +22.04] |

## Robustness to the late cost assumed when tuning

lambda 0.5: alns_fixed@40~z=auto4;lam=0.5+periodic:60 - Prop@1: +1.46 [+0.94, +1.99] p 0.0000
lambda 0.5: alns_fixed@40~z=auto4;lam=0.5+periodic:60 - CCnf@1: +3.32 [+2.80, +3.84] p 0.0000
lambda 0.5: alns_fixed@40~z=auto4;lam=0.5+periodic:60 - alns_fixed@40~z=auto4;lam=1+periodic:60: +0.02 [$-$0.40, +0.45] p 0.9062
lambda 2: alns_fixed@40~z=auto4;lam=2+periodic:60 - Prop@1: +1.05 [+0.42, +1.69] p 0.0012
lambda 2: alns_fixed@40~z=auto4;lam=2+periodic:60 - CCnf@1: $-$0.02 [$-$0.47, +0.42] p 0.9366
lambda 2: alns_fixed@40~z=auto4;lam=2+periodic:60 - alns_fixed@40~z=auto4;lam=1+periodic:60: +1.22 [+0.63, +1.83] p 0.0000

## lambda = 1 per regime

| regime | CCfb | Prop | CCnf | Forty |
|---|---|---|---|---|
| mid w1 | +1.15 [+0.24, +2.06] | $-$2.08 [$-$3.01, $-$1.18] | $-$1.68 [$-$2.58, $-$0.79] | +11.54 [+10.24, +12.84] |
| mid w0.5 | +1.03 [+0.22, +1.84] | +1.48 [+0.48, +2.44] | +1.84 [+0.85, +2.80] | +8.72 [+7.56, +9.84] |
| high w1 | +4.24 [+2.91, +5.61] | +2.03 [+0.76, +3.31] | +0.48 [$-$0.66, +1.62] | +16.40 [+14.86, +17.90] |
| high w0.5 | +3.24 [+2.04, +4.47] | +2.18 [+1.28, +3.07] | +6.49 [+5.51, +7.46] | +10.33 [+8.93, +11.76] |

## Mean score per method (%), late services per mission

| method | lambda 0 | 0.5 | 1 | 2 | late |
|---|---|---|---|---|---|
| CCnf@0.5 | 51.28 | 47.84 | 44.40 | 37.51 | 4.86 |
| CCnf@1 | 48.33 | 46.18 | 44.03 | 39.73 | 3.00 |
| CCnf@2 | 48.33 | 46.18 | 44.03 | 39.73 | 3.00 |
| Prop@0.5 | 54.62 | 49.28 | 43.95 | 33.28 | 7.11 |
| Prop@1 | 51.16 | 48.03 | 44.91 | 38.66 | 4.36 |
| Prop@2 | 46.55 | 45.10 | 43.64 | 40.73 | 2.02 |
| alns_fixed@40+event | 47.84 | 40.56 | 33.27 | 18.71 | 10.25 |
| alns_fixed@40+periodic:60 | 49.63 | 41.85 | 34.07 | 18.50 | 11.08 |
| alns_fixed@40~buf=60+periodic:60 | 50.33 | 45.66 | 40.98 | 31.64 | 6.49 |
| alns_fixed@40~mp=auto+periodic:60 | 45.06 | 44.00 | 42.94 | 40.81 | 1.50 |
| alns_fixed@40~mp=auto;fb=nominal+periodic:60 | 54.57 | 49.14 | 43.72 | 32.87 | 7.29 |
| alns_fixed@40~prop=0.3;fb=none+periodic:60 | 51.76 | 47.85 | 43.95 | 36.14 | 5.58 |
| alns_fixed@40~prop=0.45;fb=nominal+periodic:60 | 54.59 | 49.08 | 43.57 | 32.55 | 7.35 |
| alns_fixed@40~prop=0.45;fb=none+periodic:60 | 49.49 | 46.95 | 44.41 | 39.33 | 3.53 |
| alns_fixed@40~prop=0.75;fb=nominal+periodic:60 | 53.63 | 48.06 | 42.49 | 31.36 | 7.47 |
| alns_fixed@40~prop=0.75;fb=none+periodic:60 | 41.15 | 40.01 | 38.87 | 36.59 | 1.57 |
| alns_fixed@40~z=0+periodic:60 | 51.33 | 46.43 | 41.53 | 31.72 | 6.88 |
| alns_fixed@40~z=0.5+periodic:60 | 48.76 | 46.02 | 43.27 | 37.78 | 3.82 |
| alns_fixed@40~z=1+periodic:60 | 44.59 | 43.09 | 41.59 | 38.58 | 2.11 |
| alns_fixed@40~z=auto4;fb=nominal+periodic:60 | 54.33 | 48.86 | 43.40 | 32.46 | 7.39 |
| alns_fixed@40~z=auto4;lam=0.5+periodic:60 | 54.64 | 49.49 | 44.35 | 34.05 | 6.87 |
| alns_fixed@40~z=auto4;lam=1+periodic:60 | 53.13 | 49.47 | 45.81 | 38.50 | 4.96 |
| alns_fixed@40~z=auto4;lam=2+periodic:60 | 49.82 | 47.29 | 44.77 | 39.71 | 3.46 |
