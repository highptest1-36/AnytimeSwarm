# Study 4, tier B held-out

## Primary family, Holm (H9 PropBuf, H10 MP non-inferiority, H11 fallback for MP, H12 Buf, H13 Forty)

| comparison | test | diff pp [95% CI] | p | p Holm |
|---|---|---|---|---|
| PropBufAll | sup | $-$0.38 [$-$0.72, $-$0.05] | 0.0252 | 0.0504 |
| MPAll | ni | $-$0.25 [$-$0.62, +0.12] | 0.0920 | 0.0920 |
| MPAll | sup (fixed sequence) | $-$0.25 [$-$0.62, +0.12] | 0.1888 | not tested |
| FbMPAll | sup | +9.66 [+9.04, +10.29] | 0.0000 | 0.0000 |
| BufAll | sup | +4.22 [+3.74, +4.68] | 0.0000 | 0.0000 |
| FortyAll | sup | +5.07 [+4.63, +5.52] | 0.0000 | 0.0000 |

H10b iterations/ms, CC minus MP: +1.131 [+0.994, +1.266] p 0.0000

## Secondary

OnlCC (ni): $-$0.30 [$-$0.68, +0.08] p 0.1489
FullCC (sup): +0.34 [+0.16, +0.51] p 0.0002
RepCCRep (sup): +3.33 [+2.88, +3.79] p 0.0000
CCConv (sup): +6.45 [+5.95, +6.94] p 0.0000
FullConv (sup): +6.79 [+6.30, +7.27] p 0.0000
FullBuf (sup): +4.56 [+4.09, +5.02] p 0.0000
FullForty (sup): +5.41 [+4.97, +5.84] p 0.0000

| regime | CC-PropBuf | CC-MP | CC-Buf | CC-Forty | CC-Conv | MP-MPnf |
|---|---|---|---|---|---|---|
| mid w1 | $-$0.52 [$-$1.23, +0.17] | +0.02 [$-$0.71, +0.72] | +3.61 [+2.80, +4.40] | +6.35 [+5.53, +7.17] | +7.95 [+7.09, +8.81] | +2.17 [+1.49, +2.86] |
| mid w0.5 | $-$0.20 [$-$0.75, +0.34] | $-$0.59 [$-$1.13, $-$0.05] | +4.33 [+3.60, +5.04] | +3.16 [+2.44, +3.87] | +4.51 [+3.75, +5.26] | +9.66 [+8.83, +10.48] |
| high w1 | $-$0.16 [$-$0.99, +0.67] | $-$0.23 [$-$1.10, +0.66] | +5.33 [+4.34, +6.30] | +7.22 [+6.17, +8.25] | +8.53 [+7.48, +9.56] | +8.52 [+7.30, +9.75] |
| high w0.5 | $-$0.64 [$-$1.24, $-$0.04] | $-$0.21 [$-$0.91, +0.52] | +3.61 [+2.83, +4.40] | +3.56 [+2.87, +4.27] | +4.81 [+4.07, +5.55] | +18.31 [+17.18, +19.46] |

| method | U | late | lost | skipped | ms | it/ms |
|---|---|---|---|---|---|---|
| Proposed planning model | 53.85 | 7.54 | 1.87 | 13.01 | 40.1 | 13.35 |
| Proportional buffer $c\,h$ | 54.23 | 7.13 | 2.00 | 12.72 | 40.1 | 13.72 |
| Moment propagation | 54.10 | 7.36 | 2.35 | 15.15 | 40.1 | 12.22 |
| Moment propagation, no fallback | 44.44 | 1.62 | 0.00 | 3.79 | 40.1 | 15.97 |
| Proposed, online calibration | 53.55 | 7.63 | 1.79 | 12.27 | 40.1 | 13.59 |
| Proposed, learned stopping rule | 54.19 | 7.34 | 2.27 | 12.97 | 50.4 | 10.12 |
| Constant 60 s buffer | 49.63 | 6.52 | 0.00 | 14.17 | 40.1 | 14.75 |
| Nominal model | 48.78 | 11.22 | 3.26 | 38.19 | 40.1 | 13.00 |
| Conventional (event-only) | 47.40 | 10.28 | 2.97 | 15.98 | 40.1 | 9.04 |
| Repair only, proposed model | 50.62 | 7.81 | 1.34 | 12.01 | 0.3 | 0.00 |
| Repair only, nominal model | 47.28 | 11.12 | 1.99 | 33.25 | 0.4 | 0.00 |
coverage CC mid: predicted 0.902 observed 0.888 (n=77158)
coverage CC high: predicted 0.713 observed 0.769 (n=68509)
coverage Forty mid: predicted 0.802 observed 0.817 (n=79110)
coverage Forty high: predicted 0.598 observed 0.686 (n=70207)
