"""Study 8 analysis (docs/18_PROTOCOL_V8.md): planning budget (8a) and the emergency-response scenario family (8b).

    python experiments/analyze_study8.py            # held-out (results/tier_b/s8a_heldout_B.csv, s8b_heldout_B.csv)
    python experiments/analyze_study8.py --dev      # development files (dev8a_check.csv, dev8b_check.csv), report only

Scores: U and u_1 = U - n_late / n. Statistics as in studies 2-7: per mission the paired difference is averaged over
the configurations, paired bootstrap over missions (10 000 resamples, seed 0), 95% percentile interval, two-sided p;
non-inferiority: one-sided share at or below -0.5 pp, superiority after non-inferiority. Holm within each family:
    8a (14 tests, u_1): H29_B CAprop - MPCA and H30_B CAfee - Prop for each budget B in {5, ..., 250} ms
    8b (4 tests): H31 CAfee - Forty (u_1), H32 CAfee - CCfb (u_1), H33 CAfee vs tuned Prop (u_1, NI),
                  H34 CCfb - Forty (U)
Secondary: means per method, budget, kappa and level; timing of the whole planning call; the smallest budget within
0.5 pp of the best; per profile; urgent tasks; calibration of the transferred error model; the same contrasts on the
conference family (study 7a held-out runs); seed-cluster bootstrap of every primary test.
Writes paper_journal/tables/numbers_s8.tex (macros \\val{S...}), tables/tab_s8a.tex, tab_s8b.tex and
results/study8/report.md. The figure is drawn by experiments/paper_s8fig.py (presentation only).
"""
import argparse
import sys
from pathlib import Path

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze_study2 import holm  # noqa: E402
from analyze_study4 import NI_MARGIN, noninf, paired, sup  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from journal_core.study7 import TUNED7  # noqa: E402

P, TB, OUT = ROOT / "paper_journal", ROOT / "results" / "tier_b", ROOT / "results" / "study8"
MAC, REPORT = {}, []
WRITE = {"tables": True}                    # False with --dev: development runs never write manuscript tables
T = "+periodic:60"
BUDGETS = {5: "Five", 10: "Ten", 20: "Twenty", 40: "Forty", 80: "Eighty", 160: "OneSixty", 250: "TwoFifty"}
OPT_A = {"CAfee": "~z=auto4;lam=1;cost=fee", "CAprop": "~z=auto4;lam=1", "MPCA": "~mp=auto;lam=1",
         "Prop": "~prop=0.45;fb=none", "Nom": ""}
LAB_A = {"CAfee": "Proposed, cost-aware (fixed)", "CAprop": "Proposed, cost-aware (prop.)",
         "MPCA": "Moment propagation, cost-aware", "Prop": "Proportional buffer (tuned)", "Nom": "Nominal model"}
COL = {"CAfee": "#C62828", "CAprop": "#EF8A62", "MPCA": "#1F6FC5", "Prop": "#2E7D32", "Nom": "0.45"}
A40 = "alns_fixed@40"
M8B = {"Forty": A40 + T, "CCfb": A40 + "~z=auto4;fb=nominal" + T, "CAfee": A40 + "~z=auto4;lam=1;cost=fee" + T,
       "CAprop": A40 + "~z=auto4;lam=1" + T, "MPCA": A40 + "~mp=auto;lam=1" + T, "Prop": "Prop@fee1", "CCnf": "CCnf@fee1"}
LAB_B = {"Forty": "Nominal model", "CCfb": "Proposed, nominal fallback", "CAfee": "Proposed, cost-aware (fixed)",
         "CAprop": "Proposed, cost-aware (prop.)", "MPCA": "Moment propagation, cost-aware",
         "Prop": "Proportional buffer (tuned)", "CCnf": "Proposed, no fallback (tuned $z$)"}
PROFILES = {"incidents": "Incidents", "attrition": "Attrition", "priorities": "Priorities"}
N_BOOT = 10_000


def put(k, v):
    MAC["S" + k] = v


