# Tier B pilot summary (pilot_dev.csv, metric = utility_rate)

90 missions; resampling unit = mission; 95% percentile CI, 10 000 resamples.

## Mean utility_rate

|                           |   alns_fixed |   alns_fixed@40 |   alns_stagnation |   anytime |   anytime_nodelay |   regret_repair |
|:--------------------------|-------------:|----------------:|------------------:|----------:|------------------:|----------------:|
| ('low', 'high', 1.0)      |       0.7834 |          0.7799 |            0.7883 |    0.7876 |            0.7874 |          0.752  |
| ('low', 'high', 10.0)     |       0.7799 |          0.7813 |            0.7873 |    0.7889 |            0.7871 |          0.7515 |
| ('low', 'high', 50.0)     |       0.7555 |          0.7798 |            0.7777 |    0.7834 |            0.7797 |          0.7511 |
| ('low', 'none', 1.0)      |       0.7923 |          0.7863 |            0.7897 |    0.7905 |            0.7902 |          0.7559 |
| ('low', 'none', 10.0)     |       0.7854 |          0.7847 |            0.789  |    0.7877 |            0.7902 |          0.7556 |
| ('low', 'none', 50.0)     |       0.7652 |          0.7853 |            0.7843 |    0.7874 |            0.7888 |          0.7555 |
| ('mid', 'high', 1.0)      |       0.6618 |          0.6646 |            0.6625 |    0.6662 |            0.6633 |          0.643  |
| ('mid', 'high', 10.0)     |       0.6593 |          0.6635 |            0.6655 |    0.6626 |            0.6663 |          0.6432 |
| ('mid', 'high', 50.0)     |       0.6509 |          0.6581 |            0.6583 |    0.6615 |            0.6608 |          0.6422 |
| ('mid', 'none', 1.0)      |       0.6604 |          0.6641 |            0.6668 |    0.669  |            0.6689 |          0.6389 |
| ('mid', 'none', 10.0)     |       0.668  |          0.6649 |            0.6698 |    0.6673 |            0.6702 |          0.6388 |
| ('mid', 'none', 50.0)     |       0.6514 |          0.6657 |            0.668  |    0.6691 |            0.6672 |          0.6394 |
| ('nominal', 'high', 1.0)  |       0.8866 |          0.879  |            0.8835 |    0.884  |            0.8843 |          0.8382 |
| ('nominal', 'high', 10.0) |       0.8793 |          0.8768 |            0.8807 |    0.8814 |            0.8821 |          0.8381 |
| ('nominal', 'high', 50.0) |       0.8425 |          0.8723 |            0.8704 |    0.875  |            0.8701 |          0.8375 |
| ('nominal', 'none', 1.0)  |       0.8982 |          0.889  |            0.895  |    0.8974 |            0.8976 |          0.8484 |
| ('nominal', 'none', 10.0) |       0.8908 |          0.8877 |            0.8917 |    0.8939 |            0.8933 |          0.8483 |
| ('nominal', 'none', 50.0) |       0.8551 |          0.8827 |            0.8828 |    0.8889 |            0.8801 |          0.8482 |

## Mean planning time per call (ms)

|                           |   alns_fixed |   alns_fixed@40 |   alns_stagnation |   anytime |   anytime_nodelay |   regret_repair |
|:--------------------------|-------------:|----------------:|------------------:|----------:|------------------:|----------------:|
| ('low', 'high', 1.0)      |        250.1 |            40.1 |              62.6 |      50.4 |              50.2 |             1.1 |
| ('low', 'high', 10.0)     |        250.1 |            40.1 |              63.2 |      42.6 |              50.9 |             1.1 |
| ('low', 'high', 50.0)     |        250.1 |            40.2 |              62.4 |      39.5 |              50.4 |             1.1 |
| ('low', 'none', 1.0)      |        250.1 |            40.1 |              63   |      48.3 |              48.8 |             1.1 |
| ('low', 'none', 10.0)     |        250.1 |            40.1 |              62.7 |      42.9 |              49.9 |             1.1 |
| ('low', 'none', 50.0)     |        250.1 |            40.1 |              62.8 |      37.7 |              49.9 |             1.1 |
| ('mid', 'high', 1.0)      |        250.4 |            40.1 |              63.7 |      57.4 |              55.3 |             1.1 |
| ('mid', 'high', 10.0)     |        250.1 |            40.1 |              62.1 |      49.1 |              58.9 |             1.1 |
| ('mid', 'high', 50.0)     |        250.1 |            40.2 |              62   |      40.1 |              53.9 |             1.1 |
| ('mid', 'none', 1.0)      |        250.1 |            40.1 |              63.4 |      52.5 |              53   |             1.1 |
| ('mid', 'none', 10.0)     |        250.1 |            40.1 |              62.8 |      45.9 |              52.1 |             1   |
| ('mid', 'none', 50.0)     |        250.1 |            40.1 |              63.4 |      42.2 |              55.5 |             1.1 |
| ('nominal', 'high', 1.0)  |        250.1 |            40.1 |              62.2 |      42.5 |              42.9 |             0.9 |
| ('nominal', 'high', 10.0) |        250.1 |            40.1 |              61.6 |      38.1 |              45   |             0.9 |
| ('nominal', 'high', 50.0) |        250.1 |            40.1 |              61.7 |      34.1 |              47.6 |             1.3 |
| ('nominal', 'none', 1.0)  |        250.1 |            40.1 |              61.9 |      43.2 |              43.2 |             1   |
| ('nominal', 'none', 10.0) |        250.1 |            40.1 |              62.1 |      37.9 |              44.2 |             1   |
| ('nominal', 'none', 50.0) |        250.1 |            40.1 |              62.2 |      31.5 |              43.6 |             0.9 |

