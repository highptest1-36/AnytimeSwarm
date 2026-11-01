"""Calibration of the predicted probability of meeting the deadline (reviewer audit, docs/15_PLAN_REVIEW_RESPONSE.md).

Every tier B run since study 4 bins its executed tasks by the probability Phi((d - f - m(h)) / s(h)) that the error
model of the disturbance level predicted at the last published plan (columns cov_n*, cov_k*, cov_p*: count, tasks on
time, sum of predicted probabilities per decile). From these bins this script computes, per study, method and level,
the expected calibration error ECE = sum_i |k_i - p_i| / N, the share on time against the mean prediction, and the same
for the upper tail (predicted probability >= 0.8), where a chance constraint acts. Study 7b runs (if present) add the
execution levels with errors outside the calibrated model, and their Brier score (columns brier_sum, brier_n).
Exploratory; no new runs.

    python experiments/paper_calib.py  ->  paper_journal/tables/numbers_calib.tex (macros \\val{V...}),
                                           paper_journal/figures/fig_calib.pdf, results/robust/report_calib.md
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TB, P, OUT = ROOT / "results" / "tier_b", ROOT / "paper_journal", ROOT / "results" / "robust"
T, A = "+periodic:60", "alns_fixed@40~"
CC, CA, NOM = A + "z=auto4;fb=nominal" + T, A + "z=auto4;lam=1" + T, "alns_fixed@40" + T
SHIFT = {"high_gauss": "Gaussian (calibrated)", "high_t3": "Student-$t$", "high_outlier": "Rare long delays",
         "high_uavbias": "Bias per UAV"}
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9.5, "xtick.labelsize": 8.5,
                     "ytick.labelsize": 8.5, "legend.fontsize": 8, "font.family": "serif", "mathtext.fontset": "stix",
                     "font.serif": ["STIXGeneral", "DejaVu Serif"]})


def bins(df):
    n = np.array([df[f"cov_n{i}"].sum() for i in range(10)], float)
    k = np.array([df[f"cov_k{i}"].sum() for i in range(10)], float)
    p = np.array([df[f"cov_p{i}"].sum() for i in range(10)], float)
    return n, k, p


def stats(df):
    n, k, p = bins(df)
    N = n.sum()
    hi = slice(8, 10)
    out = {"N": N, "ece": np.abs(k - p).sum() / N, "obs": k.sum() / N, "pred": p.sum() / N,
           "obs_hi": k[hi].sum() / max(n[hi].sum(), 1), "pred_hi": p[hi].sum() / max(n[hi].sum(), 1),
           "share_hi": n[hi].sum() / N}
    if "brier_sum" in df and df["brier_n"].sum() > 0:
        out["brier"] = df["brier_sum"].sum() / df["brier_n"].sum()
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {4: (TB / "s4_heldout_B.csv", CC), 5: (TB / "s5_heldout_B.csv", CA), 6: (TB / "s6_heldout_B.csv", CA)}
    rep = ["# Calibration of the predicted probability of meeting the deadline", "",
           "| study | method | level | tasks | ECE pp | on time % | predicted % | tail on time % | tail predicted % |"
           " tail share % | Brier |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    mac, curves = {}, {}

    def row(st, meth, lvl, s):
        rep.append(f"| {st} | {meth} | {lvl} | {s['N']:.0f} | {s['ece'] * 100:.2f} | {s['obs'] * 100:.1f} | "
                   f"{s['pred'] * 100:.1f} | {s['obs_hi'] * 100:.1f} | {s['pred_hi'] * 100:.1f} | "
                   f"{s['share_hi'] * 100:.1f} | {s.get('brier', float('nan')):.3f} |")

    eces = []
    for st, (f, m) in data.items():
        if not f.exists():
            continue
        df = pd.read_csv(f, usecols=lambda c: c.startswith("cov_") or c in ("method", "exec_level"))
        for meth, spec in (("proposed", m), ("nominal", NOM)):
            for lvl in ("mid", "high"):
                s = stats(df[(df.method == spec) & (df.exec_level == lvl)])
                row(st, meth, lvl, s)
                if meth == "proposed":
                    eces.append(s["ece"])
                    curves[(st, lvl)] = bins(df[(df.method == spec) & (df.exec_level == lvl)])
                    key = {4: "Four", 5: "Five", 6: "Six"}[st] + lvl.capitalize()
                    mac[f"VCalEce{key}"] = f"{s['ece'] * 100:.1f}"
                    mac[f"VCalObsHi{key}"] = f"{s['obs_hi'] * 100:.1f}"
                    mac[f"VCalPredHi{key}"] = f"{s['pred_hi'] * 100:.1f}"
    if eces:
        mac["VCalEceMin"], mac["VCalEceMax"] = f"{min(eces) * 100:.1f}", f"{max(eces) * 100:.1f}"

    shift_curves = {}
    f7 = [TB / "s7b_heldout_B.csv", TB / "s7b_lat_heldout_B.csv"]
    if all(f.exists() for f in f7):
        d7 = pd.concat([pd.read_csv(f) for f in f7], ignore_index=True)
        rep += ["", "## Study 7b: errors outside the calibrated model (proposed model, cost-aware fallback lam = 1)", ""]
        for lvl, lab in list(SHIFT.items()) + [("high_gauss|high_pareto", "Pareto latency")]:
            xl, _, ll = lvl.partition("|")
            sub = d7[(d7.method == CA) & (d7.exec_level == xl) & (d7.latency_level == (ll or "high"))]
            if sub.empty:
                continue
            s = stats(sub)
            row("7b", "proposed", lab, s)
            shift_curves[lab] = bins(sub)
            key = {"high_gauss": "Gauss", "high_t3": "Tthree", "high_outlier": "Outlier", "high_uavbias": "Bias"}[xl]
            key = "Pareto" if ll else key
            mac[f"VCalEceS{key}"] = f"{s['ece'] * 100:.1f}"
            mac[f"VCalBrierS{key}"] = f"{s['brier']:.3f}"
            mac[f"VCalObsHiS{key}"] = f"{s['obs_hi'] * 100:.1f}"
            mac[f"VCalPredHiS{key}"] = f"{s['pred_hi'] * 100:.1f}"

    (OUT / "report_calib.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    with open(P / "tables" / "numbers_calib.tex", "w", encoding="utf-8") as fh:
        fh.write("% generated by experiments/paper_calib.py -- do not edit\n")
        for k, v in sorted(mac.items()):
            fh.write(f"\\expandafter\\def\\csname v{k}\\endcsname{{{v}}}\n")

    ncol = 3 if shift_curves else 2
    fig, ax = plt.subplots(1, ncol, figsize=(7.16, 2.5), sharey=True)
    col = {4: "#1F6FC5", 5: "#C62828", 6: "#178A5E"}
    for i, lvl in enumerate(("mid", "high")):
        a = ax[i]
        for st in (4, 5, 6):
            if (st, lvl) not in curves:
                continue
            n, k, p = curves[(st, lvl)]
            ok = n >= 30
            a.plot(p[ok] / n[ok], k[ok] / n[ok], "o-", ms=3.5, lw=1.2, color=col[st], label=f"Study {st}")
        a.plot([0, 1], [0, 1], ":", color="black", lw=1)
        a.set_title(f"{lvl} disturbances")
        a.set_xlabel("predicted probability")
        a.set_xlim(0, 1)
        a.set_ylim(0, 1)
        a.grid(alpha=0.25, lw=0.5)
    ax[0].set_ylabel("share on time")
    ax[0].legend(loc="upper left", frameon=False)
    if shift_curves:
        a = ax[2]
        cs = ["#000000", "#D9622B", "#6A4BB5", "#0E7C86", "#B8337C"]
        for (lab, (n, k, p)), c in zip(shift_curves.items(), cs):
            ok = n >= 30
            a.plot(p[ok] / n[ok], k[ok] / n[ok], "o-", ms=3, lw=1.1, color=c, label=lab)
        a.plot([0, 1], [0, 1], ":", color="black", lw=1)
        a.set_title("study 7b, high, shifted errors")
        a.set_xlabel("predicted probability")
        a.set_xlim(0, 1)
        a.grid(alpha=0.25, lw=0.5)
        a.legend(loc="upper left", frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(P / "figures" / "fig_calib.pdf")


if __name__ == "__main__":
    main()