def spec_a(key, B):
    return f"alns_fixed@{B}{OPT_A[key]}{T}"


def scores(df):
    return df.assign(U=df.utility_rate, u1=df.utility_rate - df.late_served / df.n_tasks)


def tuned(df, fam):
    """Rows of the member selected for u_1 at lam = 1 (TUNED7) per disturbance level, renamed <fam>@fee1."""
    parts = [df[(df.exec_level == lvl) & (df.method == A40 + "~" + o + T)]
             for lvl, o in TUNED7["fee"][1.0][fam].items() if lvl in set(df.exec_level)]
    if not parts or any(p.empty for p in parts):
        return df.iloc[:0]
    return pd.concat(parts).assign(method=f"{fam}@fee1")


def pp(x):
    return f"{x * 100:.2f}"


def num(name, m, lo, hi):
    put(f"D{name}", f"{m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}]".replace("-", "$-$"))
    put(f"Dabs{name}", f"{abs(m) * 100:.2f}")
    put(f"CI{name}", f"{lo * 100:.2f} to {hi * 100:.2f}".replace("-", "$-$"))


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def seed_of(scenario: str) -> int:
    return int(scenario.split("-")[2])


def cluster(d: pd.Series, kind: str, n=N_BOOT, seed=0):
    """Seed-cluster bootstrap of the mean of d (index: scenario): interval and p as sup / noninf."""
    g = pd.DataFrame({"x": d.values, "s": [seed_of(s) for s in d.index]}).groupby("s").x.agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    idx = np.random.default_rng(seed).integers(0, len(s), size=(n, len(s)))
    b = s[idx].sum(axis=1) / c[idx].sum(axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    p = float(np.mean(b <= -NI_MARGIN)) if kind == "ni" else float(min(2 * min(np.mean(b <= 0), np.mean(b >= 0)), 1.0))
    return float(lo), float(hi), p


def outcome(kind, m, p_adj, p_sup=None):
    if kind == "ni":
        if p_adj >= 0.05:
            return "not supported"
        return "supported, sup." if (p_sup is not None and p_sup < 0.05 and m > 0) else "supported (NI)"
    if p_adj >= 0.05:
        return "no significant difference"
    return "first better" if m > 0 else "second better"


def family(tests, label):
    """tests: list of (name, kind, frame, a, b, metric). Holm over the family; mission and seed-cluster bootstrap."""
    res = []
    for name, kind, x, a, b, metric in tests:
        if a not in set(x.method) or b not in set(x.method):
            continue
        d = paired(x, a, b, metric)
        r = sup(d) if kind == "sup" else noninf(d)
        res.append((name, kind, d) + r)
    if not res:
        return [], 0
    adj = holm(np.array([r[6] for r in res]))
    cl = [cluster(r[2], r[1]) for r in res]
    adj_c = holm(np.array([c[2] for c in cl]))
    out, changed = [], 0
    REPORT.extend([f"## {label}", "", "| H | test | diff pp [95% CI] | p | p Holm | outcome | seed-cluster CI | "
                   "p Holm (cluster) | outcome (cluster) |", "|---|---|---|---|---|---|---|---|---|"])
    for (name, kind, d, m, lo, hi, p), pa, c, pc in zip(res, adj, cl, adj_c):
        p_sup = sup(d)[3] if kind == "ni" else None
        o = outcome(kind, m, pa, p_sup)
        oc = outcome(kind, m, pc, sup(d)[3] if kind == "ni" else None)
        changed += o != oc
        num(name, m, lo, hi)
        put(f"P{name}", pv(pa))
        put(f"Out{name}", o)
        if kind == "ni":
            put(f"PSup{name}", pv(p_sup))
        REPORT.append(f"| {name} | {kind} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] | {p:.4f} | {pa:.4f} | "
                      f"{o} | [{c[0] * 100:+.2f}, {c[1] * 100:+.2f}] | {pc:.4f} | {oc} |")
        out.append((name, kind, m, lo, hi, p, pa, o))
    REPORT.append("")
    REPORT.append(f"Seed-cluster bootstrap changed {changed} of {len(res)} outcomes.")
    REPORT.append("")
    return out, changed


# ---------------------------------------------------------------------------------------------- 8a
def study8a(df):
    df = scores(df)
    df = df.assign(budget=df.method.str.extract(r"alns_fixed@(\d+)")[0].astype(int))
    put("ANRuns", f"{len(df):,}".replace(",", "\\,"))
    put("ANMissions", str(df.scenario.nunique()))
    budgets = [B for B in BUDGETS if B in set(df.budget)]
    tests = []
    for B in budgets:
        tests.append((f"HTwentyNineAt{BUDGETS[B]}", "sup", df, spec_a("CAprop", B), spec_a("MPCA", B), "u1"))
        tests.append((f"HThirtyAt{BUDGETS[B]}", "sup", df, spec_a("CAfee", B), spec_a("Prop", B), "u1"))
    res, changed = family(tests, "8a primary family (Holm over the budgets x 2): H29_B CAprop - MPCA, H30_B CAfee - "
                                 "Prop, u_1")
    put("AClusterChanged", str(changed))
    put("ANTests", str(len(res)))
    for key in ("HTwentyNineAt", "HThirtyAt"):
        r = [x for x in res if x[0].startswith(key)]
        for o in ("first better", "second better", "no significant difference"):
            put(f"ACount{key}{o.split()[0].capitalize()}", str(sum(x[7] == o for x in r)))
    g = df.groupby(["method"]).agg(U=("U", "mean"), u1=("u1", "mean"), call=("call_ms_mean", "mean"),
                                   p99=("call_ms_p99", "mean"), mx=("call_ms_max", "max"),
                                   model=("model_ms_mean", "mean"), over=("over_ms_mean", "mean"),
                                   itms=("iters_per_search_ms", "mean"), late=("late_served", "mean"))
    gk = df.groupby(["method", "kappa"]).u1.mean()
    rows = []
    for k in OPT_A:
        best_b, best = None, -np.inf
        for B in budgets:
            s = spec_a(k, B)
            if s not in g.index:
                continue
            r = g.loc[s]
            n = BUDGETS[B]
            put(f"AUone{k}{n}", pp(r.u1))
            put(f"AU{k}{n}", pp(r.U))
            put(f"ACall{k}{n}", f"{r.call:.1f}")
            put(f"ACallP{k}{n}", f"{r.p99:.1f}")
            put(f"AModel{k}{n}", f"{r.model:.2f}")
            put(f"AOver{k}{n}", f"{r.over:.2f}")
            put(f"AItms{k}{n}", f"{r.itms:.1f}")
            for kap in (10, 50, 200):
                if (s, kap) in gk.index:
                    put(f"AUone{k}{n}K{kap}", pp(gk.loc[(s, kap)]))
            rows.append((k, B, r))
            if r.u1 > best:
                best_b, best = B, r.u1
        if best_b is not None:
            within = min(B for B in budgets if spec_a(k, B) in g.index and g.loc[spec_a(k, B)].u1 >= best - 0.005)
            put(f"ABest{k}", str(best_b))
            put(f"AWithin{k}", str(within))
            vals = [g.loc[spec_a(k, B)].u1 for B in budgets if spec_a(k, B) in g.index]
            put(f"ARange{k}", pp(max(vals) - min(vals)))
    if budgets:
        put("ASmallest", str(budgets[0]))
        put("ALargest", str(budgets[-1]))
    REPORT.extend(["## 8a means per method and budget", "",
                   "| method | B ms | U % | u_1 % | late | call ms | p99 ms | max ms | model ms | over ms | it/ms |",
                   "|---|---|---|---|---|---|---|---|---|---|---|"])
    for k, B, r in rows:
        REPORT.append(f"| {k} | {B} | {r.U * 100:.2f} | {r.u1 * 100:.2f} | {r.late:.2f} | {r.call:.2f} | {r.p99:.2f} | "
                      f"{r.mx:.1f} | {r.model:.2f} | {r.over:.2f} | {r.itms:.1f} |")
    REPORT.append("")
    REPORT.extend(["## 8a mean u_1 per kappa", "", "| method | B | kappa 10 | kappa 50 | kappa 200 |", "|---|---|---|---|---|"])
    for k in OPT_A:
        for B in budgets:
            s = spec_a(k, B)
            REPORT.append(f"| {k} | {B} | " + " | ".join(f"{gk.loc[(s, kap)] * 100:.2f}" if (s, kap) in gk.index
                                                          else "-" for kap in (10, 50, 200)) + " |")
    REPORT.append("")
    table_a(g, budgets)
    return df, budgets, res


def table_a(g, budgets):
    if not WRITE["tables"]:
        return
    cols = "".join("c" for _ in budgets)
    head = " & ".join(str(B) for B in budgets)
    lines = ["% generated by experiments/analyze_study8.py -- do not edit", "\\begin{table*}[t]",
             "\\caption{Study~8a, tier B, held-out seeds 15000--15029, high disturbances: score $u_1$ (\\%) and whole "
             "planning call (mean / 99th percentile per mission, ms) for ALNS budgets $B$ of 5 to 250~ms. The "
             "publication delay charges the whole call, including the construction of the planning model.}"
             "\\label{tab:s8a}", "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             f"\\begin{{tabular}}{{@{{}}l{cols}@{{}}}}", "\\toprule", f"$B$ (ms) & {head} \\\\", "\\midrule",
             f"\\multicolumn{{{len(budgets) + 1}}}{{@{{}}l}}{{score $u_1$ (\\%)}} \\\\"]
    for k in OPT_A:
        vals = [pp(g.loc[spec_a(k, B)].u1) if spec_a(k, B) in g.index else "--" for B in budgets]
        lines.append(f"{LAB_A[k]} & " + " & ".join(vals) + " \\\\")
    lines += ["\\midrule", f"\\multicolumn{{{len(budgets) + 1}}}{{@{{}}l}}{{whole planning call, mean / 99th "
                           "percentile (ms)}} \\\\"]
    for k in OPT_A:
        vals = [f"{g.loc[spec_a(k, B)].call:.1f} / {g.loc[spec_a(k, B)].p99:.1f}" if spec_a(k, B) in g.index else "--"
                for B in budgets]
        lines.append(f"{LAB_A[k]} & " + " & ".join(vals) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (P / "tables" / "tab_s8a.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------- 8b
def with_tuned(df):
    df = scores(df)
    return pd.concat([df, tuned(df, "Prop"), tuned(df, "CCnf")], ignore_index=True)


def calib(df):
    n = np.array([df[f"cov_n{i}"].sum() for i in range(10)], float)
    k = np.array([df[f"cov_k{i}"].sum() for i in range(10)], float)
    p = np.array([df[f"cov_p{i}"].sum() for i in range(10)], float)
    N = n.sum()
    if N == 0:
        return None
    return {"ece": np.abs(k - p).sum() / N, "obs_hi": k[8:].sum() / max(n[8:].sum(), 1),
            "pred_hi": p[8:].sum() / max(n[8:].sum(), 1), "obs": k.sum() / N, "pred": p.sum() / N}


def study8b(df, conf):
    df = with_tuned(df)
    put("BNRuns", f"{len(df[~df.method.str.contains('@fee1')]):,}".replace(",", "\\,"))
    put("BNMissions", str(df.scenario.nunique()))
    tests = [("HThirtyOne", "sup", df, M8B["CAfee"], M8B["Forty"], "u1"),
             ("HThirtyTwo", "sup", df, M8B["CAfee"], M8B["CCfb"], "u1"),
             ("HThirtyThree", "ni", df, M8B["CAfee"], M8B["Prop"], "u1"),
             ("HThirtyFour", "sup", df, M8B["CCfb"], M8B["Forty"], "U")]
    res, changed = family(tests, "8b primary family (Holm over four): H31 CAfee - Forty (u_1), H32 CAfee - CCfb "
                                 "(u_1), H33 CAfee vs tuned Prop (u_1, NI), H34 CCfb - Forty (U)")
    put("BClusterChanged", str(changed))
    # secondary contrasts and the same contrasts on the conference family (study 7a held-out runs)
    contrasts = [("CAfeeForty", "CAfee", "Forty", "u1"), ("CAfeeCCfb", "CAfee", "CCfb", "u1"),
                 ("CAfeeProp", "CAfee", "Prop", "u1"), ("CCfbForty", "CCfb", "Forty", "U"),
                 ("CAfeeCCnf", "CAfee", "CCnf", "u1"), ("MPCACAprop", "MPCA", "CAprop", "u1"),
                 ("CAfeeCAprop", "CAfee", "CAprop", "u1"), ("CAfeeFortyU", "CAfee", "Forty", "U")]
    fam_rows = []
    for name, a, b, metric in contrasts:
        for tag, x in (("", df), ("Conf", conf)):
            if x is None or M8B[a] not in set(x.method) or M8B[b] not in set(x.method):
                continue
            m, lo, hi, _ = sup(paired(x, M8B[a], M8B[b], metric))
            num(f"B{tag}{name}", m, lo, hi)
            fam_rows.append((name, tag or "new", m, lo, hi))
        for prof, pn in PROFILES.items():
            x = df[df.profile == prof]
            if M8B[a] in set(x.method) and M8B[b] in set(x.method):
                m, lo, hi, _ = sup(paired(x, M8B[a], M8B[b], metric))
                num(f"B{name}{pn}", m, lo, hi)
        for lvl in ("mid", "high"):
            x = df[df.exec_level == lvl]
            if M8B[a] in set(x.method) and M8B[b] in set(x.method):
                m, lo, hi, _ = sup(paired(x, M8B[a], M8B[b], metric))
                num(f"B{name}{lvl.capitalize()}", m, lo, hi)
    REPORT.extend(["## 8b contrasts: new family vs conference family (study 7a)", "",
                   "| contrast | family | diff pp [95% CI] |", "|---|---|---|"])
    for name, fam, m, lo, hi in fam_rows:
        REPORT.append(f"| {name} | {fam} | {m * 100:+.2f} [{lo * 100:+.2f}, {hi * 100:+.2f}] |")
    REPORT.append("")
    g = df.groupby(["method", "exec_level"]).agg(U=("U", "mean"), u1=("u1", "mean"), late=("late_served", "mean"))
    ga = df.groupby("method").agg(U=("U", "mean"), u1=("u1", "mean"), late=("late_served", "mean"),
                                  urg=("urgent_on_time", "sum"), nurg=("n_urgent", "sum"),
                                  call=("call_ms_mean", "mean"), model=("model_ms_mean", "mean"))
    REPORT.extend(["## 8b means", "", "| method | U mid | u_1 mid | U high | u_1 high | U | u_1 | late | urgent on time % | "
                   "call ms | model ms |", "|---|---|---|---|---|---|---|---|---|---|---|"])
    for k, s in M8B.items():
        if s not in ga.index:
            continue
        r = ga.loc[s]
        cells = []
        for lvl in ("mid", "high"):
            if (s, lvl) in g.index:
                put(f"BU{k}{lvl.capitalize()}", pp(g.loc[(s, lvl)].U))
                put(f"BUone{k}{lvl.capitalize()}", pp(g.loc[(s, lvl)].u1))
                cells += [pp(g.loc[(s, lvl)].U), pp(g.loc[(s, lvl)].u1)]
            else:
                cells += ["-", "-"]
        put(f"BU{k}", pp(r.U))
        put(f"BUone{k}", pp(r.u1))
        put(f"BLate{k}", f"{r.late:.2f}")
        urg = r.urg / r.nurg if r.nurg > 0 else float("nan")
        put(f"BUrg{k}", f"{urg * 100:.1f}")
        REPORT.append(f"| {k} | " + " | ".join(cells) + f" | {pp(r.U)} | {pp(r.u1)} | {r.late:.2f} | {urg * 100:.1f} | "
                      f"{r.call:.1f} | {r.model:.2f} |")
    REPORT.append("")
    # calibration of the transferred error model (proposed model with the cost-aware fallback, as in paper_calib)
    REPORT.extend(["## 8b calibration of the transferred error model (CAfee runs)", "",
                   "| family | level | ECE pp | on time % | predicted % | tail on time % | tail predicted % |",
                   "|---|---|---|---|---|---|---|"])
    for tag, x in (("", df), ("Conf", conf)):
        if x is None:
            continue
        for lvl in ("mid", "high"):
            c = calib(x[(x.method == M8B["CAfee"]) & (x.exec_level == lvl)])
            if c is None:
                continue
            L = lvl.capitalize()
            put(f"B{tag}Ece{L}", f"{c['ece'] * 100:.1f}")
            put(f"B{tag}TailObs{L}", f"{c['obs_hi'] * 100:.1f}")
            put(f"B{tag}TailPred{L}", f"{c['pred_hi'] * 100:.1f}")
            put(f"B{tag}Obs{L}", f"{c['obs'] * 100:.1f}")
            put(f"B{tag}Pred{L}", f"{c['pred'] * 100:.1f}")
            REPORT.append(f"| {'conference' if tag else 'new'} | {lvl} | {c['ece'] * 100:.1f} | {c['obs'] * 100:.1f} | "
                          f"{c['pred'] * 100:.1f} | {c['obs_hi'] * 100:.1f} | {c['pred_hi'] * 100:.1f} |")
    REPORT.append("")
    table_b(g)
    return df, fam_rows


def table_b(g):
    if not WRITE["tables"]:
        return
    lines =["% generated by experiments/analyze_study8.py -- do not edit", "\\begin{table}[t]",
             "\\caption{Study~8b, tier B, emergency-response family, held-out seeds 16000--16029: utility $U$ / score "
             "$u_1$ (\\%) per disturbance level. Every model and tuned parameter is transferred from the conference "
             "family without re-tuning.}\\label{tab:s8b}", "\\centering\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{@{}lcc@{}}", "\\toprule", "Method & Mid & High \\\\", "\\midrule"]
    for k, s in M8B.items():
        cells = [f"{pp(g.loc[(s, lvl)].U)} / {pp(g.loc[(s, lvl)].u1)}" if (s, lvl) in g.index else "--"
                 for lvl in ("mid", "high")]
        lines.append(f"{LAB_B[k]} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (P / "tables" / "tab_s8b.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    WRITE["tables"] = not a.dev
    fa, fb = ("dev8a_check.csv", "dev8b_check.csv") if a.dev else ("s8a_heldout_B.csv", "s8b_heldout_B.csv")
    dfa = pd.read_csv(TB / fa)
    dfb = pd.read_csv(TB / fb)
    conf = with_tuned(pd.read_csv(TB / "s7a_heldout_B.csv")) if (TB / "s7a_heldout_B.csv").exists() else None
    REPORT.extend([f"# Study 8 analysis ({'development' if a.dev else 'held-out'})", "",
                   f"Files: {fa}, {fb}; NI margin {NI_MARGIN * 100:.1f} pp.", ""])
    study8a(dfa)
    study8b(dfb, conf)
    put("NIMargin", f"{NI_MARGIN * 100:.1f}")
    OUT.mkdir(parents=True, exist_ok=True)
    name = "report_dev.md" if a.dev else "report.md"
    (OUT / name).write_text("\n".join(REPORT) + "\n", encoding="utf-8")
    if a.dev:
        print("\n".join(REPORT))
        return
    lines = ["% generated by experiments/analyze_study8.py -- do not edit"]
    lines += [f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}" for k, v in sorted(MAC.items())]
    (P / "tables" / "numbers_s8.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(REPORT))


if __name__ == "__main__":
    main()