## AnytimeSwarm minus baseline (utility_rate, paired by mission)

| exec_level   | latency_level   |   kappa | baseline        |    diff |   ci_lo |   ci_hi |   win_rate | sig   |
|:-------------|:----------------|--------:|:----------------|--------:|--------:|--------:|-----------:|:------|
| low          | high            |       1 | alns_fixed      |  0.0041 | -0.0057 |  0.0143 |     0.7    | 0     |
| low          | high            |       1 | alns_fixed@40   |  0.0077 |  0.0009 |  0.0152 |     0.7667 | +     |
| low          | high            |       1 | alns_stagnation | -0.0007 | -0.0083 |  0.0072 |     0.7111 | 0     |
| low          | high            |       1 | anytime_nodelay |  0.0002 | -0.001  |  0.0018 |     0.9444 | 0     |
| low          | high            |       1 | regret_repair   |  0.0355 |  0.0209 |  0.0498 |     0.7333 | +     |
| low          | high            |      10 | alns_fixed      |  0.0089 | -0.0011 |  0.0193 |     0.6222 | 0     |
| low          | high            |      10 | alns_fixed@40   |  0.0076 |  0.0013 |  0.0145 |     0.8111 | +     |
| low          | high            |      10 | alns_stagnation |  0.0015 | -0.0061 |  0.0095 |     0.6778 | 0     |
| low          | high            |      10 | anytime_nodelay |  0.0018 | -0.0028 |  0.0065 |     0.8111 | 0     |
| low          | high            |      10 | regret_repair   |  0.0374 |  0.0223 |  0.0519 |     0.7444 | +     |
| low          | high            |      50 | alns_fixed      |  0.0279 |  0.0152 |  0.0409 |     0.7333 | +     |
| low          | high            |      50 | alns_fixed@40   |  0.0036 | -0.0036 |  0.0118 |     0.6778 | 0     |
| low          | high            |      50 | alns_stagnation |  0.0057 | -0.0042 |  0.0162 |     0.6889 | 0     |
| low          | high            |      50 | anytime_nodelay |  0.0037 | -0.0046 |  0.0121 |     0.7889 | 0     |
| low          | high            |      50 | regret_repair   |  0.0324 |  0.0183 |  0.0467 |     0.7667 | +     |
| low          | none            |       1 | alns_fixed      | -0.0018 | -0.0122 |  0.0092 |     0.6222 | 0     |
| low          | none            |       1 | alns_fixed@40   |  0.0042 | -0.0021 |  0.0113 |     0.7778 | 0     |
| low          | none            |       1 | alns_stagnation |  0.0008 | -0.0078 |  0.0097 |     0.7667 | 0     |
| low          | none            |       1 | anytime_nodelay |  0.0004 | -0.0032 |  0.0044 |     0.9556 | 0     |
| low          | none            |       1 | regret_repair   |  0.0347 |  0.0189 |  0.0503 |     0.7333 | +     |
| low          | none            |      10 | alns_fixed      |  0.0023 | -0.009  |  0.0136 |     0.6111 | 0     |
| low          | none            |      10 | alns_fixed@40   |  0.003  | -0.005  |  0.0111 |     0.7889 | 0     |
| low          | none            |      10 | alns_stagnation | -0.0014 | -0.0104 |  0.0076 |     0.7111 | 0     |
| low          | none            |      10 | anytime_nodelay | -0.0025 | -0.0094 |  0.0039 |     0.7889 | 0     |
| low          | none            |      10 | regret_repair   |  0.0321 |  0.0165 |  0.0471 |     0.7333 | +     |
| low          | none            |      50 | alns_fixed      |  0.0222 |  0.0095 |  0.0353 |     0.6556 | +     |
| low          | none            |      50 | alns_fixed@40   |  0.002  | -0.0064 |  0.011  |     0.6889 | 0     |
| low          | none            |      50 | alns_stagnation |  0.0031 | -0.0064 |  0.0129 |     0.6667 | 0     |
| low          | none            |      50 | anytime_nodelay | -0.0015 | -0.0087 |  0.0057 |     0.7    | 0     |
| low          | none            |      50 | regret_repair   |  0.0318 |  0.0166 |  0.047  |     0.7333 | +     |
| mid          | high            |       1 | alns_fixed      |  0.0043 | -0.0053 |  0.014  |     0.6778 | 0     |
| mid          | high            |       1 | alns_fixed@40   |  0.0015 | -0.0055 |  0.009  |     0.7222 | 0     |
| mid          | high            |       1 | alns_stagnation |  0.0036 | -0.0047 |  0.012  |     0.7111 | 0     |
| mid          | high            |       1 | anytime_nodelay |  0.0028 | -0.001  |  0.0074 |     0.8556 | 0     |
| mid          | high            |       1 | regret_repair   |  0.0232 |  0.0065 |  0.039  |     0.6889 | +     |
| mid          | high            |      10 | alns_fixed      |  0.0032 | -0.0078 |  0.0147 |     0.6444 | 0     |
| mid          | high            |      10 | alns_fixed@40   | -0.0009 | -0.0084 |  0.0066 |     0.7222 | 0     |
| mid          | high            |      10 | alns_stagnation | -0.003  | -0.0116 |  0.0063 |     0.7    | 0     |
| mid          | high            |      10 | anytime_nodelay | -0.0037 | -0.0098 |  0.0018 |     0.7889 | 0     |
| mid          | high            |      10 | regret_repair   |  0.0194 |  0.003  |  0.0351 |     0.6778 | +     |
| mid          | high            |      50 | alns_fixed      |  0.0107 | -0.0017 |  0.0231 |     0.6222 | 0     |
| mid          | high            |      50 | alns_fixed@40   |  0.0034 | -0.0057 |  0.0129 |     0.6444 | 0     |
| mid          | high            |      50 | alns_stagnation |  0.0032 | -0.0086 |  0.0149 |     0.6889 | 0     |
| mid          | high            |      50 | anytime_nodelay |  0.0007 | -0.0081 |  0.0097 |     0.7667 | 0     |
| mid          | high            |      50 | regret_repair   |  0.0194 |  0.0032 |  0.0351 |     0.6556 | +     |
| mid          | none            |       1 | alns_fixed      |  0.0086 | -0.0007 |  0.0181 |     0.6889 | 0     |
| mid          | none            |       1 | alns_fixed@40   |  0.0049 | -0.0027 |  0.0119 |     0.8333 | 0     |
| mid          | none            |       1 | alns_stagnation |  0.0022 | -0.0057 |  0.0096 |     0.7889 | 0     |
| mid          | none            |       1 | anytime_nodelay |  0.0001 | -0.0032 |  0.0029 |     0.9778 | 0     |
| mid          | none            |       1 | regret_repair   |  0.0301 |  0.0137 |  0.0464 |     0.6778 | +     |
| mid          | none            |      10 | alns_fixed      | -0.0007 | -0.0112 |  0.0101 |     0.6333 | 0     |
| mid          | none            |      10 | alns_fixed@40   |  0.0024 | -0.0035 |  0.008  |     0.8    | 0     |
| mid          | none            |      10 | alns_stagnation | -0.0025 | -0.0117 |  0.0067 |     0.7222 | 0     |
| mid          | none            |      10 | anytime_nodelay | -0.0029 | -0.0089 |  0.003  |     0.7889 | 0     |
| mid          | none            |      10 | regret_repair   |  0.0285 |  0.0126 |  0.0444 |     0.7222 | +     |
| mid          | none            |      50 | alns_fixed      |  0.0177 |  0.0044 |  0.0313 |     0.6556 | +     |
| mid          | none            |      50 | alns_fixed@40   |  0.0034 | -0.0054 |  0.0124 |     0.7444 | 0     |
| mid          | none            |      50 | alns_stagnation |  0.0011 | -0.0105 |  0.013  |     0.7    | 0     |
| mid          | none            |      50 | anytime_nodelay |  0.0019 | -0.0055 |  0.0099 |     0.7556 | 0     |
| mid          | none            |      50 | regret_repair   |  0.0296 |  0.0144 |  0.0451 |     0.7111 | +     |
| nominal      | high            |       1 | alns_fixed      | -0.0026 | -0.0076 |  0.0024 |     0.7667 | 0     |
| nominal      | high            |       1 | alns_fixed@40   |  0.005  |  0.0014 |  0.0088 |     0.8667 | +     |
| nominal      | high            |       1 | alns_stagnation |  0.0006 | -0.0039 |  0.005  |     0.8222 | 0     |
| nominal      | high            |       1 | anytime_nodelay | -0.0003 | -0.001  |  0.0002 |     0.9667 | 0     |
| nominal      | high            |       1 | regret_repair   |  0.0458 |  0.0351 |  0.0567 |     0.9111 | +     |
| nominal      | high            |      10 | alns_fixed      |  0.0021 | -0.0044 |  0.0088 |     0.7    | 0     |
| nominal      | high            |      10 | alns_fixed@40   |  0.0046 |  0.0006 |  0.0091 |     0.8556 | +     |
| nominal      | high            |      10 | alns_stagnation |  0.0007 | -0.0047 |  0.0062 |     0.8111 | 0     |
| nominal      | high            |      10 | anytime_nodelay | -0.0006 | -0.0037 |  0.0022 |     0.8444 | 0     |
| nominal      | high            |      10 | regret_repair   |  0.0434 |  0.0326 |  0.0543 |     0.8889 | +     |
| nominal      | high            |      50 | alns_fixed      |  0.0325 |  0.0231 |  0.0426 |     0.8333 | +     |
| nominal      | high            |      50 | alns_fixed@40   |  0.0027 | -0.0021 |  0.0079 |     0.7556 | 0     |
| nominal      | high            |      50 | alns_stagnation |  0.0047 | -0.0025 |  0.0123 |     0.7    | 0     |
| nominal      | high            |      50 | anytime_nodelay |  0.0049 |  0.0011 |  0.0087 |     0.8333 | +     |
| nominal      | high            |      50 | regret_repair   |  0.0375 |  0.0281 |  0.0472 |     0.8889 | +     |
| nominal      | none            |       1 | alns_fixed      | -0.0008 | -0.006  |  0.0044 |     0.7444 | 0     |
| nominal      | none            |       1 | alns_fixed@40   |  0.0083 |  0.0043 |  0.0128 |     0.9222 | +     |
| nominal      | none            |       1 | alns_stagnation |  0.0024 | -0.0019 |  0.0068 |     0.8889 | 0     |
| nominal      | none            |       1 | anytime_nodelay | -0.0002 | -0.0009 |  0.0003 |     0.9667 | 0     |
| nominal      | none            |       1 | regret_repair   |  0.0489 |  0.0375 |  0.0606 |     0.9111 | +     |
| nominal      | none            |      10 | alns_fixed      |  0.0031 | -0.0034 |  0.0099 |     0.6333 | 0     |
| nominal      | none            |      10 | alns_fixed@40   |  0.0063 |  0.0025 |  0.0106 |     0.8333 | +     |
| nominal      | none            |      10 | alns_stagnation |  0.0023 | -0.0035 |  0.0079 |     0.7778 | 0     |
| nominal      | none            |      10 | anytime_nodelay |  0.0007 | -0.0025 |  0.0033 |     0.8667 | 0     |
| nominal      | none            |      10 | regret_repair   |  0.0457 |  0.0346 |  0.0569 |     0.9111 | +     |
| nominal      | none            |      50 | alns_fixed      |  0.0338 |  0.0237 |  0.0446 |     0.8111 | +     |
| nominal      | none            |      50 | alns_fixed@40   |  0.0063 |  0.0015 |  0.0118 |     0.8667 | +     |
| nominal      | none            |      50 | alns_stagnation |  0.0061 |  0.0001 |  0.0123 |     0.8333 | +     |
| nominal      | none            |      50 | anytime_nodelay |  0.0088 |  0.0043 |  0.0136 |     0.9111 | +     |
| nominal      | none            |      50 | regret_repair   |  0.0408 |  0.0306 |  0.0509 |     0.9222 | +     |

## Go/No-Go

Disturbed configurations where AnytimeSwarm > alns_fixed@40 with CI above 0: 2 / 12.

| exec_level   | latency_level   |   kappa | baseline      |   diff |   ci_lo |   ci_hi |   win_rate | sig   |
|:-------------|:----------------|--------:|:--------------|-------:|--------:|--------:|-----------:|:------|
| low          | high            |       1 | alns_fixed@40 | 0.0077 |  0.0009 |  0.0152 |     0.7667 | +     |
| low          | high            |      10 | alns_fixed@40 | 0.0076 |  0.0013 |  0.0145 |     0.8111 | +     |
