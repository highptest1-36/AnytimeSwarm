# Seed-cluster bootstrap vs mission bootstrap, tier B primary hypotheses

| H | comparison | diff pp | mission CI | p Holm | seed-cluster CI | p Holm | width ratio | outcome |
|---|---|---|---|---|---|---|---|---|
| H1 | vs. ALNS 40 ms | +2.87 | [+2.29, +3.45] | 0.0000 | [+2.25, +3.44] | 0.0000 | 1.03 | supported -> supported |
| H1 | vs. size-scaled budget | +2.57 | [+1.99, +3.17] | 0.0000 | [+1.93, +3.16] | 0.0000 | 1.03 | supported -> supported |
| H1 | vs. online prediction | +2.70 | [+2.13, +3.28] | 0.0000 | [+2.07, +3.28] | 0.0000 | 1.06 | supported -> supported |
| H1 | vs. performance profile | +2.62 | [+2.04, +3.19] | 0.0000 | [+2.03, +3.17] | 0.0000 | 0.99 | supported -> supported |
| H1 | vs. AnytimeSwarm-R | +2.49 | [+1.92, +3.06] | 0.0000 | [+1.90, +3.04] | 0.0000 | 1.01 | supported -> supported |
| H1 | vs. constant buffer | +1.35 | [+0.93, +1.77] | 0.0000 | [+1.02, +1.69] | 0.0000 | 0.80 | supported -> supported |
| H2 | vs. conventional | +4.44 | [+3.82, +5.05] | 0.0000 | [+3.78, +5.10] | 0.0000 | 1.08 | supported -> supported |
| H3 | stopping rule vs. fixed 40 ms | +0.22 | [+0.09, +0.35] | nan | [+0.07, +0.37] | nan | 1.18 | equivalent -> equivalent |
| H5 | fallback vs. no fallback | +1.97 | [+1.61, +2.33] | 0.0000 | [+1.63, +2.33] | 0.0000 | 0.97 | supported -> supported |
| H6 | vs. buffer, high, $\times0.5$ | +3.31 | [+2.58, +4.03] | 0.0000 | [+2.73, +3.90] | 0.0000 | 0.81 | supported -> supported |
| H7 | vs. ALNS 40 ms | +4.61 | [+4.15, +5.06] | 0.0000 | [+4.17, +5.05] | 0.0000 | 0.97 | supported -> supported |
| H8 | vs. constant buffer | +3.59 | [+3.17, +4.02] | 0.0000 | [+3.25, +3.93] | 0.0000 | 0.80 | supported -> supported |
| H9 | vs. proportional buffer | -0.38 | [-0.72, -0.05] | 0.0504 | [-0.69, -0.07] | 0.0324 | 0.92 | not supported -> reversed |
| H10 | vs. moment propagation (NI) | -0.25 | [-0.62, +0.12] | 0.0920 | [-0.61, +0.11] | 0.0842 | 0.99 | NI not shown -> NI not shown |
| H11 | MP: fallback vs. none | +9.66 | [+9.04, +10.29] | 0.0000 | [+8.99, +10.36] | 0.0000 | 1.09 | supported -> supported |
| H12 | vs. constant buffer | +4.22 | [+3.74, +4.68] | 0.0000 | [+3.87, +4.59] | 0.0000 | 0.77 | supported -> supported |
| H13 | vs. nominal model | +5.07 | [+4.63, +5.52] | 0.0000 | [+4.63, +5.49] | 0.0000 | 0.97 | supported -> supported |
| H16 | vs. nominal fallback | +2.42 | [+1.81, +3.02] | 0.0000 | [+2.00, +2.83] | 0.0000 | 0.69 | supported -> supported |
| H17 | vs. tuned prop. buffer (NI) | +0.90 | [+0.38, +1.44] | 0.0000 | [+0.39, +1.40] | 0.0000 | 0.95 | NI shown -> NI shown |
| H18 | vs. tuned $z$, no fallback (NI) | +1.78 | [+1.25, +2.31] | 0.0000 | [+1.29, +2.28] | 0.0000 | 0.93 | NI shown -> NI shown |
| H19 | vs. nominal model | +11.75 | [+10.88, +12.57] | 0.0000 | [+11.12, +12.38] | 0.0000 | 0.75 | supported -> supported |
| H20 | vs. CBBA | +12.77 | [+11.91, +13.63] | 0.0000 | [+12.09, +13.45] | 0.0000 | 0.79 | supported -> supported |
| H21 | CBBA on proposed model vs. CBBA | +12.12 | [+11.31, +12.93] | 0.0000 | [+11.49, +12.72] | 0.0000 | 0.76 | supported -> supported |
| H22 | MP: cost-aware vs. nominal fb | +2.71 | [+2.13, +3.27] | 0.0000 | [+2.13, +3.26] | 0.0000 | 0.98 | supported -> supported |
| H23 | MP: cost-aware vs. no fallback | +3.30 | [+2.83, +3.79] | 0.0000 | [+2.90, +3.69] | 0.0000 | 0.82 | supported -> supported |

outcomes changed: 1 of 25; width ratio min 0.69, median 0.97, max 1.18
