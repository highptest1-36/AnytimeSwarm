#!/usr/bin/env python3
"""Study 4 development selection (dev seeds 0-9 only).

    python experiments/analyze_dev4.py results/tier_b/dev4_tune.csv [more csv ...]

Every planning model has one parameter (z of the effective deadline, c of the proportional buffer, z of moment
propagation, (n0, z) of online calibration). The rule is that of study 2: per disturbance level, the value with the
highest mean utility over both window factors and the three latency factors; online calibration uses one value for
both levels. Prints the table per level x window and the selection.
"""
import sys

import pandas as pd


def family(m: str) -> tuple[str, str]:
    base = m.split("~")[0]
    opt = m.split("~")[1].split("+")[0] if "~" in m else ""
    kv = dict(x.split("=") for x in opt.split(";") if x)
    kv.pop("fb", None)
    if "prop" in kv:
        return f"{base} prop", kv["prop"]
    if "mp" in kv:
        return f"{base} mp", kv["mp"]
    if "online" in kv:
        return f"{base} online", f"n0={kv['online']},z={kv.get('z', 'auto')}"
    if "z" in kv:
        return f"{base} cc", kv["z"]
    return base, "-"


def main():
    d = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
    d = d.drop_duplicates(["method", "exec_level", "kappa", "window", "scenario"], keep="last")
    d[["family", "param"]] = d.method.apply(lambda m: pd.Series(family(m)))
    d["U"] = 100 * d.utility_rate
    g = d.groupby(["family", "param"])
    t = d.pivot_table(index=["family", "param"], columns=["exec_level", "window"], values="U", aggfunc="mean")
    t.columns = [f"{x}/w{w:g}" for x, w in t.columns]
    t["mid"] = d[d.exec_level == "mid"].groupby(["family", "param"]).U.mean()
    t["high"] = d[d.exec_level == "high"].groupby(["family", "param"]).U.mean()
    t["all"] = g.U.mean()
    t["it/ms"] = g.iters_per_ms.mean()
    t["late"] = g.late_served.mean()
    t["lost"] = g.dropped_in_exec.mean()
    pd.set_option("display.width", 200)
    print(t.round(2).to_string())
    print("\nselection (max mean utility per level; online: max over both levels)")
    for fam, s in t.groupby(level=0):
        s = s.droplevel(0)
        if fam.endswith("online"):
            print(f"  {fam:22s} both: {s['all'].idxmax()} ({s['all'].max():.2f})")
        else:
            print(f"  {fam:22s} mid: {s['mid'].idxmax()} ({s['mid'].max():.2f})  "
                  f"high: {s['high'].idxmax()} ({s['high'].max():.2f})")

if __name__ == "__main__":
    main()
