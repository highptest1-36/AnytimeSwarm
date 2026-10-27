# explore_dev: utility_rate

90 missions per configuration; paired bootstrap over missions (95% CI).

## Mean utility_rate

|                                       |   alns_fixed |   alns_fixed@40 |   alns_stagnation |   anytime |   anytime_nodelay |   anytime_risk |
|:--------------------------------------|-------------:|----------------:|------------------:|----------:|------------------:|---------------:|
| ('low', 'high', 10.0, 'deviation:30') |       0.7821 |          0.7864 |            0.7893 |    0.7917 |            0.7924 |         0.7952 |
| ('low', 'high', 10.0, 'event')        |       0.7774 |          0.7825 |            0.7874 |    0.7841 |            0.7852 |         0.7894 |
| ('low', 'high', 10.0, 'periodic:60')  |       0.7886 |          0.7956 |            0.7983 |    0.7922 |            0.7943 |         0.7994 |
| ('low', 'high', 50.0, 'deviation:30') |       0.7612 |          0.7798 |            0.779  |    0.7791 |            0.7798 |         0.784  |
| ('low', 'high', 50.0, 'event')        |       0.7553 |          0.7777 |            0.773  |    0.777  |            0.7799 |         0.7853 |
| ('low', 'high', 50.0, 'periodic:60')  |       0.7715 |          0.7895 |            0.7892 |    0.7895 |            0.7891 |         0.7967 |
| ('low', 'none', 10.0, 'deviation:30') |       0.7889 |          0.7908 |            0.7936 |    0.7904 |            0.7904 |         0.7969 |
| ('low', 'none', 10.0, 'event')        |       0.7867 |          0.7857 |            0.7896 |    0.7853 |            0.7856 |         0.7917 |
| ('low', 'none', 10.0, 'periodic:60')  |       0.7987 |          0.797  |            0.8011 |    0.7968 |            0.7995 |         0.8056 |
| ('low', 'none', 50.0, 'deviation:30') |       0.7715 |          0.7873 |            0.7862 |    0.785  |            0.7852 |         0.7938 |
| ('low', 'none', 50.0, 'event')        |       0.7658 |          0.78   |            0.7824 |    0.7795 |            0.7848 |         0.791  |
| ('low', 'none', 50.0, 'periodic:60')  |       0.7804 |          0.794  |            0.7961 |    0.7904 |            0.7951 |         0.8051 |
| ('mid', 'high', 10.0, 'deviation:30') |       0.6703 |          0.6692 |            0.6665 |    0.6638 |            0.6701 |         0.6685 |
| ('mid', 'high', 10.0, 'event')        |       0.6612 |          0.6573 |            0.6617 |    0.6657 |            0.6666 |         0.6656 |
| ('mid', 'high', 10.0, 'periodic:60')  |       0.6793 |          0.6702 |            0.6692 |    0.6758 |            0.6728 |         0.68   |
| ('mid', 'high', 50.0, 'deviation:30') |       0.6598 |          0.6597 |            0.6576 |    0.6581 |            0.656  |         0.6723 |
| ('mid', 'high', 50.0, 'event')        |       0.6513 |          0.6599 |            0.661  |    0.6601 |            0.6615 |         0.6664 |
| ('mid', 'high', 50.0, 'periodic:60')  |       0.6704 |          0.6708 |            0.6659 |    0.6722 |            0.6723 |         0.6791 |
| ('mid', 'none', 10.0, 'deviation:30') |       0.6746 |          0.6735 |            0.677  |    0.6726 |            0.6734 |         0.6789 |
| ('mid', 'none', 10.0, 'event')        |       0.6655 |          0.6655 |            0.6726 |    0.6659 |            0.6709 |         0.676  |
| ('mid', 'none', 10.0, 'periodic:60')  |       0.6787 |          0.6681 |            0.6738 |    0.6677 |            0.6721 |         0.6823 |
| ('mid', 'none', 50.0, 'deviation:30') |       0.6623 |          0.6741 |            0.6785 |    0.6725 |            0.6679 |         0.6764 |
| ('mid', 'none', 50.0, 'event')        |       0.654  |          0.6651 |            0.6622 |    0.6652 |            0.6673 |         0.6722 |
| ('mid', 'none', 50.0, 'periodic:60')  |       0.6779 |          0.6737 |            0.6749 |    0.6701 |            0.6702 |         0.6787 |

## Planning time per call (ms)

