"""Presentation copies of generated result tables for the IEEE manuscript (not frozen, presentation only).

The frozen analysis scripts write paper_journal/tables/tab_*.tex. This script copies selected tables to tabm_*.tex
with a short caption, the method names used in the text (LTCC, ...), a note under the table (threeparttable) and a few
exact text replacements (for example a corrected citation). Every number is copied unchanged; the script stops if an
expected string is not found.

Usage: python experiments/paper_tables_final.py
"""
from pathlib import Path

TAB = Path(__file__).resolve().parents[1] / "paper_journal" / "tables"
BUF = r"Constant buffer (60\,s)"

SPEC = {
    # ---------------- main text ----------------
    "tab_s4": {
        "caption": r"Study 4: utility (\%) per planning model and regime.",
        "replace": [
            ("Proposed planning model &", r"\mname{} &"),
            ("Proposed, online calibration &", r"\mname{}, online calibration &"),
            (r"Proportional buffer $c\,h$ &", "Proportional buffer &"),
            ("Constant 60 s buffer &", BUF + " &"),
            ("Conventional (event-only) &", "Conventional planner &"),
            ("it/ms", "Iter./ms"),
        ],
        "note": r"Regimes: disturbance level and time-window factor, averaged over the latency factors. Models with a "
                r"margin use the nominal fallback unless stated. Late: tasks served late per mission; Iter./ms: search "
                r"iterations per planning millisecond. 270 missions, search budget 40\,ms.",
    },
    "tab_s5": {
        "caption": r"Study 5: score $u_\lambda$ (\%) for a late cost of $\lambda$ task rewards.",
        "replace": [
            ("Cost-aware fallback (proposed) &", r"\mname{}, cost-aware fallback &"),
            ("Nominal fallback (study 4) &", r"\mname{}, nominal fallback &"),
            (r"Proportional buffer, tuned per $\lambda$ &", "Tuned proportional buffer &"),
            (r"No fallback, $z$ tuned per $\lambda$ &", r"\mname{}, no fallback, tuned safety factor &"),
            ("Moment propagation, fallback &", "Moment propagation, nominal fallback &"),
            ("Constant 60 s buffer &", BUF + " &"),
            ("Conventional (event-only) &", "Conventional planner &"),
        ],
        "note": r"$\lambda=0$ is the utility. The cost-aware fallback and the tuned competitors run with the late cost "
                r"of each column. Late: tasks served late per mission at $\lambda=1$. 270 missions.",
    },
    "tab_s6": {
        "caption": r"Study 6: score $u_\lambda$ (\%), late tasks and planning time.",
        "replace": [
            ("Proposed (ALNS, cost-aware fallback) &", r"\mname{}, cost-aware fallback &"),
            ("CBBA on the proposed model &", r"CBBA on \mname{} deadlines &"),
            ("CBBA, periodic &", "CBBA &"),
            ("CBBA, event-triggered &", "CBBA, event trigger only &"),
            ("Nominal model (ALNS) &", "Nominal model &"),
        ],
        "note": r"Methods with the cost-aware fallback run with $\lambda=1$ and are scored at every $\lambda$ from the "
                r"same runs. Late: tasks served late per mission; ms: planning time per call. 270 missions.",
    },
    # ---------------- supplementary material ----------------
    "tab_errmodels": {
        "caption": "Finish-time error models fitted on development missions.",
        "replace": [],
        "note": r"Mean $m(h)=b_0+b_1h$ and spread $s(h)=s_0+s_1h$, in seconds of the respective tier; $n$: executed "
                r"tasks.",
    },
    "tab_static_scale": {
        "caption": "Regret at equal computation per fleet scale.",
        "replace": [],
        "note": r"Fleet scale as UAVs/tasks. Baselines run for the mean time of AnytimeSwarm on the same scale; "
                r"$^{\dagger}$: 95\% interval of the paired difference below zero. Right: computation a baseline needs "
                r"to match AnytimeSwarm.",
    },
    "tab_main": {
        "caption": "Study 1: results of the tier B primary matrix.",
        "replace": [],
        "note": r"270 held-out missions in 16 configurations. Utility and lost tasks per mission, mean planning time per "
                r"call, and pooled paired difference of AnytimeSwarm-R minus each method (pp, 95\% bootstrap interval; "
                r"Holm-adjusted $p$ for the three primary comparisons).",
    },
    "tab_tierc": {
        "caption": "Study 1: software-in-the-loop results.",
        "replace": [],
        "note": r"30 held-out missions per method, mid disturbances, latency factor 50. Utility, tasks lost to late "
                r"plans and skipped at departure per mission, planning time per call, and tier B utility on the same "
                r"rescaled missions.",
    },
    "tab_s2_main": {
        "caption": "Study 2: tier B results of all methods.",
        "replace": [
            (r"\textbf{Proposed} &", r"\mname{}, no fallback &"),
            (r"Constant 60 s buffer~\cite{agra2013robust} &", BUF + r"~\cite{jabali2015selfimposed} &"),
            (r"\textit{Ablations of the proposed method}", r"Ablations of \mname{}"),
            ("Proposed, event-only trigger &", r"\mname{}, event trigger only &"),
            ("Proposed model, fixed 40 ms stop &", r"\mname{}, fixed 40\,ms &"),
            ("Proposed, mean correction only &", r"\mname{}, mean correction only &"),
            ("Proposed minus method (pp)", r"\mname{} minus method (pp)"),
            ("Conventional (40 ms, event-only) &", "Conventional planner &"),
        ],
        "note": r"270 missions in 12 configurations per method. Late: tasks served late; Lost: tasks lost because a "
                r"plan arrived too late; Calls: planning calls per mission. The last column gives \mname{} minus each "
                r"method, pooled over configurations (pp, 95\% paired bootstrap interval; Holm-adjusted $p$ for the six "
                r"primary comparisons, marked $^{\ast}$).",
    },
    "tab_s2_regime": {
        "caption": r"Study 2: utility (\%) per regime.",
        "replace": [],
        "note": r"Disturbance level, time-window factor and latency factor (10, 50, 200); tier B held-out missions.",
    },
    "tab_s2_tierc": {
        "caption": "Study 2: software-in-the-loop results.",
        "replace": [],
        "note": r"30 held-out missions per method, mid disturbances, latency factor 50. Utility, tasks served late, "
                r"tasks skipped at departure, planning calls and computation per call, and tier B utility on the same "
                r"rescaled missions.",
    },
    "tab_s3": {
        "caption": r"Study 3: utility (\%) per method and regime.",
        "replace": [
            (r"\textbf{Proposed with fallback} &", r"\mname{}, nominal fallback &"),
            ("Proposed (study 2) &", r"\mname{}, no fallback &"),
            ("Constant 60 s buffer &", BUF + " &"),
            ("Conventional (40 ms, event-only) &", "Conventional planner &"),
        ],
        "note": r"Regimes: disturbance level and time-window factor, averaged over the latency factors. Late: tasks "
                r"served late per mission. 270 missions, 12 configurations.",
    },
    "tab_cluster": {
        "caption": "Sensitivity of the tier B primary tests to the resampling unit.",
        "replace": [],
        "note": r"Mission: paired bootstrap over 270 missions, as in the primary analyses. Seed cluster: paired "
                r"bootstrap over the 30 seeds, each with its nine missions, which share the execution disturbances. "
                r"Differences in pp, 95\% intervals (90\% for the equivalence test H3), Holm-adjusted $p$ within each "
                r"primary family; for non-inferiority tests, $p$ is the one-sided $p$ with a margin of 0.5\,pp.",
    },
    "tab_s7": {
        "caption": r"Study 7b: utility $U$ / score $u_1$ (\%) under errors outside the model.",
        "replace": [
            ("Proposed, nominal fallback &", r"\mname{}, nominal fallback &"),
            ("Proposed, cost-aware (prop.) &", r"\mname{}, cost-aware, proportional rule &"),
            ("Proposed, cost-aware (fixed) &", r"\mname{}, cost-aware, fixed-cost rule &"),
            ("Constant 60 s buffer &", BUF + " &"),
        ],
        "note": r"Held-out seeds 14000--14029, high disturbances. The error model, the safety factor and every tuned "
                r"parameter are those of the calibrated level.",
    },
    "tab_s7const": {
        "caption": "Study 7a: fixed-cost rule under two definitions of the fixed cost.",
        "replace": [],
        "note": r"$u_\lambda$ charges a late arrival the realised mean reward $R/n$ of the mission, and "
                r"$u'_\lambda=U-\lambda\bar w\,n_{\mathrm{late}}/R$ charges exactly the cost $\lambda\bar w$ that the "
                r"rule assumes. Differences in pp with 95\% paired bootstrap intervals over 270 missions; $p$ for "
                r"$u'_\lambda$.",
    },
}


