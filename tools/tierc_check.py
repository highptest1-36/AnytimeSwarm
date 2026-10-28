"""Tier C held-out checks: real-time factor per run and tier B / tier C scenario alignment."""
import glob
import json

import pandas as pd

J = "/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal"
rows = []
for f in sorted(glob.glob(f"{J}/results/tier_c/heldout_C/gz-*.json")):
    m = json.load(open(f))
    rows.append({k: v for k, v in m.items() if not k.startswith("_")})
c = pd.DataFrame(rows)
print(c.rtf.describe())
print(c[c.rtf < 1.6][["scenario", "method", "rtf", "utility_rate"]])
b = pd.read_csv(f"{J}/results/tier_b/heldout_B_gz.csv")
print("C scenarios", sorted(c.scenario.unique())[:3], "B scenarios", sorted(b.scenario.unique())[:3])
both = c.merge(b, on=["scenario", "method"], suffixes=("_c", "_b"))
print("matched runs", len(both), "pearson", both.utility_rate_c.corr(both.utility_rate_b).round(3))
print(both.groupby("method")[["utility_rate_b", "utility_rate_c"]].mean().round(4))