|                                       |   alns_fixed |   alns_fixed@40 |   alns_stagnation |   anytime |   anytime_nodelay |   anytime_risk |
|:--------------------------------------|-------------:|----------------:|------------------:|----------:|------------------:|---------------:|
| ('low', 'high', 10.0, 'deviation:30') |        250.2 |            40.2 |              62.3 |      52   |              55.8 |           43.4 |
| ('low', 'high', 10.0, 'event')        |        250.2 |            40.2 |              64.1 |      51.2 |              59.2 |           44.5 |
| ('low', 'high', 10.0, 'periodic:60')  |        250.1 |            40.1 |              55.4 |      39.5 |              41.5 |           38.6 |
| ('low', 'high', 50.0, 'deviation:30') |        250.2 |            40.1 |              62   |      47.9 |              56.9 |           34.3 |
| ('low', 'high', 50.0, 'event')        |        250.2 |            40.1 |              64.6 |      49.5 |              61.4 |           34.3 |
| ('low', 'high', 50.0, 'periodic:60')  |        250.2 |            40.1 |              55.9 |      42.5 |              41.3 |           33.5 |
| ('low', 'none', 10.0, 'deviation:30') |        250.2 |            40.2 |              62.2 |      51.4 |              56   |           43.8 |
| ('low', 'none', 10.0, 'event')        |        250.2 |            40.2 |              63.6 |      51.8 |              58.9 |           46.1 |
| ('low', 'none', 10.0, 'periodic:60')  |        250.2 |            40.2 |              55.6 |      39   |              41.8 |           39.5 |
| ('low', 'none', 50.0, 'deviation:30') |        250.1 |            40.2 |              62.2 |      47   |              57.7 |           35.4 |
| ('low', 'none', 50.0, 'event')        |        250.2 |            40.1 |              63.4 |      46.2 |              57.9 |           34.8 |
| ('low', 'none', 50.0, 'periodic:60')  |        250.2 |            40.1 |              55.4 |      39.2 |              41.8 |           33.6 |
| ('mid', 'high', 10.0, 'deviation:30') |        250.1 |            40.1 |              59.1 |      46.8 |              50.7 |           42.4 |
| ('mid', 'high', 10.0, 'event')        |        250.1 |            40.1 |              62.6 |      53.2 |              59.6 |           46.5 |
| ('mid', 'high', 10.0, 'periodic:60')  |        250.1 |            40.1 |              56.3 |      49.7 |              46.5 |           41.6 |
| ('mid', 'high', 50.0, 'deviation:30') |        250.2 |            40.2 |              61.2 |      49.3 |              60   |           36.7 |
| ('mid', 'high', 50.0, 'event')        |        250.1 |            40.1 |              63.4 |      46.9 |              62.3 |           35.3 |
| ('mid', 'high', 50.0, 'periodic:60')  |        250.1 |            40.1 |              56.2 |      44.7 |              47.5 |           36   |
| ('mid', 'none', 10.0, 'deviation:30') |        250.1 |            40.2 |              59.2 |      58.6 |              57   |           46.2 |
| ('mid', 'none', 10.0, 'event')        |        250.2 |            40.1 |              64.4 |      55.9 |              62.2 |           51.4 |
| ('mid', 'none', 10.0, 'periodic:60')  |        250.1 |            40.2 |              55.7 |      44.3 |              44.8 |           40.7 |
| ('mid', 'none', 50.0, 'deviation:30') |        250.1 |            40.1 |              59.3 |      44.7 |              52.2 |           34.9 |
| ('mid', 'none', 50.0, 'event')        |        250.1 |            40.1 |              63   |      50   |              66.5 |           42.3 |
| ('mid', 'none', 50.0, 'periodic:60')  |        250.1 |            40.1 |              56.8 |      41.6 |              45.5 |           36.3 |

## Replanning calls per mission