def convert(name, spec):
    src = (TAB / f"{name}.tex").read_text(encoding="utf-8")
    head, rest = src.split(r"\caption{", 1)
    depth, i = 1, 0
    while depth:                      # skip the original caption (balanced braces)
        depth += {"{": 1, "}": -1}.get(rest[i], 0)
        i += 1
    out = head + r"\caption{" + spec["caption"] + "}" + rest[i:]
    for old, new in spec["replace"]:
        if old not in out:
            raise SystemExit(f"{name}: text not found: {old}")
        out = out.replace(old, new, 1)
    note = ("\\begin{tablenotes}[flushleft]\\scriptsize\n\\item[] " + spec["note"] + "\n\\end{tablenotes}\n")
    if out.count("\\begin{tabular}") != 1:
        raise SystemExit(f"{name}: expected one tabular")
    out = out.replace("\\begin{tabular}", "\\begin{threeparttable}\n\\begin{tabular}", 1)
    out = out.replace("\\end{tabular}", "\\end{tabular}\n" + note + "\\end{threeparttable}", 1)
    banner = f"% generated by experiments/paper_tables_final.py from {name}.tex -- presentation copy, numbers unchanged\n"
    target = TAB / ("tabm_" + name[4:] + ".tex")
    target.write_text(banner + out, encoding="utf-8", newline="\n")
    print("wrote", target.name)


if __name__ == "__main__":
    for n, s in SPEC.items():
        convert(n, s)
