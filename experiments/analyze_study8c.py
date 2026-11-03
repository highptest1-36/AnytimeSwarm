"""Study 8c analysis (docs/18_PROTOCOL_V8.md sections 5 and 6): the cost-aware fallback in PX4/Gazebo flights, high
disturbances, halved windows, seeds 17000-17019 (60 missions, three methods).

    python experiments/analyze_study8c.py                                   # held-out flights
    python experiments/analyze_study8c.py --dir results/tier_c/dev8c_smoke --dev   # smoke flights, report only

Fixed sequence at two-sided 0.05, cost-aware fallback (CAfee) minus nominal fallback (CCfb):
    H35  late arrivals per mission (supported if negative and p < 0.05),
    H36  score u_1 = U - n_late / n (tested only if H35 is supported; supported if positive and p < 0.05).
Paired bootstrap over missions (10 000 resamples, seed 0, 95% percentile interval, two-sided p). A mission enters when
all three methods have a valid run (real-time factor in [1.6, 2.2]; a run outside was repeated once and the original
moved to invalid_rtf/, used in the sensitivity analysis). Secondary: CAfee - Prop and CCfb - Prop, U, the tier B
prediction of every comparison on the same missions (results/tier_b/s8c_heldout_B_gz.csv), per-run agreement of tier B
and tier C, planning time and real-time factor.
Writes paper_journal/tables/numbers_s8c.tex (macros \\val{T...}), tables/tab_s8c.tex and results/study8/report_c.md.
The figure is drawn by experiments/paper_s8fig.py (presentation only).
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "results" / "tier_c" / "s8c_heldout_C"
BGZ = ROOT / "results" / "tier_b" / "s8c_heldout_B_gz.csv"
P = ROOT / "paper_journal"
OUT = ROOT / "results" / "study8"
CA, FB, PR = "alns_fixed@40~z=0.5,lam=1,cost=fee", "alns_fixed@40~z=0.5,fb=nominal", "alns_fixed@40~prop=0.45,fb=none"
B_OF = {m: m.replace(",", ";") + "+periodic:60" for m in (CA, FB, PR)}
KEY = {CA: "CAfee", FB: "CCfb", PR: "Prop"}
LAB = {CA: "Proposed, cost-aware (fixed)", FB: "Proposed, nominal fallback", PR: "Proportional buffer (tuned)"}
RTF = (1.6, 2.2)
MAC, REPORT = {}, []


def put(k, v):
    MAC["T" + k] = v


def mission(name: str) -> str:
    """Scenario name without the window suffix that tighten_windows appends in tier C."""
    return re.sub(r"-w[0-9.]+$", "", name)


def boot(d, n=10_000, seed=0):
    d = np.asarray(d, float)
    m = d[np.random.default_rng(seed).integers(0, d.size, size=(n, d.size))].mean(axis=1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi), float(min(2 * min(np.mean(m <= 0), np.mean(m >= 0)), 1.0))


def load(d: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(d.glob("gz-*.json")):
        m = json.loads(f.read_text())
        rows.append({"scenario": mission(m["scenario"]), "seed": int(m["seed"]), "profile": m["profile"],
                     "method": m["method"], "U": m["utility_rate"], "late": m["late_served"], "n": m["n_tasks"],
                     "rtf": m["rtf"], "ms": m["plan_ms_mean"], "ms95": m["plan_ms_p95"]})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["u1"] = df.U - df.late / df.n
    return df


def with_originals(df: pd.DataFrame, d: Path) -> pd.DataFrame:
    """Sensitivity: the original runs of repeated missions instead of their repeats."""
    if not (d / "invalid_rtf").exists():
        return df
    orig = load(d / "invalid_rtf")
    if orig.empty:
        return df
    keep = df.set_index(["scenario", "method"]).drop(orig.set_index(["scenario", "method"]).index, errors="ignore")
    return pd.concat([keep.reset_index(), orig], ignore_index=True)


def complete(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[(df.rtf >= RTF[0]) & (df.rtf <= RTF[1])]
    n = ok.groupby("scenario").method.nunique()
    return ok[ok.scenario.isin(n[n == 3].index)]


def paired(df, a, b, col):
    w = df.pivot_table(index="scenario", columns="method", values=col)
    if a not in w or b not in w:
        return pd.Series(dtype=float)
    return (w[a] - w[b]).dropna()


def fmt(m, lo, hi, scale=100, d=2):
    return f"{m * scale:+.{d}f} [{lo * scale:+.{d}f}, {hi * scale:+.{d}f}]".replace("-", "$-$")


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(C))
    ap.add_argument("--dev", action="store_true", help="report only (smoke flights)")
    a = ap.parse_args()
    d = Path(a.dir)
    raw = load(d)
    df = complete(raw)
    n = df.scenario.nunique()
    REPORT.extend([f"# Study 8c analysis ({'development' if a.dev else 'held-out'}): {n} complete missions, "
                   f"{len(raw)} flights in {d.name}", ""])
    put("NMissions", str(n))
    put("NFlights", str(len(df)))
    put("RtfMean", f"{df.rtf.mean():.2f}" if n else "nan")
    put("RtfMin", f"{df.rtf.min():.2f}" if n else "nan")
    n_rep = len(list((d / "invalid_rtf").glob("gz-*.json"))) if (d / "invalid_rtf").exists() else 0
    put("NRepeated", str(n_rep))
    if n == 0:
        print("\n".join(REPORT + ["no complete mission"]))
        return

    # ---------------------------------------------------------------- primary: fixed sequence H35 -> H36
    res = {}
    for name, col in (("HThirtyFive", "late"), ("HThirtySix", "u1")):
        x = paired(df, CA, FB, col)
        res[name] = boot(x) if len(x) > 1 else (float(x.mean()), np.nan, np.nan, np.nan)
    m35, lo35, hi35, p35 = res["HThirtyFive"]
    ok35 = bool(p35 < 0.05 and m35 < 0)
    m36, lo36, hi36, p36 = res["HThirtySix"]
    ok36 = bool(ok35 and p36 < 0.05 and m36 > 0)
    put("DHThirtyFive", fmt(m35, lo35, hi35, scale=1))
    put("DabsHThirtyFive", f"{abs(m35):.2f}")
    put("PHThirtyFive", pv(p35))
    put("OutHThirtyFive", "supported" if ok35 else "not supported")
    put("DHThirtySix", fmt(m36, lo36, hi36))
    put("DabsHThirtySix", f"{abs(m36) * 100:.2f}")
    put("PHThirtySix", pv(p36))
    put("OutHThirtySix", ("supported" if ok36 else "not supported") if ok35 else "not tested")
    REPORT.extend(["## Primary (fixed sequence, CAfee - CCfb)", "",
                   "| H | metric | diff [95% CI] | p | outcome |", "|---|---|---|---|---|",
                   f"| H35 | late arrivals per mission | {m35:+.3f} [{lo35:+.3f}, {hi35:+.3f}] | {p35:.4f} | "
                   f"{'supported' if ok35 else 'not supported'} |",
                   f"| H36 | u_1 (pp) | {m36 * 100:+.2f} [{lo36 * 100:+.2f}, {hi36 * 100:+.2f}] | {p36:.4f} | "
                   f"{('supported' if ok36 else 'not supported') if ok35 else 'not tested (H35 not supported)'} |", ""])

    # ---------------------------------------------------------------- secondary, tier B prediction
    bgz = None
    if BGZ.exists():
        bgz = pd.read_csv(BGZ)
        bgz = bgz.assign(scenario=bgz.scenario.map(mission), U=bgz.utility_rate, late=bgz.late_served,
                         u1=bgz.utility_rate - bgz.late_served / bgz.n_tasks)
        bgz = bgz[bgz.scenario.isin(set(df.scenario))]
    REPORT.extend(["## All comparisons: tier C and the tier B prediction on the same missions", "",
                   "| comparison | metric | tier C [95% CI] | p | tier B prediction [95% CI] |", "|---|---|---|---|---|"])
    rows = []
    for (x, y) in ((CA, FB), (CA, PR), (FB, PR)):
        for col, scale in (("late", 1), ("u1", 100), ("U", 100)):
            m, lo, hi, p = boot(paired(df, x, y, col))
            key = f"{KEY[x]}{KEY[y]}{col.capitalize()}"
            put(f"D{key}", fmt(m, lo, hi, scale, 2))
            put(f"P{key}", pv(p))
            pred = ""
            if bgz is not None:
                pb = paired(bgz, B_OF[x], B_OF[y], col)
                if len(pb) > 1:
                    mb, lob, hib, _ = boot(pb)
                    put(f"B{key}", fmt(mb, lob, hib, scale, 2))
                    pred = f"{mb * scale:+.2f} [{lob * scale:+.2f}, {hib * scale:+.2f}]"
                    rows.append((x, y, col, m, lo, hi, mb, lob, hib))
            REPORT.append(f"| {KEY[x]} - {KEY[y]} | {col} | {m * scale:+.2f} [{lo * scale:+.2f}, {hi * scale:+.2f}] | "
                          f"{p:.4f} | {pred} |")
    REPORT.append("")
    g = df.groupby("method").agg(U=("U", "mean"), u1=("u1", "mean"), late=("late", "mean"), ms=("ms", "mean"),
                                 ms95=("ms95", "mean"), rtf=("rtf", "mean"))
    REPORT.extend(["## Means (tier C)", "", "| method | U % | u_1 % | late | plan ms | p95 ms | RTF |",
                   "|---|---|---|---|---|---|---|"])
    for s in (CA, FB, PR):
        if s in g.index:
            r = g.loc[s]
            put(f"U{KEY[s]}", f"{r.U * 100:.2f}")
            put(f"Uone{KEY[s]}", f"{r.u1 * 100:.2f}")
            put(f"Late{KEY[s]}", f"{r.late:.2f}")
            put(f"Ms{KEY[s]}", f"{r.ms:.1f}")
            REPORT.append(f"| {KEY[s]} | {r.U * 100:.2f} | {r.u1 * 100:.2f} | {r.late:.2f} | {r.ms:.1f} | {r.ms95:.1f} | "
                          f"{r.rtf:.2f} |")
    REPORT.append("")
    if bgz is not None and not bgz.empty:
        gb = bgz.groupby("method").agg(U=("U", "mean"), u1=("u1", "mean"), late=("late", "mean"))
        for s in (CA, FB, PR):
            if B_OF[s] in gb.index:
                put(f"BU{KEY[s]}", f"{gb.loc[B_OF[s]].U * 100:.2f}")
                put(f"BUone{KEY[s]}", f"{gb.loc[B_OF[s]].u1 * 100:.2f}")
                put(f"BLate{KEY[s]}", f"{gb.loc[B_OF[s]].late:.2f}")
        mg = df.merge(bgz.assign(method=bgz.method.map({v: k for k, v in B_OF.items()})),
                      on=["scenario", "method"], suffixes=("", "_b"))
        for col in ("U", "u1", "late"):
            r = float(np.corrcoef(mg[col], mg[f"{col}_b"])[0, 1]) if len(mg) > 2 else float("nan")
            put(f"Corr{col.capitalize()}", f"{r:.2f}")
            REPORT.append(f"Per-run correlation tier B vs tier C ({col}): r = {r:.2f} (n = {len(mg)})")
        inside = sum(lob * 1 <= m <= hib * 1 for (_x, _y, _c, m, _lo, _hi, _mb, lob, hib) in rows)
        put("NInsidePred", str(inside))
        put("NPred", str(len(rows)))
        REPORT.append(f"Tier C means inside the tier B 95% interval: {inside} of {len(rows)}")
        REPORT.append("")

    # ---------------------------------------------------------------- RTF sensitivity
    alt = complete(with_originals(raw, d))
    if n_rep and alt.scenario.nunique() > 1:
        for name, col in (("HThirtyFive", "late"), ("HThirtySix", "u1")):
            m, lo, hi, p = boot(paired(alt, CA, FB, col))
            sc = 1 if col == "late" else 100
            put(f"Sens{name}", fmt(m, lo, hi, sc))
            REPORT.append(f"Sensitivity with the original runs, {name}: {m * sc:+.2f} [{lo * sc:+.2f}, {hi * sc:+.2f}], "
                          f"p {p:.4f}")
        REPORT.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("report_c_dev.md" if a.dev else "report_c.md")).write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    print("\n".join(REPORT))
    if a.dev:
        return
    table(g, bgz)
    lines = ["% generated by experiments/analyze_study8c.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s8c.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(g, bgz):
    gb = None
    if bgz is not None and not bgz.empty:
        gb = bgz.groupby("method").agg(U=("U", "mean"), u1=("u1", "mean"), late=("late", "mean"))
    lines = ["% generated by experiments/analyze_study8c.py -- do not edit", "\\begin{table}[t]",
             "\\caption{Study~8c, tier C (PX4 SITL, three X500), held-out seeds 17000--17019, high disturbances, halved "
             "windows: utility $U$, score $u_1$ (\\%) and late arrivals per mission, with the tier B prediction on the "
             "same missions.}\\label{tab:s8c}", "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{@{}lccc@{}}", "\\toprule", "Method & $U$ (\\%) & $u_1$ (\\%) & late \\\\", "\\midrule",
             "\\multicolumn{4}{@{}l}{tier C flights} \\\\"]
    for s in (CA, FB, PR):
        if s in g.index:
            r = g.loc[s]
            lines.append(f"{LAB[s]} & {r.U * 100:.2f} & {r.u1 * 100:.2f} & {r.late:.2f} \\\\")
    if gb is not None:
        lines += ["\\midrule", "\\multicolumn{4}{@{}l}{tier B, same missions} \\\\"]
        for s in (CA, FB, PR):
            if B_OF[s] in gb.index:
                r = gb.loc[B_OF[s]]
                lines.append(f"{LAB[s]} & {r.U * 100:.2f} & {r.u1 * 100:.2f} & {r.late:.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s8c.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