|                                       |   alns_fixed |   alns_fixed@40 |   alns_stagnation |   anytime |   anytime_nodelay |   anytime_risk |
|:--------------------------------------|-------------:|----------------:|------------------:|----------:|------------------:|---------------:|
| ('low', 'high', 10.0, 'deviation:30') |          8.2 |             8.2 |               8.2 |       8.1 |               8.2 |            8.2 |
| ('low', 'high', 10.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('low', 'high', 10.0, 'periodic:60')  |         24.2 |            24.1 |              24   |      24.1 |              24.1 |           23.8 |
| ('low', 'high', 50.0, 'deviation:30') |          8.1 |             8.2 |               8.1 |       8.2 |               8.1 |            8.2 |
| ('low', 'high', 50.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('low', 'high', 50.0, 'periodic:60')  |         24.1 |            24.3 |              24.4 |      24   |              24.2 |           24   |
| ('low', 'none', 10.0, 'deviation:30') |          8.1 |             8.2 |               8.2 |       8.1 |               8.1 |            8.1 |
| ('low', 'none', 10.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('low', 'none', 10.0, 'periodic:60')  |         24   |            23.9 |              24   |      24   |              23.8 |           23.8 |
| ('low', 'none', 50.0, 'deviation:30') |          8.1 |             8.2 |               8.2 |       8.2 |               8.1 |            8.1 |
| ('low', 'none', 50.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('low', 'none', 50.0, 'periodic:60')  |         24.1 |            23.8 |              24.1 |      23.8 |              24   |           23.8 |
| ('mid', 'high', 10.0, 'deviation:30') |         11.3 |            11.4 |              11.3 |      11.3 |              11.3 |           11.3 |
| ('mid', 'high', 10.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('mid', 'high', 10.0, 'periodic:60')  |         24.8 |            24.8 |              24.7 |      24.6 |              24.7 |           24.8 |
| ('mid', 'high', 50.0, 'deviation:30') |         11.1 |            11.1 |              11.2 |      11.3 |              11.2 |           11.2 |
| ('mid', 'high', 50.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('mid', 'high', 50.0, 'periodic:60')  |         24.5 |            24.8 |              24.6 |      24.6 |              24.7 |           25   |
| ('mid', 'none', 10.0, 'deviation:30') |         11.3 |            11.2 |              11.2 |      11.2 |              11.2 |           11.3 |
| ('mid', 'none', 10.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('mid', 'none', 10.0, 'periodic:60')  |         24.9 |            24.5 |              24.8 |      24.7 |              24.6 |           24.7 |
| ('mid', 'none', 50.0, 'deviation:30') |         11.1 |            11.2 |              11.3 |      11.2 |              11.2 |           11.2 |
| ('mid', 'none', 50.0, 'event')        |          6.9 |             6.9 |               6.9 |       6.9 |               6.9 |            6.9 |
| ('mid', 'none', 50.0, 'periodic:60')  |         24.5 |            24.8 |              24.8 |      24.7 |              24.7 |           24.7 |

## anytime_risk minus other methods

| exec_level   | latency_level   |   kappa | trigger      | method          |    diff |   ci_lo |   ci_hi |    win |   loss | sig   |
|:-------------|:----------------|--------:|:-------------|:----------------|--------:|--------:|--------:|-------:|-------:|:------|
| low          | high            |      10 | deviation:30 | alns_fixed      |  0.0131 |  0.0018 |  0.025  | 0.5    | 0.3444 | +     |
| low          | high            |      10 | deviation:30 | alns_fixed@40   |  0.0088 |  0.0014 |  0.0167 | 0.3778 | 0.2111 | +     |
| low          | high            |      10 | deviation:30 | alns_stagnation |  0.0059 | -0.0032 |  0.015  | 0.3444 | 0.2889 | 0     |
| low          | high            |      10 | deviation:30 | anytime         |  0.0035 | -0.0036 |  0.0108 | 0.3333 | 0.2667 | 0     |
| low          | high            |      10 | deviation:30 | anytime_nodelay |  0.0028 | -0.0054 |  0.0109 | 0.3444 | 0.2667 | 0     |
| low          | high            |      10 | event        | alns_fixed      |  0.012  |  0.0004 |  0.0241 | 0.5333 | 0.3111 | +     |
| low          | high            |      10 | event        | alns_fixed@40   |  0.0069 | -0.0016 |  0.0157 | 0.3889 | 0.2111 | 0     |
| low          | high            |      10 | event        | alns_stagnation |  0.002  | -0.0066 |  0.0111 | 0.3111 | 0.3111 | 0     |
| low          | high            |      10 | event        | anytime         |  0.0054 | -0.0019 |  0.0129 | 0.3111 | 0.2667 | 0     |
| low          | high            |      10 | event        | anytime_nodelay |  0.0042 | -0.0036 |  0.0124 | 0.3667 | 0.2556 | 0     |
| low          | high            |      10 | periodic:60  | alns_fixed      |  0.0107 |  0.0006 |  0.0214 | 0.4889 | 0.3333 | +     |
| low          | high            |      10 | periodic:60  | alns_fixed@40   |  0.0038 | -0.0036 |  0.0112 | 0.3    | 0.2333 | 0     |
| low          | high            |      10 | periodic:60  | alns_stagnation |  0.0011 | -0.0073 |  0.0097 | 0.3333 | 0.3111 | 0     |
| low          | high            |      10 | periodic:60  | anytime         |  0.0072 | -0.0004 |  0.0152 | 0.3444 | 0.2333 | 0     |
| low          | high            |      10 | periodic:60  | anytime_nodelay |  0.0051 | -0.0023 |  0.0125 | 0.4111 | 0.2222 | 0     |
| low          | high            |      50 | deviation:30 | alns_fixed      |  0.0228 |  0.0087 |  0.0368 | 0.6778 | 0.3    | +     |
| low          | high            |      50 | deviation:30 | alns_fixed@40   |  0.0042 | -0.0056 |  0.0145 | 0.4222 | 0.3667 | 0     |
| low          | high            |      50 | deviation:30 | alns_stagnation |  0.005  | -0.0055 |  0.0158 | 0.4667 | 0.3444 | 0     |
| low          | high            |      50 | deviation:30 | anytime         |  0.0049 | -0.0029 |  0.013  | 0.4222 | 0.3    | 0     |
| low          | high            |      50 | deviation:30 | anytime_nodelay |  0.0043 | -0.0054 |  0.014  | 0.4778 | 0.3222 | 0     |
| low          | high            |      50 | event        | alns_fixed      |  0.0299 |  0.0137 |  0.0459 | 0.6111 | 0.3222 | +     |
| low          | high            |      50 | event        | alns_fixed@40   |  0.0076 | -0.0028 |  0.0181 | 0.5    | 0.2667 | 0     |
| low          | high            |      50 | event        | alns_stagnation |  0.0122 |  0.0002 |  0.0244 | 0.5222 | 0.3444 | +     |
| low          | high            |      50 | event        | anytime         |  0.0083 | -0.0011 |  0.0178 | 0.5222 | 0.2556 | 0     |
| low          | high            |      50 | event        | anytime_nodelay |  0.0053 | -0.0057 |  0.0161 | 0.4889 | 0.3222 | 0     |
| low          | high            |      50 | periodic:60  | alns_fixed      |  0.0252 |  0.0134 |  0.0381 | 0.6444 | 0.2889 | +     |
| low          | high            |      50 | periodic:60  | alns_fixed@40   |  0.0072 | -0.0033 |  0.0182 | 0.5    | 0.3444 | 0     |
| low          | high            |      50 | periodic:60  | alns_stagnation |  0.0075 | -0.0031 |  0.0187 | 0.5111 | 0.3444 | 0     |
| low          | high            |      50 | periodic:60  | anytime         |  0.0072 | -0.003  |  0.018  | 0.4444 | 0.3667 | 0     |
| low          | high            |      50 | periodic:60  | anytime_nodelay |  0.0076 | -0.0037 |  0.0195 | 0.4889 | 0.3222 | 0     |
| low          | none            |      10 | deviation:30 | alns_fixed      |  0.008  | -0.0028 |  0.0194 | 0.5    | 0.3889 | 0     |
| low          | none            |      10 | deviation:30 | alns_fixed@40   |  0.0061 | -0.0025 |  0.0151 | 0.3333 | 0.2667 | 0     |
| low          | none            |      10 | deviation:30 | alns_stagnation |  0.0033 | -0.0056 |  0.0129 | 0.2889 | 0.3    | 0     |
| low          | none            |      10 | deviation:30 | anytime         |  0.0065 | -0.0002 |  0.0136 | 0.3778 | 0.2    | 0     |
| low          | none            |      10 | deviation:30 | anytime_nodelay |  0.0065 | -0.0013 |  0.0145 | 0.4222 | 0.2111 | 0     |
| low          | none            |      10 | event        | alns_fixed      |  0.005  | -0.0063 |  0.0166 | 0.5    | 0.4    | 0     |
| low          | none            |      10 | event        | alns_fixed@40   |  0.006  | -0.0033 |  0.0156 | 0.4    | 0.1889 | 0     |
| low          | none            |      10 | event        | alns_stagnation |  0.0021 | -0.0075 |  0.0119 | 0.4    | 0.3222 | 0     |
| low          | none            |      10 | event        | anytime         |  0.0064 | -0.002  |  0.0151 | 0.4333 | 0.2333 | 0     |
| low          | none            |      10 | event        | anytime_nodelay |  0.0061 | -0.0026 |  0.0147 | 0.4444 | 0.2444 | 0     |
| low          | none            |      10 | periodic:60  | alns_fixed      |  0.0069 | -0.0028 |  0.0166 | 0.5    | 0.3444 | 0     |
| low          | none            |      10 | periodic:60  | alns_fixed@40   |  0.0086 | -0.0002 |  0.0176 | 0.4    | 0.2    | 0     |
| low          | none            |      10 | periodic:60  | alns_stagnation |  0.0045 | -0.0038 |  0.0129 | 0.4222 | 0.2556 | 0     |
| low          | none            |      10 | periodic:60  | anytime         |  0.0088 |  0.0017 |  0.0163 | 0.3778 | 0.1778 | +     |
| low          | none            |      10 | periodic:60  | anytime_nodelay |  0.0062 | -0.0021 |  0.0146 | 0.4111 | 0.2556 | 0     |
| low          | none            |      50 | deviation:30 | alns_fixed      |  0.0223 |  0.0094 |  0.0353 | 0.6222 | 0.3333 | +     |
| low          | none            |      50 | deviation:30 | alns_fixed@40   |  0.0065 | -0.0041 |  0.0174 | 0.4556 | 0.3111 | 0     |
| low          | none            |      50 | deviation:30 | alns_stagnation |  0.0076 | -0.004  |  0.0196 | 0.5    | 0.3889 | 0     |
| low          | none            |      50 | deviation:30 | anytime         |  0.0088 | -0.0003 |  0.0179 | 0.5111 | 0.2889 | 0     |
| low          | none            |      50 | deviation:30 | anytime_nodelay |  0.0086 | -0.0012 |  0.0186 | 0.4667 | 0.3444 | 0     |
| low          | none            |      50 | event        | alns_fixed      |  0.0252 |  0.0116 |  0.0394 | 0.6222 | 0.3    | +     |
| low          | none            |      50 | event        | alns_fixed@40   |  0.011  |  0.002  |  0.0204 | 0.4889 | 0.2889 | +     |
| low          | none            |      50 | event        | alns_stagnation |  0.0086 | -0.0029 |  0.0201 | 0.5    | 0.3444 | 0     |
| low          | none            |      50 | event        | anytime         |  0.0115 |  0.0041 |  0.0193 | 0.5444 | 0.2222 | +     |
| low          | none            |      50 | event        | anytime_nodelay |  0.0062 | -0.0042 |  0.0165 | 0.4667 | 0.3222 | 0     |
| low          | none            |      50 | periodic:60  | alns_fixed      |  0.0247 |  0.0118 |  0.038  | 0.6333 | 0.3444 | +     |
| low          | none            |      50 | periodic:60  | alns_fixed@40   |  0.0111 |  0.0024 |  0.0203 | 0.5111 | 0.2778 | +     |
| low          | none            |      50 | periodic:60  | alns_stagnation |  0.009  | -0.0007 |  0.0192 | 0.4444 | 0.3889 | 0     |
| low          | none            |      50 | periodic:60  | anytime         |  0.0147 |  0.0065 |  0.0235 | 0.5111 | 0.2556 | +     |
| low          | none            |      50 | periodic:60  | anytime_nodelay |  0.01   |  0.0003 |  0.0205 | 0.4778 | 0.3111 | +     |
| mid          | high            |      10 | deviation:30 | alns_fixed      | -0.0018 | -0.0133 |  0.0093 | 0.4111 | 0.4    | 0     |
| mid          | high            |      10 | deviation:30 | alns_fixed@40   | -0.0007 | -0.0112 |  0.0101 | 0.2889 | 0.3778 | 0     |
| mid          | high            |      10 | deviation:30 | alns_stagnation |  0.002  | -0.0084 |  0.0125 | 0.3333 | 0.3111 | 0     |
| mid          | high            |      10 | deviation:30 | anytime         |  0.0047 | -0.0043 |  0.0139 | 0.3222 | 0.2889 | 0     |
| mid          | high            |      10 | deviation:30 | anytime_nodelay | -0.0016 | -0.0105 |  0.0076 | 0.2778 | 0.3111 | 0     |
| mid          | high            |      10 | event        | alns_fixed      |  0.0045 | -0.0069 |  0.0159 | 0.4333 | 0.3444 | 0     |
| mid          | high            |      10 | event        | alns_fixed@40   |  0.0083 |  0.0008 |  0.0162 | 0.4111 | 0.2222 | +     |
| mid          | high            |      10 | event        | alns_stagnation |  0.0039 | -0.0052 |  0.0129 | 0.3333 | 0.3111 | 0     |
| mid          | high            |      10 | event        | anytime         | -0.0001 | -0.0084 |  0.0083 | 0.3111 | 0.2889 | 0     |
| mid          | high            |      10 | event        | anytime_nodelay | -0.001  | -0.0098 |  0.0082 | 0.2667 | 0.3444 | 0     |
| mid          | high            |      10 | periodic:60  | alns_fixed      |  0.0007 | -0.0111 |  0.0123 | 0.4444 | 0.4    | 0     |
| mid          | high            |      10 | periodic:60  | alns_fixed@40   |  0.0098 | -0.0004 |  0.0206 | 0.3889 | 0.2667 | 0     |
| mid          | high            |      10 | periodic:60  | alns_stagnation |  0.0108 | -0.0002 |  0.022  | 0.3889 | 0.2667 | 0     |
| mid          | high            |      10 | periodic:60  | anytime         |  0.0042 | -0.0042 |  0.0127 | 0.3444 | 0.2556 | 0     |
| mid          | high            |      10 | periodic:60  | anytime_nodelay |  0.0072 | -0.0028 |  0.018  | 0.4    | 0.2444 | 0     |
| mid          | high            |      50 | deviation:30 | alns_fixed      |  0.0125 | -0.0015 |  0.0265 | 0.5222 | 0.4    | 0     |
| mid          | high            |      50 | deviation:30 | alns_fixed@40   |  0.0126 |  0.0016 |  0.0239 | 0.4667 | 0.3444 | +     |
| mid          | high            |      50 | deviation:30 | alns_stagnation |  0.0147 |  0.0022 |  0.0274 | 0.4667 | 0.3222 | +     |
| mid          | high            |      50 | deviation:30 | anytime         |  0.0142 |  0.0038 |  0.0251 | 0.4889 | 0.2667 | +     |
| mid          | high            |      50 | deviation:30 | anytime_nodelay |  0.0163 |  0.0052 |  0.0278 | 0.4889 | 0.3222 | +     |
| mid          | high            |      50 | event        | alns_fixed      |  0.0152 |  0.0017 |  0.029  | 0.5444 | 0.4    | +     |
| mid          | high            |      50 | event        | alns_fixed@40   |  0.0065 | -0.0042 |  0.018  | 0.3778 | 0.3889 | 0     |
| mid          | high            |      50 | event        | alns_stagnation |  0.0054 | -0.0052 |  0.0168 | 0.4333 | 0.3889 | 0     |
| mid          | high            |      50 | event        | anytime         |  0.0063 | -0.0047 |  0.0179 | 0.3667 | 0.3556 | 0     |
| mid          | high            |      50 | event        | anytime_nodelay |  0.005  | -0.0066 |  0.0167 | 0.4111 | 0.3889 | 0     |
| mid          | high            |      50 | periodic:60  | alns_fixed      |  0.0088 | -0.005  |  0.0226 | 0.5333 | 0.4222 | 0     |
| mid          | high            |      50 | periodic:60  | alns_fixed@40   |  0.0084 | -0.0021 |  0.0184 | 0.4111 | 0.3222 | 0     |
| mid          | high            |      50 | periodic:60  | alns_stagnation |  0.0133 |  0.0028 |  0.0238 | 0.4889 | 0.3    | +     |
| mid          | high            |      50 | periodic:60  | anytime         |  0.0069 | -0.0029 |  0.017  | 0.3889 | 0.3889 | 0     |
| mid          | high            |      50 | periodic:60  | anytime_nodelay |  0.0068 | -0.0029 |  0.0168 | 0.4333 | 0.3444 | 0     |
| mid          | none            |      10 | deviation:30 | alns_fixed      |  0.0042 | -0.0067 |  0.0151 | 0.5222 | 0.3778 | 0     |
| mid          | none            |      10 | deviation:30 | alns_fixed@40   |  0.0053 | -0.0053 |  0.016  | 0.3556 | 0.3    | 0     |
| mid          | none            |      10 | deviation:30 | alns_stagnation |  0.0019 | -0.0082 |  0.012  | 0.3778 | 0.3444 | 0     |
| mid          | none            |      10 | deviation:30 | anytime         |  0.0062 | -0.0016 |  0.0142 | 0.3444 | 0.2778 | 0     |
| mid          | none            |      10 | deviation:30 | anytime_nodelay |  0.0055 | -0.0031 |  0.0143 | 0.3667 | 0.3    | 0     |
| mid          | none            |      10 | event        | alns_fixed      |  0.0105 | -0.0004 |  0.0218 | 0.5667 | 0.3111 | 0     |
| mid          | none            |      10 | event        | alns_fixed@40   |  0.0106 |  0.0007 |  0.0208 | 0.4222 | 0.2778 | +     |
| mid          | none            |      10 | event        | alns_stagnation |  0.0034 | -0.0048 |  0.0116 | 0.3889 | 0.3111 | 0     |
| mid          | none            |      10 | event        | anytime         |  0.0101 |  0.0015 |  0.0191 | 0.3778 | 0.2444 | +     |
| mid          | none            |      10 | event        | anytime_nodelay |  0.0051 | -0.0041 |  0.0146 | 0.4    | 0.2889 | 0     |
| mid          | none            |      10 | periodic:60  | alns_fixed      |  0.0037 | -0.0111 |  0.0181 | 0.4667 | 0.4111 | 0     |
| mid          | none            |      10 | periodic:60  | alns_fixed@40   |  0.0142 |  0.0051 |  0.0236 | 0.4444 | 0.2111 | +     |
| mid          | none            |      10 | periodic:60  | alns_stagnation |  0.0085 | -0.0029 |  0.0201 | 0.4556 | 0.2556 | 0     |
| mid          | none            |      10 | periodic:60  | anytime         |  0.0147 |  0.0042 |  0.0262 | 0.4    | 0.1778 | +     |
| mid          | none            |      10 | periodic:60  | anytime_nodelay |  0.0103 |  0.0005 |  0.0207 | 0.4    | 0.2333 | +     |
| mid          | none            |      50 | deviation:30 | alns_fixed      |  0.0141 |  0.0005 |  0.0279 | 0.5556 | 0.3444 | +     |
| mid          | none            |      50 | deviation:30 | alns_fixed@40   |  0.0023 | -0.0094 |  0.0141 | 0.4333 | 0.3889 | 0     |
| mid          | none            |      50 | deviation:30 | alns_stagnation | -0.0021 | -0.014  |  0.01   | 0.3778 | 0.4889 | 0     |
| mid          | none            |      50 | deviation:30 | anytime         |  0.0039 | -0.0082 |  0.016  | 0.3778 | 0.4111 | 0     |
| mid          | none            |      50 | deviation:30 | anytime_nodelay |  0.0085 | -0.0032 |  0.0204 | 0.4667 | 0.3667 | 0     |
| mid          | none            |      50 | event        | alns_fixed      |  0.0182 |  0.0047 |  0.032  | 0.5444 | 0.3778 | +     |
| mid          | none            |      50 | event        | alns_fixed@40   |  0.0071 | -0.0046 |  0.0187 | 0.4778 | 0.3778 | 0     |
| mid          | none            |      50 | event        | alns_stagnation |  0.01   | -0.0013 |  0.0217 | 0.5222 | 0.3444 | 0     |
| mid          | none            |      50 | event        | anytime         |  0.007  | -0.0045 |  0.0185 | 0.4222 | 0.3889 | 0     |
| mid          | none            |      50 | event        | anytime_nodelay |  0.0049 | -0.0067 |  0.0171 | 0.4    | 0.4    | 0     |
| mid          | none            |      50 | periodic:60  | alns_fixed      |  0.0009 | -0.0124 |  0.0144 | 0.3778 | 0.5    | 0     |
| mid          | none            |      50 | periodic:60  | alns_fixed@40   |  0.005  | -0.0076 |  0.0178 | 0.3889 | 0.3889 | 0     |
| mid          | none            |      50 | periodic:60  | alns_stagnation |  0.0039 | -0.0089 |  0.0164 | 0.4222 | 0.4111 | 0     |
| mid          | none            |      50 | periodic:60  | anytime         |  0.0086 | -0.0031 |  0.0201 | 0.4222 | 0.3222 | 0     |
| mid          | none            |      50 | periodic:60  | anytime_nodelay |  0.0085 | -0.003  |  0.0198 | 0.4222 | 0.3778 | 0     |

Count of significant wins (+), ties (0), losses (-):

| method          |   + |   0 |
|:----------------|----:|----:|
| alns_fixed      |  12 |  12 |
| alns_fixed@40   |   7 |  17 |
| alns_stagnation |   3 |  21 |
| anytime         |   6 |  18 |
| anytime_nodelay |   3 |  21 |

## Trigger minus event-only replanning (same method)

| exec_level   | latency_level   |   kappa | method          | trigger      | vs    |    diff |   ci_lo |   ci_hi |    win |   loss | sig   |
|:-------------|:----------------|--------:|:----------------|:-------------|:------|--------:|--------:|--------:|-------:|-------:|:------|
| low          | high            |      10 | alns_fixed      | deviation:30 | event |  0.0046 | -0.0001 |  0.0095 | 0.3333 | 0.1222 | 0     |
| low          | high            |      10 | alns_fixed@40   | deviation:30 | event |  0.0039 | -0.0023 |  0.0098 | 0.3667 | 0.1667 | 0     |
| low          | high            |      10 | alns_stagnation | deviation:30 | event |  0.0019 | -0.0034 |  0.0074 | 0.3333 | 0.1778 | 0     |
| low          | high            |      10 | anytime         | deviation:30 | event |  0.0076 |  0.0017 |  0.014  | 0.3111 | 0.1667 | +     |
| low          | high            |      10 | anytime_nodelay | deviation:30 | event |  0.0072 |  0.0027 |  0.0122 | 0.3333 | 0.1111 | +     |
| low          | high            |      10 | anytime_risk    | deviation:30 | event |  0.0058 |  0.0013 |  0.0103 | 0.3444 | 0.1222 | +     |
| low          | high            |      50 | alns_fixed      | deviation:30 | event |  0.0059 |  0.0004 |  0.0112 | 0.3333 | 0.1889 | +     |
| low          | high            |      50 | alns_fixed@40   | deviation:30 | event |  0.0022 | -0.0046 |  0.0082 | 0.3778 | 0.1889 | 0     |
| low          | high            |      50 | alns_stagnation | deviation:30 | event |  0.006  | -0.0006 |  0.0122 | 0.4222 | 0.2111 | 0     |
| low          | high            |      50 | anytime         | deviation:30 | event |  0.0021 | -0.0043 |  0.0087 | 0.3667 | 0.2333 | 0     |
| low          | high            |      50 | anytime_nodelay | deviation:30 | event | -0.0002 | -0.0062 |  0.0056 | 0.3222 | 0.2333 | 0     |
| low          | high            |      50 | anytime_risk    | deviation:30 | event | -0.0012 | -0.009  |  0.0061 | 0.2778 | 0.2556 | 0     |
| low          | none            |      10 | alns_fixed      | deviation:30 | event |  0.0022 | -0.0031 |  0.0072 | 0.2778 | 0.1889 | 0     |
| low          | none            |      10 | alns_fixed@40   | deviation:30 | event |  0.0051 | -0.0013 |  0.0112 | 0.3556 | 0.1889 | 0     |
| low          | none            |      10 | alns_stagnation | deviation:30 | event |  0.004  | -0.0028 |  0.0105 | 0.3222 | 0.2111 | 0     |
| low          | none            |      10 | anytime         | deviation:30 | event |  0.0051 | -0.0012 |  0.0111 | 0.3556 | 0.1333 | 0     |
| low          | none            |      10 | anytime_nodelay | deviation:30 | event |  0.0048 | -0.0013 |  0.0112 | 0.3111 | 0.1778 | 0     |
| low          | none            |      10 | anytime_risk    | deviation:30 | event |  0.0052 |  0.0006 |  0.0102 | 0.3    | 0.1444 | +     |
| low          | none            |      50 | alns_fixed      | deviation:30 | event |  0.0057 |  0.0006 |  0.0105 | 0.3444 | 0.1222 | +     |
| low          | none            |      50 | alns_fixed@40   | deviation:30 | event |  0.0073 |  0.0016 |  0.013  | 0.4    | 0.1444 | +     |
| low          | none            |      50 | alns_stagnation | deviation:30 | event |  0.0037 | -0.0015 |  0.0093 | 0.3    | 0.2333 | 0     |
| low          | none            |      50 | anytime         | deviation:30 | event |  0.0055 |  0.0004 |  0.0105 | 0.3667 | 0.1333 | +     |
| low          | none            |      50 | anytime_nodelay | deviation:30 | event |  0.0004 | -0.0057 |  0.006  | 0.3667 | 0.2111 | 0     |
| low          | none            |      50 | anytime_risk    | deviation:30 | event |  0.0028 | -0.004  |  0.0092 | 0.2889 | 0.2222 | 0     |
| mid          | high            |      10 | alns_fixed      | deviation:30 | event |  0.0091 |  0.0006 |  0.0173 | 0.4778 | 0.1889 | +     |
| mid          | high            |      10 | alns_fixed@40   | deviation:30 | event |  0.0119 |  0.0009 |  0.0224 | 0.4667 | 0.2333 | +     |
| mid          | high            |      10 | alns_stagnation | deviation:30 | event |  0.0048 | -0.0044 |  0.0131 | 0.4333 | 0.2222 | 0     |
| mid          | high            |      10 | anytime         | deviation:30 | event | -0.0019 | -0.012  |  0.0072 | 0.3889 | 0.2667 | 0     |
| mid          | high            |      10 | anytime_nodelay | deviation:30 | event |  0.0036 | -0.0055 |  0.0117 | 0.3778 | 0.2222 | 0     |
| mid          | high            |      10 | anytime_risk    | deviation:30 | event |  0.0029 | -0.0071 |  0.0122 | 0.4    | 0.2556 | 0     |
| mid          | high            |      50 | alns_fixed      | deviation:30 | event |  0.0085 |  0.0013 |  0.0156 | 0.4556 | 0.2667 | +     |
| mid          | high            |      50 | alns_fixed@40   | deviation:30 | event | -0.0002 | -0.0096 |  0.0091 | 0.3889 | 0.3222 | 0     |
| mid          | high            |      50 | alns_stagnation | deviation:30 | event | -0.0034 | -0.0151 |  0.0081 | 0.3333 | 0.4222 | 0     |
| mid          | high            |      50 | anytime         | deviation:30 | event | -0.002  | -0.0127 |  0.0079 | 0.3333 | 0.3    | 0     |
| mid          | high            |      50 | anytime_nodelay | deviation:30 | event | -0.0055 | -0.015  |  0.0031 | 0.3556 | 0.3111 | 0     |
| mid          | high            |      50 | anytime_risk    | deviation:30 | event |  0.0058 | -0.005  |  0.0161 | 0.4222 | 0.2778 | 0     |
| mid          | none            |      10 | alns_fixed      | deviation:30 | event |  0.0091 |  0.0006 |  0.0171 | 0.4111 | 0.2444 | +     |
| mid          | none            |      10 | alns_fixed@40   | deviation:30 | event |  0.0081 | -0.0014 |  0.0171 | 0.4444 | 0.2444 | 0     |
| mid          | none            |      10 | alns_stagnation | deviation:30 | event |  0.0044 | -0.0043 |  0.0124 | 0.4    | 0.2667 | 0     |
| mid          | none            |      10 | anytime         | deviation:30 | event |  0.0067 | -0.0033 |  0.0163 | 0.3889 | 0.2222 | 0     |
| mid          | none            |      10 | anytime_nodelay | deviation:30 | event |  0.0024 | -0.0074 |  0.0117 | 0.3889 | 0.3    | 0     |
| mid          | none            |      10 | anytime_risk    | deviation:30 | event |  0.0029 | -0.0065 |  0.0114 | 0.4556 | 0.2333 | 0     |
| mid          | none            |      50 | alns_fixed      | deviation:30 | event |  0.0084 |  0.0016 |  0.0154 | 0.4    | 0.2889 | +     |
| mid          | none            |      50 | alns_fixed@40   | deviation:30 | event |  0.009  |  0      |  0.0174 | 0.4333 | 0.2111 | +     |
| mid          | none            |      50 | alns_stagnation | deviation:30 | event |  0.0163 |  0.007  |  0.0255 | 0.4778 | 0.2111 | +     |
| mid          | none            |      50 | anytime         | deviation:30 | event |  0.0074 | -0.0034 |  0.0172 | 0.4333 | 0.2444 | 0     |
| mid          | none            |      50 | anytime_nodelay | deviation:30 | event |  0.0006 | -0.0109 |  0.0111 | 0.4444 | 0.2778 | 0     |
| mid          | none            |      50 | anytime_risk    | deviation:30 | event |  0.0042 | -0.0055 |  0.0136 | 0.5    | 0.2444 | 0     |
| low          | high            |      10 | alns_fixed      | periodic:60  | event |  0.0112 |  0.0036 |  0.0188 | 0.4667 | 0.2    | +     |
| low          | high            |      10 | alns_fixed@40   | periodic:60  | event |  0.0131 |  0.0059 |  0.0205 | 0.5    | 0.1778 | +     |
| low          | high            |      10 | alns_stagnation | periodic:60  | event |  0.0108 |  0.0037 |  0.0185 | 0.4889 | 0.1889 | +     |
| low          | high            |      10 | anytime         | periodic:60  | event |  0.0082 | -0.0012 |  0.0166 | 0.4778 | 0.2    | 0     |
| low          | high            |      10 | anytime_nodelay | periodic:60  | event |  0.0091 |  0.0002 |  0.0175 | 0.4667 | 0.2    | +     |
| low          | high            |      10 | anytime_risk    | periodic:60  | event |  0.0099 |  0.002  |  0.0172 | 0.4889 | 0.2    | +     |
| low          | high            |      50 | alns_fixed      | periodic:60  | event |  0.0162 |  0.0063 |  0.0262 | 0.5556 | 0.2111 | +     |
| low          | high            |      50 | alns_fixed@40   | periodic:60  | event |  0.0118 |  0.0053 |  0.0186 | 0.4889 | 0.1778 | +     |
| low          | high            |      50 | alns_stagnation | periodic:60  | event |  0.0162 |  0.0074 |  0.0249 | 0.5667 | 0.1778 | +     |
| low          | high            |      50 | anytime         | periodic:60  | event |  0.0125 |  0.0026 |  0.0219 | 0.5667 | 0.2444 | +     |
| low          | high            |      50 | anytime_nodelay | periodic:60  | event |  0.0092 |  0.0004 |  0.0172 | 0.5    | 0.2111 | +     |
| low          | high            |      50 | anytime_risk    | periodic:60  | event |  0.0114 |  0.0023 |  0.0202 | 0.5    | 0.1889 | +     |
| low          | none            |      10 | alns_fixed      | periodic:60  | event |  0.012  |  0.0041 |  0.0206 | 0.4778 | 0.2    | +     |
| low          | none            |      10 | alns_fixed@40   | periodic:60  | event |  0.0113 |  0.004  |  0.0189 | 0.4778 | 0.2667 | +     |
| low          | none            |      10 | alns_stagnation | periodic:60  | event |  0.0115 |  0.0043 |  0.0186 | 0.5333 | 0.2111 | +     |
| low          | none            |      10 | anytime         | periodic:60  | event |  0.0115 |  0.0044 |  0.0187 | 0.5667 | 0.1778 | +     |
| low          | none            |      10 | anytime_nodelay | periodic:60  | event |  0.0139 |  0.0074 |  0.0202 | 0.5667 | 0.1333 | +     |
| low          | none            |      10 | anytime_risk    | periodic:60  | event |  0.0139 |  0.007  |  0.0207 | 0.5333 | 0.1556 | +     |
| low          | none            |      50 | alns_fixed      | periodic:60  | event |  0.0146 |  0.0055 |  0.0236 | 0.5333 | 0.2222 | +     |
| low          | none            |      50 | alns_fixed@40   | periodic:60  | event |  0.014  |  0.007  |  0.0212 | 0.5    | 0.1778 | +     |
| low          | none            |      50 | alns_stagnation | periodic:60  | event |  0.0136 |  0.0057 |  0.0217 | 0.5111 | 0.2444 | +     |
| low          | none            |      50 | anytime         | periodic:60  | event |  0.0109 |  0.0035 |  0.0181 | 0.5    | 0.1556 | +     |
| low          | none            |      50 | anytime_nodelay | periodic:60  | event |  0.0102 |  0.0026 |  0.0173 | 0.5111 | 0.2    | +     |
| low          | none            |      50 | anytime_risk    | periodic:60  | event |  0.0141 |  0.0056 |  0.0227 | 0.5444 | 0.1778 | +     |
| mid          | high            |      10 | alns_fixed      | periodic:60  | event |  0.0181 |  0.0072 |  0.029  | 0.5556 | 0.2333 | +     |
| mid          | high            |      10 | alns_fixed@40   | periodic:60  | event |  0.0129 |  0.0015 |  0.0239 | 0.5667 | 0.3111 | +     |
| mid          | high            |      10 | alns_stagnation | periodic:60  | event |  0.0075 | -0.0045 |  0.0192 | 0.5444 | 0.3    | 0     |
| mid          | high            |      10 | anytime         | periodic:60  | event |  0.01   | -0.002  |  0.0219 | 0.5333 | 0.3333 | 0     |
| mid          | high            |      10 | anytime_nodelay | periodic:60  | event |  0.0062 | -0.0062 |  0.0182 | 0.5    | 0.3333 | 0     |
| mid          | high            |      10 | anytime_risk    | periodic:60  | event |  0.0144 |  0.0025 |  0.026  | 0.5222 | 0.3222 | +     |
| mid          | high            |      50 | alns_fixed      | periodic:60  | event |  0.0191 |  0.0101 |  0.028  | 0.6    | 0.1556 | +     |
| mid          | high            |      50 | alns_fixed@40   | periodic:60  | event |  0.0109 | -0.0013 |  0.0231 | 0.5222 | 0.3222 | 0     |
| mid          | high            |      50 | alns_stagnation | periodic:60  | event |  0.0049 | -0.0071 |  0.0166 | 0.5111 | 0.3333 | 0     |
| mid          | high            |      50 | anytime         | periodic:60  | event |  0.0121 | -0      |  0.0246 | 0.5    | 0.3444 | 0     |
| mid          | high            |      50 | anytime_nodelay | periodic:60  | event |  0.0109 | -0.0002 |  0.0216 | 0.5889 | 0.2667 | 0     |
| mid          | high            |      50 | anytime_risk    | periodic:60  | event |  0.0127 | -0.0005 |  0.0253 | 0.5778 | 0.3    | 0     |
| mid          | none            |      10 | alns_fixed      | periodic:60  | event |  0.0131 |  0.0008 |  0.0248 | 0.6222 | 0.2333 | +     |
| mid          | none            |      10 | alns_fixed@40   | periodic:60  | event |  0.0026 | -0.0083 |  0.0134 | 0.4444 | 0.3889 | 0     |
| mid          | none            |      10 | alns_stagnation | periodic:60  | event |  0.0012 | -0.0096 |  0.0115 | 0.5222 | 0.2889 | 0     |
| mid          | none            |      10 | anytime         | periodic:60  | event |  0.0017 | -0.0102 |  0.0132 | 0.4333 | 0.3778 | 0     |
| mid          | none            |      10 | anytime_nodelay | periodic:60  | event |  0.0011 | -0.0109 |  0.0125 | 0.4667 | 0.3222 | 0     |
| mid          | none            |      10 | anytime_risk    | periodic:60  | event |  0.0063 | -0.0046 |  0.0166 | 0.5333 | 0.2667 | 0     |
| mid          | none            |      50 | alns_fixed      | periodic:60  | event |  0.0239 |  0.0146 |  0.0332 | 0.6556 | 0.1444 | +     |
| mid          | none            |      50 | alns_fixed@40   | periodic:60  | event |  0.0086 | -0.0026 |  0.0192 | 0.5333 | 0.3222 | 0     |
| mid          | none            |      50 | alns_stagnation | periodic:60  | event |  0.0126 |  0.002  |  0.0227 | 0.6222 | 0.2444 | +     |
| mid          | none            |      50 | anytime         | periodic:60  | event |  0.0049 | -0.0058 |  0.015  | 0.5333 | 0.3111 | 0     |
| mid          | none            |      50 | anytime_nodelay | periodic:60  | event |  0.0029 | -0.0089 |  0.0144 | 0.5889 | 0.3    | 0     |
| mid          | none            |      50 | anytime_risk    | periodic:60  | event |  0.0066 | -0.0064 |  0.0186 | 0.5444 | 0.2778 | 0     |
