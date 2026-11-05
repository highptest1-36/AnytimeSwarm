#!/usr/bin/env python3
"""Final data figures of the manuscript in one consistent style (presentation only; no statistic is new).

Every figure is drawn from the same result files and with the same bootstrap functions (seed 0) as the scripts that
produced it before (paper_errstructure.py, paper_s4c.py, analyze_study5.py, analyze_study6.py, paper_s7fig.py,
paper_demo.py, ...). The frozen analysis modules are only imported, never modified. Macro files (numbers_*.tex) are
not written here.

    ~/venvs/atswarm/bin/python experiments/paper_figs_final.py             # all figures
    ~/venvs/atswarm/bin/python experiments/paper_figs_final.py s5 s7       # selected figures

Style: Times-like serif (STIX), upright text, 8 pt labels, Okabe-Ito colours with one colour and marker per method in
every figure, legends outside the data, panel labels (a), (b) at the top left, figure widths at print size (IEEE Access
column 85.29 mm = 3.36 in, text 177.53 mm = 6.99 in).
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT))
FIG = ROOT / "paper_journal" / "figures"
TB = ROOT / "results" / "tier_b"

W1, W2 = 3.36, 6.99          # column and text width (in)
LAM = "λ"                # upright Greek lambda in plain text
MINUS = "−"

RC = {
    "font.family": "serif", "font.serif": ["STIXGeneral", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix", "mathtext.default": "regular",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 7.5, "legend.title_fontsize": 7.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.direction": "out", "ytick.direction": "out",
    "lines.linewidth": 1.3, "lines.markersize": 4.5, "errorbar.capsize": 1.8,
    "axes.grid": True, "grid.color": "0.88", "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "legend.handlelength": 1.8, "legend.handletextpad": 0.4,
    "legend.columnspacing": 1.0, "legend.borderaxespad": 0.2, "legend.labelspacing": 0.3,
    "text.color": "black", "axes.labelcolor": "black", "xtick.color": "black", "ytick.color": "black",
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "savefig.dpi": 600,
}


def style():
    """(Re)apply the style: some analysis modules change rcParams when they are imported."""
    plt.rcParams.update(RC)


style()

# one colour and one marker per method in every figure (Okabe-Ito palette, colour-blind safe)
METHOD = {
    "ca":     ("LTCC, cost-aware fallback", "#D55E00", "o"),
    "fb":     ("LTCC, nominal fallback", "#0072B2", "s"),
    "nofb":   ("LTCC, no fallback", "#56B4E9", "v"),
    "prop":   ("Proportional buffer", "#E69F00", "D"),
    "mp":     ("Moment propagation", "#CC79A7", "^"),
    "cbba":   ("CBBA", "#009E73", "P"),
    "nom":    ("Nominal model", "#3C3C3C", "X"),
    "buf":    ("Constant buffer", "#9A9A9A", "h"),
    "conv":   ("Conventional planner", "#000000", "*"),
    "propru": ("proportional rule", "#882255", "s"),     # study 7a: cost-aware fallback with the proportional rule
}
TIER = {
    "dev": ("Tier B, development seeds", "#A8A8A8", "D"),
    "b":   ("Tier B (kinematic)", "#1A1A1A", "s"),
    "c":   ("Tier C (PX4 SITL)", "#0072B2", "o"),
}
LEVEL = {"mid": ("mid disturbances", "#0072B2", "o"), "high": ("high disturbances", "#D55E00", "s")}


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)
    print("wrote", FIG / f"{name}.pdf")


def panel(ax, tag, x=-0.02):
    """Plain upright panel label at the top left, outside the data area."""
    ax.text(x, 1.02, f"({tag})", transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5)


def ebar(ax, x, m, lo, hi, color, marker, horizontal=False, line=False, label=None, ms=4.5, fill=True, **kw):
    """Point estimate with a 95% interval; m, lo, hi in percentage points."""
    m, lo, hi = (np.atleast_1d(np.asarray(v, float)) for v in (m, lo, hi))
    err = [m - lo, hi - m]
    fmt = marker + ("-" if line else "")
    style = dict(fmt=fmt, color=color, ms=ms, mec=color, mfc=color if fill else "white", mew=0.8,
                 elinewidth=0.9, capsize=1.8, capthick=0.9, lw=1.2, label=label, zorder=3)
    style.update(kw)
    if horizontal:
        return ax.errorbar(m, x, xerr=err, **style)
    return ax.errorbar(x, m, yerr=err, **style)


def _fig_y(fig, axes, which="y0"):
    """Lowest (y0) or highest (y1) edge of the axes including tick and axis labels, in figure coordinates."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bbs = [a.get_tightbbox(r) for a in np.atleast_1d(axes).ravel()]
    y = min(b.y0 for b in bbs) if which == "y0" else max(b.y1 for b in bbs)
    return fig.transFigure.inverted().transform((0, y))[1]


def legend_below(fig, axes, hs, labs, ncol, gap=0.02, **kw):
    """Figure legend centred under all axes and their labels, so it can never cover data or labels."""
    return fig.legend(hs, labs, loc="upper center", bbox_to_anchor=(0.5, _fig_y(fig, axes) - gap), ncol=ncol, **kw)


def legend_under(ax, hs, labs, ncol=1, gap=0.03, **kw):
    """Axes legend centred under one axes and its labels."""
    fig = ax.figure
    fig.canvas.draw()
    bb = ax.get_tightbbox(fig.canvas.get_renderer())
    y = (bb.y0 - ax.bbox.y0) / ax.bbox.height - gap
    return ax.legend(hs, labs, loc="upper center", bbox_to_anchor=(0.5, y), ncol=ncol, **kw)


def zero(ax, horizontal=False):
    (ax.axvline if horizontal else ax.axhline)(0, color="black", lw=0.7, zorder=1)


def handle(color, marker, line=False, fill=True):
    return Line2D([], [], color=color, marker=marker, ls="-" if line else "", lw=1.2, ms=4.5, mec=color,
                  mfc=color if fill else "white", mew=0.8)


# ---------------------------------------------------------------------------------------------------------------
# Fig. 2: structure of the finish-time error (development missions)
# ---------------------------------------------------------------------------------------------------------------
def fig_errstructure():
    js = json.loads((TB / "dev4_errstructure.json").read_text())
    bins = pd.read_csv(TB / "dev4_errbins.csv")
    legs = pd.read_csv(TB / "dev4_legs.csv")
    mp = json.loads((ROOT / "models" / "mp_model_dev.json").read_text())
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.25), gridspec_kw={"wspace": 0.22})
    fig.subplots_adjust(left=0.075, right=0.995, top=0.93, bottom=0.17)
    for lv, (lab, col, mk) in LEVEL.items():
        b = bins[bins.level == lv]
        h = np.linspace(b.h_mean.min(), b.h_mean.max(), 100)
        a0, a1 = js[lv]["affine"]["theta"][2:]
        q0, q1 = js[lv]["sqrt"]["theta"][2:]
        ax[0].plot(h, a0 + a1 * h, "-", color=col, lw=1.3, zorder=2)
        ax[0].plot(h, np.sqrt(q0 + q1 * h), "--", color=col, lw=1.1, zorder=2)
        ax[0].plot(b.h_mean, b.sd_emp, mk, ms=4.5, color=col, mec="white", mew=0.5, zorder=3)
        g = legs[(legs.level == lv) & (legs.t_nom > 1.0)]
        q = pd.qcut(g.t_nom, 10)
        m = mp[lv]
        res = g.t_act - (1 + m["a"]) * g.t_nom - m["c"]
        sd = res.groupby(q, observed=True).std()
        tm = g.t_nom.groupby(q, observed=True).mean()
        t = np.linspace(0, tm.max(), 50)
        ax[1].plot(t, m["cv"] * t, "-", color=col, lw=1.3, zorder=2)
        ax[1].plot(tm, sd, mk, ms=4.5, color=col, mec="white", mew=0.5, zorder=3)
    ax[0].set_xlabel("lead time (s)")
    ax[0].set_ylabel("SD of finish-time error (s)")
    ax[1].set_xlabel("nominal flight time of a leg (s)")
    ax[1].set_ylabel("SD of flight-time error (s)")
    for a, tag in zip(ax, "ab"):
        a.set_ylim(bottom=0)
        panel(a, tag)
    ax[1].set_xlim(left=0)
    hs = [handle(LEVEL[k][1], LEVEL[k][2]) for k in LEVEL]
    hs += [Line2D([], [], color="0.35", lw=1.3), Line2D([], [], color="0.35", lw=1.1, ls="--"),
           Line2D([], [], color="0.35", lw=1.3)]
    labs = [LEVEL[k][0] for k in LEVEL] + ["affine fit (a)", "independent-increment fit (a)",
                                           "proportional fit (b)"]
    legend_below(fig, ax, hs, labs, ncol=5)
    save(fig, "fig_errstructure")


# ---------------------------------------------------------------------------------------------------------------
# Fig. 5: study 4C, tier C against its tier B counterpart
# ---------------------------------------------------------------------------------------------------------------
def fig_s4c():
    from analyze_study4c import B_OF, BGZ, FB, NOFB, NOM, C, boot, load, paired

    def tier_b(csv, window=0.5):
        b = pd.read_csv(csv)
        b = b[b.window == window]
        b = b.assign(method=b.method.map({v: k for k, v in B_OF.items()})).dropna(subset=["method"])
        return b.pivot_table(index="scenario", columns="method", values="utility_rate")

    df = load(C)
    complete = df.groupby("scenario").method.nunique()
    df = df[df.scenario.isin(complete[complete == 3].index)]
    df = df.assign(scenario=df.scenario.str.replace(r"-w0\.5$", "", regex=True))
    wb = tier_b(BGZ).loc[sorted(df.scenario.unique())]
    dev = tier_b(TB / "dev4c_gz.csv")
    tests = [(NOM, f"minus nominal model\n(H14)"), (NOFB, "minus LTCC, no fallback\n(H15)")]
    fig, ax = plt.subplots(figsize=(W1, 2.45))
    out = {}
    for i, (s, _) in enumerate(tests):
        for dx, key, d in [(-0.22, "dev", dev[FB] - dev[s]), (0.0, "b", wb[FB] - wb[s]),
                           (0.22, "c", paired(df, FB, s))]:
            m, lo, hi, _ = boot(d)
            lab, col, mk = TIER[key]
            ebar(ax, i + dx, 100 * m, 100 * lo, 100 * hi, col, mk, ms=5)
            out[(i, key)] = round(100 * m, 2)
    zero(ax)
    ax.set_xticks(range(len(tests)), [t[1] for t in tests])
    for t in ax.get_xticklabels():
        t.set_linespacing(1.05)
    ax.set_xlim(-0.55, len(tests) - 0.45)
    ax.set_ylabel(f"LTCC, nominal fallback {MINUS} method (pp)")
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
    ax.grid(axis="x", visible=False)
    ax.legend([handle(TIER[k][1], TIER[k][2]) for k in TIER], [TIER[k][0] for k in TIER], loc="lower left",
              bbox_to_anchor=(0.0, 1.02), ncol=2)
    print("fig_s4c means (pp):", out)
    save(fig, "fig_s4c")


# ---------------------------------------------------------------------------------------------------------------
# Fig. 6: study 5, cost-aware fallback against competitors at every late cost
# ---------------------------------------------------------------------------------------------------------------
def fig_s5():
    import analyze_study5 as a5
    from analyze_study4 import paired, sup
    df = pd.read_csv(TB / "s5_heldout_B.csv")
    df = pd.concat([df] + [a5.tuned(df, f, lam) for lam in a5.LAMS for f in ("Prop", "CCnf")], ignore_index=True)
    have = set(df.method)
    series = [("CCfb", "fb", "LTCC, nominal fallback"),
              ("Prop", "prop", "tuned proportional buffer"),
              ("CCnf", "nofb", "LTCC, no fallback, tuned per late cost"),
              ("MP", "mp", "Moment propagation, nominal fallback")]
    fig, ax = plt.subplots(figsize=(W1, 2.95))
    xs = np.log2(list(a5.LAMS))
    out = {}
    for i, (name, key, lab) in enumerate(series):
        rows = []
        for lam in a5.LAMS:
            b = f"{name}@{lam:g}" if name in ("Prop", "CCnf") else a5.M[name]
            if b not in have or a5.ca(lam) not in have:
                continue
            m, lo, hi, _ = sup(paired(a5.scored(df, lam), a5.ca(lam), b, "u"))
            rows.append((lam, 100 * m, 100 * lo, 100 * hi))
        r = np.array(rows)
        _, col, mk = METHOD[key]
        ebar(ax, np.log2(r[:, 0]) + (i - 1.5) * 0.045, r[:, 1], r[:, 2], r[:, 3], col, mk, line=True, label=lab)
        out[name] = [round(v, 2) for v in r[:, 1]]
    zero(ax)
    ax.set_xticks(xs, [f"{lam:g}" for lam in a5.LAMS])
    ax.set_xlim(xs[0] - 0.3, xs[-1] + 0.3)
    ax.set_xlabel(f"late cost {LAM} (mean task rewards)")
    ax.set_ylabel("score difference (pp)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=1, title=f"LTCC, cost-aware fallback {MINUS}",
              alignment="left")
    print("fig_s5 means (pp):", out)
    save(fig, "fig_s5")


# ---------------------------------------------------------------------------------------------------------------
# Fig. 7: study 6, CBBA and moment propagation
# ---------------------------------------------------------------------------------------------------------------
def fig_s6():
    import analyze_study6 as a6
    from analyze_study4 import paired, sup
    df = pd.read_csv(TB / "s6_heldout_B.csv")
    df = df[df.method.isin(a6.M.values())]
    panels = [
        [("CA", "CBBA", "ca", f"(a) LTCC, cost-aware fallback {MINUS} CBBA"),
         ("CBBACA", "CBBA", "cbba", f"(a) CBBA on LTCC deadlines {MINUS} CBBA")],
        [("MPCA", "MP", "fb", f"(b) Moment propagation: cost-aware {MINUS} nominal fallback"),
         ("MPCA", "MPnf", "nofb", f"(b) Moment propagation: cost-aware {MINUS} no fallback")],
    ]
    fig, axes = plt.subplots(1, 2, figsize=(W1, 2.2), gridspec_kw={"wspace": 0.38})
    lams = list(a6.LAMS)
    out = {}
    hs, labs = [], []
    for ax, tag, ser in zip(axes, "ab", panels):
        for i, (a, b, key, lab) in enumerate(ser):
            rows = [sup(paired(a6.scored(df, lam), a6.M[a], a6.M[b], "u"))[:3] for lam in lams]
            r = 100 * np.array(rows)
            _, col, mk = METHOD[key]
            ebar(ax, np.arange(len(lams)) + (i - 0.5) * 0.12, r[:, 0], r[:, 1], r[:, 2], col, mk, line=True)
            hs.append(handle(col, mk, line=True))
            labs.append(lab)
            out[f"{a}-{b}"] = [round(v, 2) for v in r[:, 0]]
        zero(ax)
        ax.set_xticks(range(len(lams)), [f"{lam:g}" for lam in lams])
        ax.set_xlim(-0.4, len(lams) - 0.6)
        ax.set_xlabel(f"late cost {LAM}")
        panel(ax, tag)
    axes[0].set_ylabel("score difference (pp)")
    legend_below(fig, axes, hs, labs, ncol=1)
    print("fig_s6 means (pp):", out)
    save(fig, "fig_s6")


# ---------------------------------------------------------------------------------------------------------------
# Fig. 8: study 7, late-cost model (7a) and errors outside the model (7b)
# ---------------------------------------------------------------------------------------------------------------
def fig_s7():
    import analyze_study7 as a7
    from analyze_study4 import paired, sup
    s7 = pd.read_csv(a7.TB / "s7a_heldout_B.csv")
    b = pd.concat([pd.read_csv(a7.TB / f) for f in ("s7b_heldout_B.csv", "s7b_lat_heldout_B.csv")], ignore_index=True)
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.6), gridspec_kw={"width_ratios": [1.0, 1.3], "wspace": 0.36})
    fig.subplots_adjust(left=0.16, right=0.995, top=0.93, bottom=0.2)
    out = {}

    a = ax[0]
    rules = [("fee", "ca", "fixed-cost rule"), ("prop", "propru", "proportional rule")]
    ticks, labels, groups, y = [], [], [], 0.0
    for kind, gname in (("fee", "fixed late cost"), ("w", "late cost proportional\nto task reward")):
        g0 = y
        for lam in (0.5, 1.0, 2.0):
            x = a7.score(s7, lam, kind)
            x = pd.concat([x, a7.tuned(x, kind, lam, "Prop")], ignore_index=True)
            for k, (rule, key, _) in enumerate(rules):
                m, lo, hi, _ = sup(paired(x, a7.ca(lam, rule), f"Prop@{kind}{lam:g}", "u"))
                _, col, mk = METHOD[key]
                ebar(a, y + 0.28 * (k - 0.5), 100 * m, 100 * lo, 100 * hi, col, mk, horizontal=True, ms=4)
                out[(kind, lam, rule)] = round(100 * m, 2)
            ticks.append(y)
            labels.append(f"{LAM} = {lam:g}")
            y += 1.0
        groups.append(((g0 + y - 1.0) / 2, gname))
        y += 0.6
    zero(a, horizontal=True)
    a.set_yticks(ticks, labels)
    a.set_ylim(y - 0.5, -0.6)
    a.grid(axis="y", visible=False)
    a.set_xlabel(f"cost-aware fallback {MINUS} tuned proportional buffer (pp)")
    for yc, gname in groups:
        a.text(-0.30, yc, gname, transform=a.get_yaxis_transform(), rotation=90, ha="center", va="center",
               fontsize=7.5, linespacing=1.0)
    a.axhline(ticks[2] + 0.8, color="0.75", lw=0.6)
    panel(a, "a", x=-0.30)

    c = ax[1]
    conds = [a7.CONTROL] + a7.SHIFTS
    comps = [(a7.M7B["CCfb"], a7.M7B["Forty"], "U", "nom", f"LTCC, nominal fallback {MINUS} nominal model, utility"),
             (a7.M7B["CA"], a7.M7B["CCfb"], "u1", "fb",
              f"LTCC, cost-aware {MINUS} nominal fallback, score at {LAM} = 1")]
    for k, (ma, mb, metric, key, lab) in enumerate(comps):
        for j, (xl, ll, _, _) in enumerate(conds):
            sub = b[(b.exec_level == xl) & (b.latency_level == ll)]
            x = a7.score(sub, 1.0, "fee") if metric == "u1" else sub.assign(u=sub.utility_rate)
            m, lo, hi, _ = sup(paired(x, ma, mb, "u"))
            _, col, mk = METHOD[key]
            ebar(c, j + (k - 0.5) * 0.26, 100 * m, 100 * lo, 100 * hi, col, mk, ms=4.5)
            out[(metric, xl, ll)] = round(100 * m, 2)
    c.axvspan(-0.5, 0.5, color="0.93", zorder=0, lw=0)
    c.axvline(0.5, color="0.75", lw=0.6)
    c.set_xlim(-0.5, len(conds) - 0.5)
    c.set_ylim(0, 8.0)
    c.set_xticks(range(len(conds)), ["Gaussian\n(control)", "Student-t\nerrors", "rare long\ndelays",
                                     "speed bias\nper UAV", "Pareto\nlatency"])
    for t in c.get_xticklabels():
        t.set_linespacing(1.05)
    c.grid(axis="x", visible=False)
    c.set_ylabel("difference (pp)")
    panel(c, "b")
    legend_under(a, [handle(METHOD[k][1], METHOD[k][2]) for _, k, _ in rules], [r[2] for r in rules], ncol=2)
    legend_under(c, [handle(METHOD[k[3]][1], METHOD[k[3]][2]) for k in comps], [k[4] for k in comps], ncol=1)
    print("fig_s7 means (pp):", out)
    save(fig, "fig_s7")


# ---------------------------------------------------------------------------------------------------------------
# Fig. 4: illustrative tier C flights (development seed 1)
# ---------------------------------------------------------------------------------------------------------------
DEMO = ROOT / "results" / "tier_c" / "demo"
UAV_COL = ["#0072B2", "#E69F00", "#CC79A7"]
STATUS = {"on time": ("served on time", "#009E73"), "late": ("served late", "#D55E00"),
          "not served": ("not served", "#B0B0B0")}


def _tracks(tag):
    from pyulog import ULog
    sys.path.insert(0, str(ROOT / "journal_ros"))
    from common import spawn_xy
    out = {}
    for f in sorted((DEMO / "ulog" / tag).glob("uav*_*.ulg")):
        k = int(f.name[3:f.name.index("_")]) - 1
        lp = ULog(str(f), ["vehicle_local_position"]).get_dataset("vehicle_local_position").data
        sx, sy = spawn_xy(k, 3)
        out.setdefault(k, []).append(np.c_[sx + lp["y"], sy + lp["x"]])   # NED -> ENU
    return {k: np.vstack(v) for k, v in out.items()}


def _arrows(ax, xy, color, every=140.0):
    """Small arrowheads along a flown track, one per `every` metres of path, to show the direction of flight."""
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    keep = np.r_[True, np.diff(d) > 0]
    d, xy = d[keep], xy[keep]

    def at(s):
        return np.array([np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])])

    for s in np.arange(every / 2, d[-1] - 10, every):
        p0, p1 = at(s - 6.0), at(s + 6.0)
        if np.hypot(*(p1 - p0)) < 8.0:          # hovering or turning: no clear direction here
            continue
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>,head_length=0.55,head_width=0.28",
                                                          color=color, lw=1.0, shrinkA=0, shrinkB=0), zorder=3)


def fig_demo_tracks():
    sys.path.insert(0, str(ROOT / "journal_ros"))
    from common import gz_scenario, map_to_gz
    from journal_core.study2 import tighten_windows
    sc = tighten_windows(gz_scenario("arrivals", 1), 0.5)
    task_xy = {t.id: map_to_gz(t.x, t.y, sc.depot) for t in sc.tasks}
    runs = [("proposed", "LTCC, nominal fallback"), ("nominal", "Nominal model")]
    fig, axes = plt.subplots(1, 2, figsize=(5.0, 2.95), sharex=True, sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, tag_name, tag in zip(axes, runs, "cd"):          # (a), (b) are the Gazebo images of the same figure
        run, title = tag_name
        res = json.loads((DEMO / f"{run}.json").read_text())
        served = {int(j) for j in res["_served"]}
        late = {int(j) for j in res["_late"]}
        for k, xy in _tracks(run).items():
            ax.plot(xy[:, 0], xy[:, 1], color=UAV_COL[k], lw=1.2, zorder=2, solid_capstyle="round")
            _arrows(ax, xy, UAV_COL[k])
        for j, (x, y) in task_xy.items():
            st = "on time" if j in served else "late" if j in late else "not served"
            ax.scatter(x, y, s=34, marker="o", facecolor=STATUS[st][1], edgecolor="white", lw=0.7, zorder=4)
        ax.scatter(0, 0, s=40, marker="s", color="black", zorder=5)
        ax.set_aspect("equal")
        ax.set_xlabel("east (m)")
        ax.set_title(f"({tag}) {title}\nutility {100 * res['utility_rate']:.1f}%, {res['late_served']} late",
                     loc="left", fontsize=8, linespacing=1.15)
    axes[0].set_ylabel("north (m)")
    hs = [Line2D([], [], color=c, lw=1.4) for c in UAV_COL]
    hs += [Line2D([], [], marker="o", ls="", mfc=c, mec="white", ms=6) for _, c in STATUS.values()]
    hs += [Line2D([], [], marker="s", ls="", color="black", ms=5)]
    labs = ["UAV 1", "UAV 2", "UAV 3"] + [f"task {v[0]}" for v in STATUS.values()] + ["depot"]
    order = [0, 3, 1, 4, 2, 5, 6]                   # column-wise fill: UAVs in row 1, task states in row 2
    legend_below(fig, axes, [hs[i] for i in order], [labs[i] for i in order], ncol=4, columnspacing=1.2)
    save(fig, "fig_demo_tracks")


def _levels(img, lo, hi, gamma=1.0, sat=1.0):
    """Linear levels stretch [lo, hi] -> [0, 1] with gamma and a saturation boost (img in [0, 1], RGB)."""
    x = np.clip((img - lo) / (hi - lo), 0, 1) ** gamma
    g = x.mean(axis=2, keepdims=True)
    return np.clip(g + sat * (x - g), 0, 1)


def _blobs(img, test, min_px=20):
    from scipy import ndimage
    lab, n = ndimage.label(test(img))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) >= min_px:
            out.append((xs.mean(), ys.mean(), len(xs)))
    return out


def fig_demo_gazebo():
    a = plt.imread(DEMO / "selected" / "closeup_proposed.png")[..., :3].astype(float)
    b = plt.imread(DEMO / "selected" / "overview_nominal.png")[..., :3].astype(float)
    ha, wa = a.shape[:2]
    hb, wb = b.shape[:2]
    a = a[int(0.13 * ha):int(0.70 * ha), int(0.20 * wa):int(0.80 * wa)]
    b = b[int(0.22 * hb):int(0.74 * hb), int(0.0 * wb):int(1.0 * wb)]
    red = _blobs(b, lambda im: (im[..., 0] > 0.6) & (im[..., 1] < 0.35) & (im[..., 2] < 0.35))
    green = _blobs(b, lambda im: (im[..., 1] > 0.55) & (im[..., 0] < 0.45) & (im[..., 2] < 0.5))
    grey = _blobs(b, lambda im: (im.max(axis=2) < 0.52) & (np.ptp(im, axis=2) < 0.06), min_px=40)
    drone = _blobs(a, lambda im: im.max(axis=2) < 0.25, min_px=200)
    a, b = _levels(a, 0.45, 0.93, gamma=1.15, sat=1.25), _levels(b, 0.45, 0.93, gamma=1.15, sat=1.25)
    ra, rb = a.shape[1] / a.shape[0], b.shape[1] / b.shape[0]
    fig, ax = plt.subplots(1, 2, figsize=(W2, W2 / (ra + rb) * 1.0 + 0.1),
                           gridspec_kw={"width_ratios": [ra, rb], "wspace": 0.03})
    for x, img in ((ax[0], a), (ax[1], b)):
        x.imshow(img, interpolation="lanczos")
        x.set_xticks([])
        x.set_yticks([])
        x.grid(False)
        for s in x.spines.values():
            s.set_visible(True)
            s.set_linewidth(0.6)
            s.set_color("0.4")
    box = dict(boxstyle="square,pad=0.25", fc="white", ec="none", alpha=0.9)
    arrow = dict(arrowstyle="-|>,head_length=0.5,head_width=0.25", color="black", lw=0.8, shrinkA=1, shrinkB=4)
    for x, tag in ((ax[0], "a"), (ax[1], "b")):
        x.text(0.015, 0.97, f"({tag})", transform=x.transAxes, ha="left", va="top", fontsize=8.5, bbox=box)
    if drone:
        dx, dy, _ = max(drone, key=lambda t: t[2])
        ax[0].annotate("PX4 X500", xy=(dx + 25, dy - 10), xytext=(dx + 0.22 * a.shape[1], dy - 0.12 * a.shape[0]),
                       fontsize=8, ha="left", va="center", bbox=box, arrowprops=arrow)
    ax[0].annotate("task served on time", xy=(0.47 * a.shape[1], 0.94 * a.shape[0]),
                   xytext=(0.04 * a.shape[1], 0.74 * a.shape[0]), fontsize=8, ha="left", va="center", bbox=box,
                   arrowprops=arrow)
    H, W = b.shape[:2]
    if red:
        rx, ry, _ = max(red, key=lambda t: t[2])
        ax[1].annotate("served late", xy=(rx, ry - 8), xytext=(rx + 0.03 * W, ry - 0.30 * H), fontsize=8, ha="left",
                       va="center", bbox=box, arrowprops=arrow)
    if green:
        gx, gy, _ = max(green, key=lambda t: t[2])
        ax[1].annotate("served on time", xy=(gx + 10, gy - 10), xytext=(gx + 0.10 * W, gy - 0.22 * H), fontsize=8,
                       ha="left", va="center", bbox=box, arrowprops=arrow)
    if grey:
        cand = [g for g in grey if 0.45 * W < g[0] < 0.97 * W and g[1] > 0.3 * H]
        if cand:
            sx, sy, _ = max(cand, key=lambda t: t[0])
            ax[1].annotate("not served", xy=(sx - 6, sy + 6), xytext=(sx - 0.20 * W, sy + 0.28 * H), fontsize=8,
                           ha="left", va="center", bbox=box, arrowprops=arrow)
    save(fig, "fig_demo_gazebo")
    print("blobs: red", [(round(x), round(y)) for x, y, _ in red], "green", len(green), "grey",
          [(round(x), round(y)) for x, y, _ in grey], "drone", [(round(x), round(y)) for x, y, _ in drone])


# ===============================================================================================================
# Supplementary figures
# ===============================================================================================================
OTHER = {"fix250": ("ALNS, fixed 250 ms", "#8C564B", "p"), "as": ("AnytimeSwarm", "#8C564B", "p"),
         "asr": ("AnytimeSwarm-R", "#3C3C3C", "o")}
REG4 = [("mid", 1.0), ("mid", 0.5), ("high", 1.0), ("high", 0.5)]


def _regime_ticks(ax):
    ax.set_xticks(range(len(REG4)), [f"{xl} disturbances,\nwindows ×{wf:g}" for xl, wf in REG4])
    for t in ax.get_xticklabels():
        t.set_linespacing(1.05)
    ax.grid(axis="x", visible=False)


def _dodge_regimes(ax, rows, minuend_label, fname, width=0.8):
    """rows: list of (key, label, [(m, lo, hi) per regime]) in pp; colours from METHOD."""
    n = len(rows)
    w = width / n
    hs, labs = [], []
    for j, (key, lab, est) in enumerate(rows):
        _, col, mk = METHOD[key] if key in METHOD else OTHER[key]
        for i, (m, lo, hi) in enumerate(est):
            ebar(ax, i + (j - (n - 1) / 2) * w, m, lo, hi, col, mk)
        hs.append(handle(col, mk))
        labs.append(lab)
    zero(ax)
    _regime_ticks(ax)
    ax.set_xlim(-0.5, len(REG4) - 0.5)
    ax.set_ylabel(f"{minuend_label} {MINUS} method (pp)")
    return hs, labs


def fig_s4_regimes():
    """Supplementary: study 4 per regime, and the reliability of the error model (fig_coverage)."""
    import analyze_study4 as a4
    cap = {}
    a4.table = lambda *a, **k: None
    a4.figure = lambda df, present: cap.update(df=df, present=present)
    a4.figure_coverage = lambda cov: cap.update(cov=cov)
    a4.analyse(pd.read_csv(TB / "s4_heldout_B.csv"))
    df, present, cov = cap["df"], cap["present"], cap["cov"]
    rows = []
    for k, key, lab in [("PropBuf", "prop", "Proportional buffer"), ("MP", "mp", "Moment propagation, nominal fallback"),
                        ("Buf", "buf", "Constant buffer"), ("Forty", "nom", "Nominal model"),
                        ("Conv", "conv", "Conventional planner")]:
        if k not in present:
            continue
        est = []
        for xl, wf in REG4:
            m, lo, hi, _ = a4.sup(a4.paired(a4.regime(df, xl, wf), a4.M["CC"][0], a4.M[k][0]))
            est.append((100 * m, 100 * lo, 100 * hi))
        rows.append((key, lab, est))
    print("fig_s4 means (pp):", {r[0]: [round(e[0], 2) for e in r[2]] for r in rows})
    fig, ax = plt.subplots(figsize=(6.0, 2.5))
    hs, labs = _dodge_regimes(ax, rows, "LTCC, nominal fallback", "fig_s4")
    legend_below(fig, ax, hs, labs, ncol=3)
    save(fig, "fig_s4")

    fig, axes = plt.subplots(1, 2, figsize=(5.6, 2.6), sharey=True, gridspec_kw={"wspace": 0.12})
    for a, xl, tag in zip(axes, ["mid", "high"], "ab"):
        a.plot([0, 1], [0, 1], color="0.45", lw=0.8, ls=":", zorder=1)
        for k, key, lab in [("CC", "fb", "LTCC, nominal fallback"), ("Forty", "nom", "Nominal model")]:
            if (k, xl) not in cov:
                continue
            pr, ob, n = cov[(k, xl)]
            s = n >= 20
            _, col, mk = METHOD[key]
            a.plot(pr[s], ob[s], mk + "-", color=col, ms=4, lw=1.2, mec=col, zorder=3)
        a.set_xlim(0, 1)
        a.set_ylim(0, 1.02)
        a.set_xlabel("predicted probability of meeting the deadline")
        a.text(-0.02, 1.02, f"({tag}) {xl} disturbances", transform=a.transAxes, ha="left", va="bottom",
               fontsize=8.5)
    axes[0].set_ylabel("observed share on time")
    hs = [handle(METHOD[k][1], METHOD[k][2], line=True) for k in ("fb", "nom")]
    hs.append(Line2D([], [], color="0.45", lw=0.8, ls=":"))
    legend_below(fig, axes, hs, ["LTCC, nominal fallback", "Nominal model", "perfect calibration"], ncol=3)
    save(fig, "fig_coverage")


def fig_s3_regimes():
    import analyze_study3 as a3
    from analyze_study2 import boot
    df = pd.read_csv(TB / "s3_heldout_B.csv")
    M = a3.methods("proposed~fb=nominal+periodic:60")
    rows = []
    for k, key, lab in [("Prop", "nofb", "LTCC, no fallback (study 2)"), ("Buf", "buf", "Constant buffer"),
                        ("Forty", "nom", "Nominal model"), ("Conv", "conv", "Conventional planner")]:
        est = []
        for xl, wf in REG4:
            m, lo, hi, _ = boot(a3.paired(a3.regime(df, xl, wf), M["FB"][0], M[k][0]), n=4000)
            est.append((100 * m, 100 * lo, 100 * hi))
        rows.append((key, lab, est))
    print("fig_s3 means (pp):", {r[0]: [round(e[0], 2) for e in r[2]] for r in rows})
    fig, ax = plt.subplots(figsize=(6.0, 2.5))
    hs, labs = _dodge_regimes(ax, rows, "LTCC, nominal fallback", "fig_s3")
    legend_below(fig, ax, hs, labs, ncol=4)
    save(fig, "fig_s3")


def fig_replication():
    import re
    tab = ROOT / "paper_journal" / "tables"
    q = {}
    for f in ("numbers_s2.tex", "numbers_s3.tex", "numbers_s4.tex"):
        q.update(re.findall(r"\\csname v(\w+)\\endcsname\{([^}]*)\}", (tab / f).read_text(encoding="utf-8")))

    def parse(v):
        return tuple(float(x) for x in re.fullmatch(r"(\S+) \[(.+), (.+)\]", v.replace("$-$", "-")).groups())

    comps = [("Constant buffer", ("KDBuf", "LDBufAll", "QDBufAll")),
             ("Nominal model", ("KDForty", "LDFortyAll", "QDFortyAll")),
             ("Conventional planner", ("KDConv", "LDConvAll", "QDCCConv"))]
    studies = [("study 2 (LTCC, no fallback)", "#56B4E9", "v"), ("study 3 (LTCC, nominal fallback)", "#0072B2", "s"),
               ("study 4 (LTCC, nominal fallback)", "#0072B2", "D")]
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ticks = []
    for i, (lab, keys) in enumerate(comps):
        for j, (k, (_, col, mk)) in enumerate(zip(keys, studies)):
            m, lo, hi = parse(q[k])
            ebar(ax, i + (j - 1) * 0.24, m, lo, hi, col, mk, horizontal=True, fill=(j != 2))
        ticks.append((i, f"minus {lab[0].lower() + lab[1:]}"))
    zero(ax, horizontal=True)
    ax.set_yticks([t for t, _ in ticks], [lab for _, lab in ticks])
    ax.set_ylim(len(comps) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(left=-0.5)
    ax.set_xlabel("utility difference (pp)")
    legend_below(fig, ax, [handle(c, mk, fill=(j != 2)) for j, (_, c, mk) in enumerate(studies)],
                 [s[0] for s in studies], ncol=1)
    save(fig, "fig_replication")


def fig_latepen():
    import paper_latepen as pl
    from analyze_study2 import boot
    from analyze_study4c import C, load
    data = {"3": pl.load_b("s3_heldout_B.csv", pl.S3), "4": pl.load_b("s4_heldout_B.csv", pl.S4)}
    c = load(C)
    ntask = {f"{j['scenario']}|{j['method']}": j["n_tasks"]
             for j in (json.loads(f.read_text()) for f in sorted(C.glob("gz-*.json")))}
    c["n_tasks"] = [ntask[f"{s}|{m}"] for s, m in zip(c.scenario, c.method)]
    comp = {k: (st, a, b) for k, st, a, b, _ in pl.COMP}
    series = [("SThreeFbProp", "nofb", f"LTCC: nominal fallback {MINUS} no fallback (study 3)"),
              ("SFourMPMPnf", "mp", f"Moment propagation: nominal fallback {MINUS} no fallback (study 4)"),
              ("SFourCCForty", "nom", f"LTCC, nominal fallback {MINUS} nominal model (study 4)"),
              ("SFourCCBuf", "buf", f"LTCC, nominal fallback {MINUS} constant buffer (study 4)")]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    hs = []
    out = {}
    for i, (name, key, lab) in enumerate(series):
        st, a, b = comp[name]
        rows = []
        for lam in pl.LAMBDAS:
            d = pl.diff_c(c, a, b, lam) if st == "C" else pl.diff_b(data[st], a, b, lam)
            m, lo, hi, _ = boot(d)
            rows.append((lam, 100 * m, 100 * lo, 100 * hi))
        r = np.array(rows)
        _, col, mk = METHOD[key]
        ebar(ax, r[:, 0] + (i - 1.5) * 0.025, r[:, 1], r[:, 2], r[:, 3], col, mk, line=True, ms=4)
        hs.append(handle(col, mk, line=True))
        out[name] = [round(v, 2) for v in r[:, 1]]
    zero(ax)
    ax.set_xticks(pl.LAMBDAS, [f"{v:g}" for v in pl.LAMBDAS])
    ax.set_xlabel(f"late cost {LAM} (mean task rewards)")
    ax.set_ylabel("score difference (pp)")
    legend_below(fig, ax, hs, [s[2] for s in series], ncol=1)
    print("fig_latepen means (pp):", out)
    save(fig, "fig_latepen")


def fig_calib():
    import paper_calib as pc
    data = {4: (TB / "s4_heldout_B.csv", pc.CC), 5: (TB / "s5_heldout_B.csv", pc.CA), 6: (TB / "s6_heldout_B.csv", pc.CA)}
    curves = {}
    for st, (f, m) in data.items():
        df = pd.read_csv(f, usecols=lambda c: c.startswith("cov_") or c in ("method", "exec_level"))
        for lvl in ("mid", "high"):
            curves[(st, lvl)] = pc.bins(df[(df.method == m) & (df.exec_level == lvl)])
    d7 = pd.concat([pd.read_csv(TB / f) for f in ("s7b_heldout_B.csv", "s7b_lat_heldout_B.csv")], ignore_index=True)
    shifts = [("high_gauss", "high", "Gaussian (control)", "#000000", "o"),
              ("high_t3", "high", "Student-t errors", "#E69F00", "s"),
              ("high_outlier", "high", "rare long delays", "#D55E00", "D"),
              ("high_uavbias", "high", "speed bias per UAV", "#CC79A7", "^"),
              ("high_gauss", "high_pareto", "Pareto latency", "#56B4E9", "v")]
    st_style = {4: ("study 4 (LTCC, nominal fallback)", "#0072B2", "s"),
                5: ("study 5 (LTCC, cost-aware fallback)", "#D55E00", "o"),
                6: ("study 6 (LTCC, cost-aware fallback)", "#009E73", "^")}
    fig, ax = plt.subplots(1, 3, figsize=(W2, 2.55), sharey=True, gridspec_kw={"wspace": 0.1})
    for a, lvl, tag in ((ax[0], "mid", "a"), (ax[1], "high", "b")):
        for st, (lab, col, mk) in st_style.items():
            n, k, p = curves[(st, lvl)]
            ok = n >= 30
            a.plot(p[ok] / n[ok], k[ok] / n[ok], mk + "-", ms=3.5, lw=1.1, color=col, mec=col, zorder=3)
        a.text(-0.02, 1.02, f"({tag}) {lvl} disturbances", transform=a.transAxes, ha="left", va="bottom", fontsize=8.5)
    for xl, ll, lab, col, mk in shifts:
        sub = d7[(d7.method == pc.CA) & (d7.exec_level == xl) & (d7.latency_level == ll)]
        n, k, p = pc.bins(sub)
        ok = n >= 30
        ax[2].plot(p[ok] / n[ok], k[ok] / n[ok], mk + "-", ms=3.2, lw=1.0, color=col, mec=col, zorder=3)
    ax[2].text(-0.02, 1.02, "(c) study 7b, high disturbances", transform=ax[2].transAxes, ha="left", va="bottom",
               fontsize=8.5)
    for a in ax:
        a.plot([0, 1], [0, 1], ":", color="0.45", lw=0.8, zorder=1)
        a.set_xlim(0, 1)
        a.set_ylim(0, 1.02)
        a.set_xlabel("predicted probability")
    ax[0].set_ylabel("observed share on time")
    fig.canvas.draw()
    legend_under(ax[0], [handle(c, m, line=True) for _, c, m in st_style.values()], [v[0] for v in st_style.values()],
                 ncol=1, gap=0.05)
    legend_under(ax[1], [Line2D([], [], color="0.45", lw=0.8, ls=":")], ["perfect calibration"], ncol=1, gap=0.05)
    legend_under(ax[2], [handle(s[3], s[4], line=True) for s in shifts], [s[2] for s in shifts], ncol=2, gap=0.05)
    save(fig, "fig_calib")


def _study2():
    import analyze_study2 as a2
    cap = {}
    a2.table_main = lambda *a, **k: None
    a2.table_regime = lambda *a, **k: None
    a2.fig_main = lambda df, g, tests: cap.update(g=g, tests=tests)
    a2.fig_regime = lambda df: None
    cap["df"] = a2.tier_b()
    return a2, cap


S2_NAME = {"Prop": "LTCC, no fallback", "Rep": "Regret-2 repair (no search)", "Fix": "ALNS, fixed 250 ms",
           "Forty": "ALNS, fixed 40 ms", "Scaled": "ALNS, size-scaled budget", "Stag": "ALNS, stagnation stop",
           "Prof": "Performance profile", "Onl": "Online performance prediction", "AS": "AnytimeSwarm",
           "Risk": "AnytimeSwarm-R", "Buf": "Constant buffer", "Conv": "Conventional planner"}


def fig_s2_main():
    a2, cap = _study2()
    df, g, tests = cap["df"], cap["g"], cap["tests"]
    fig, axes = plt.subplots(1, 2, figsize=(W2, 3.0), gridspec_kw={"width_ratios": [1.0, 1.0], "wspace": 0.55})
    ax = axes[0]
    keys = ["Rep", "Fix", "Stag", "AS", "Conv"] + [k for k, *_ in tests]
    est = []
    for k in keys:
        if a2.M[k][0] in g.index:
            m, lo, hi, _ = a2.boot(a2.paired(df, a2.PROP, a2.M[k][0]), n=4000)
            est.append((k, m * 100, lo * 100, hi * 100))
    est.sort(key=lambda e: e[1])
    for i, (k, m, lo, hi) in enumerate(est):
        ebar(ax, i, m, lo, hi, METHOD["nofb"][1], METHOD["nofb"][2], horizontal=True, fill=lo > 0 or hi < 0, ms=4)
    zero(ax, horizontal=True)
    ax.set_yticks(range(len(est)), [S2_NAME[k] for k, *_ in est])
    ax.grid(axis="y", visible=False)
    ax.set_xlim(left=0)
    ax.set_xlabel(f"LTCC, no fallback {MINUS} method (pp)")
    panel(ax, "a", x=-0.02)
    print("fig_s2_main (a):", [(k, round(m, 2)) for k, m, *_ in est])

    ax = axes[1]
    style = {"Prop": METHOD["nofb"], "Buf": METHOD["buf"], "Conv": METHOD["conv"], "Forty": METHOD["nom"],
             "Fix": OTHER["fix250"]}
    pts = {}
    for k, (spec, _) in a2.M.items():
        if spec not in g.index or k.startswith("Abl"):
            continue
        r = g.loc[spec]
        _, col, mk = style.get(k, ("", "#9A9A9A", "o"))
        x, y = max(r.ms, 0.5), r.u * 100
        ax.scatter(x, y, s=34 if k == "Prop" else 22, color=col, marker=mk, zorder=3, edgecolor="white", lw=0.4)
        pts[k] = (x, y)
    ax.set_xscale("log")
    ax.set_xlim(0.3, 3e4)
    ax.set_xticks([1, 10, 100, 1000])
    ax.set_xticklabels(["1", "10", "100", "1000"])
    ax.minorticks_off()
    ax.set_xlabel("computation per planning call (ms)")
    ax.set_ylabel("utility (%)")
    panel(ax, "b", x=-0.02)
    near = {"Prop": (6, 0, "left"), "Buf": (6, 0, "left"), "Conv": (6, 0, "left"), "Fix": (-6, 0, "right"),
            "Rep": (6, 0, "left")}
    for k, (dx, dy, ha) in near.items():
        if k in pts:
            ax.annotate(S2_NAME[k], pts[k], textcoords="offset points", xytext=(dx, dy), fontsize=7.5, ha=ha,
                        va="center")
    # the dense cluster: labels in a column at the right, in the order of the utility, joined by thin leader lines
    cl = sorted([k for k in ("Risk", "AS", "Stag", "Prof", "Scaled", "Onl", "Forty") if k in pts],
                key=lambda k: -pts[k][1])
    top = pts["Buf"][1] - 0.45 if "Buf" in pts else max(p[1] for p in pts.values())
    for i, k in enumerate(cl):
        ax.annotate(S2_NAME[k], pts[k], xytext=(700, top - 0.3 * i), textcoords="data", fontsize=7.5, ha="left",
                    va="center", arrowprops=dict(arrowstyle="-", lw=0.5, color="0.55", shrinkA=1, shrinkB=2.5))
    ax.set_xlim(0.3, 1.5e5)
    save(fig, "fig_s2_main")

    keys = ["Prop", "Buf", "Forty", "Fix", "Conv"]
    sty = {"Prop": METHOD["nofb"], "Buf": METHOD["buf"], "Forty": METHOD["nom"], "Fix": OTHER["fix250"],
           "Conv": METHOD["conv"]}
    fig, axes = plt.subplots(1, 4, figsize=(W2, 2.2), gridspec_kw={"wspace": 0.35})
    for ax, (xl, wf), tag in zip(axes, REG4, "abcd"):
        sub = df[(df.exec_level == xl) & (df.window == wf)]
        t = sub.pivot_table(index="kappa", columns="method", values="utility_rate") * 100
        for k in keys:
            if a2.M[k][0] in t:
                _, col, mk = sty[k]
                ax.plot(t.index, t[a2.M[k][0]], marker=mk, ms=4, color=col, mec=col, lw=1.2, zorder=3)
        ax.set_xscale("log")
        ax.set_xticks([10, 50, 200], ["10", "50", "200"])
        ax.minorticks_off()
        ax.set_xlabel("latency factor")
        ax.text(-0.02, 1.03, f"({tag}) {xl}, windows ×{wf:g}", transform=ax.transAxes, ha="left", va="bottom",
                fontsize=8)
    axes[0].set_ylabel("utility (%)")
    legend_below(fig, axes, [handle(sty[k][1], sty[k][2], line=True) for k in keys],
                 [S2_NAME[k] if k != "Forty" else "Nominal model (ALNS, fixed 40 ms)" for k in keys], ncol=5)
    save(fig, "fig_s2_regime")


def fig_s2_bc():
    from analyze_study2 import TC, boot
    rows = []
    for d, trig in [("s2_heldout_C", "periodic:60"), ("s2_heldout_C_event", "event")]:
        for f in sorted((TC / d).glob("gz-*.json")):
            m = json.loads(f.read_text())
            r = {k: v for k, v in m.items() if not k.startswith("_")}
            r["spec"] = f"{r['method']}+{trig}"
            rows.append(r)
    c = pd.DataFrame(rows)
    spec_map = {"proposed+periodic:60": "Prop", "alns_fixed@40+periodic:60": "Forty",
                "alns_fixed@40~buf=60+periodic:60": "Buf", "alns_fixed@40+event": "Conv"}
    c["k"] = c.spec.map(spec_map)
    w = c.pivot_table(index="scenario", columns="k", values="utility_rate").dropna()
    b = pd.read_csv(TB / "s2_heldout_B_gz.csv")
    b["k"] = b.method.map(spec_map)
    wb = b.pivot_table(index="scenario", columns="k", values="utility_rate").dropna()
    keys = [k for k in ["Forty", "Buf", "Conv"] if k in w and k in wb]
    lab = {"Forty": "minus nominal\nmodel", "Buf": "minus constant\nbuffer", "Conv": "minus conventional\nplanner"}
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    out = {}
    for i, k in enumerate(keys):
        for dx, ww, key in [(-0.13, wb, "b"), (0.13, w, "c")]:
            m, lo, hi, _ = boot(ww["Prop"] - ww[k], n=4000)
            ebar(ax, i + dx, 100 * m, 100 * lo, 100 * hi, TIER[key][1], TIER[key][2], ms=5)
            out[(k, key)] = round(100 * m, 2)
    zero(ax)
    ax.set_xticks(range(len(keys)), [lab[k] for k in keys])
    for t in ax.get_xticklabels():
        t.set_linespacing(1.05)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel(f"LTCC, no fallback {MINUS} method (pp)")
    ax.legend([handle(TIER[k][1], TIER[k][2]) for k in ("b", "c")], [TIER[k][0] for k in ("b", "c")],
              loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2)
    print("fig_s2_bc means (pp):", out)
    save(fig, "fig_s2_bc")


def fig_study1():
    """Study 1 (AnytimeSwarm-R on the nominal model): fig_main and fig_bc of the supplementary material."""
    import make_paper_numbers as mpn
    df = pd.read_csv(TB / "heldout_B_main.csv")
    ours = mpn.OURS
    meths = ["alns_fixed", "alns_fixed@40", "alns_stagnation", "anytime_nodelay", "anytime", "anytime_risk"]
    names = {"alns_fixed": "ALNS, fixed 250 ms", "alns_fixed@40": "ALNS, fixed 40 ms",
             "alns_stagnation": "ALNS, stagnation stop", "anytime_nodelay": "AnytimeSwarm without delay cost",
             "anytime": "AnytimeSwarm", "anytime_risk": "AnytimeSwarm-R"}
    offs = {"alns_fixed": (-6, 6, "right"), "alns_fixed@40": (0, -9, "center"), "alns_stagnation": (6, 0, "left"),
            "anytime": (-7, 0, "right"), "anytime_nodelay": (6, 2, "left"), "anytime_risk": (-7, 5, "right")}
    fig, axes = plt.subplots(1, 2, figsize=(W2, 3.6), gridspec_kw={"width_ratios": [0.9, 1.1], "wspace": 0.62})
    ax = axes[0]
    g = df[df.method.isin(meths)].groupby("method").agg(u=("utility_rate", "mean"), ms=("plan_ms_mean", "mean"))
    for m, r in g.iterrows():
        col = "#000000" if m == ours else "#8C8C8C"
        ax.scatter(r.ms, r.u * 100, s=30, color=col, zorder=3, edgecolor="white", lw=0.4)
        dx, dy, ha = offs[m]
        ax.annotate(names[m], (r.ms, r.u * 100), textcoords="offset points", xytext=(dx, dy), fontsize=7.5, ha=ha,
                    va="center")
    lo_u, hi_u = g.u.min() * 100, g.u.max() * 100
    ax.set_ylim(lo_u - 0.25 * (hi_u - lo_u), hi_u + 0.25 * (hi_u - lo_u))
    ax.set_xscale("log")
    ax.set_xlim(12, 700)
    ax.set_xticks([20, 50, 100, 200, 500], ["20", "50", "100", "200", "500"])
    ax.minorticks_off()
    ax.set_xlabel("planning time per call (ms)")
    ax.set_ylabel("utility (%)")
    panel(ax, "a")
    ax = axes[1]
    sub = []
    for k, gg in df.groupby(mpn.CFG_KEY):
        w = gg.pivot_table(index="scenario", columns="method", values="utility_rate")
        if not {ours, "alns_fixed@40", "anytime"} <= set(w.columns):
            continue
        m, lo, hi, _ = mpn.boot(w[ours] - w["alns_fixed@40"], n=4000)
        m2, lo2, hi2, _ = mpn.boot(w[ours] - w["anytime"], n=4000)
        sub.append((k, m, lo, hi, m2, lo2, hi2))
    y = np.arange(len(sub))
    ebar(ax, y - 0.17, [100 * s[1] for s in sub], [100 * s[2] for s in sub], [100 * s[3] for s in sub],
         METHOD["nom"][1], METHOD["nom"][2], horizontal=True, ms=3.2)
    ebar(ax, y + 0.17, [100 * s[4] for s in sub], [100 * s[5] for s in sub], [100 * s[6] for s in sub],
         OTHER["as"][1], OTHER["as"][2], horizontal=True, ms=3.2)
    zero(ax, horizontal=True)
    lab = [f"{k[0]}, latency {k[1]}, factor {k[2]:g}, {'periodic' if 'periodic' in k[3] else 'event'}"
           for k, *_ in sub]
    ax.set_yticks(y, lab, fontsize=6.5)
    ax.set_ylim(len(sub) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"AnytimeSwarm-R {MINUS} method (pp)")
    panel(ax, "b", x=-0.02)
    legend_under(ax, [handle(METHOD["nom"][1], METHOD["nom"][2]), handle(OTHER["as"][1], OTHER["as"][2])],
                 ["ALNS, fixed 40 ms", "AnytimeSwarm"], ncol=2, gap=0.04)
    save(fig, "fig_main")

    # tier B against tier C on the same rescaled missions (study 1)
    rows = [{k: v for k, v in json.loads(f.read_text()).items() if not k.startswith("_")}
            for f in sorted((ROOT / "results" / "tier_c" / "heldout_C").glob("gz-*.json"))]
    dc = pd.DataFrame(rows)
    b = pd.read_csv(TB / "heldout_B_gz.csv")
    both = dc[["scenario", "method", "utility_rate"]].merge(b[["scenario", "method", "utility_rate"]],
                                                            on=["scenario", "method"], suffixes=("_c", "_b"))
    bases = ["alns_fixed", "alns_fixed@40", "anytime"]
    fig, axes = plt.subplots(1, 2, figsize=(W2, 2.7), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.3})
    ax = axes[0]
    for dx, key in [(-0.13, "b"), (0.13, "c")]:
        w = both.pivot_table(index="scenario", columns="method", values=f"utility_rate_{key}")
        est = np.array([mpn.boot(w[ours] - w[bb], n=4000)[:3] for bb in bases]) * 100
        ebar(ax, np.arange(len(bases)) + dx, est[:, 0], est[:, 1], est[:, 2], TIER[key][1], TIER[key][2], ms=5)
    zero(ax)
    ax.set_xticks(range(len(bases)), [f"minus {names[bb]}".replace(", ", ",\n") if "," in names[bb]
                                      else f"minus\n{names[bb]}" for bb in bases])
    for t in ax.get_xticklabels():
        t.set_linespacing(1.05)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel(f"AnytimeSwarm-R {MINUS} method (pp)")
    panel(ax, "a")
    ax.legend([handle(TIER[k][1], TIER[k][2]) for k in ("b", "c")], [TIER[k][0] for k in ("b", "c")],
              loc="lower left", bbox_to_anchor=(0.08, 1.0), ncol=2)
    ax = axes[1]
    ax.scatter(both.utility_rate_b * 100, both.utility_rate_c * 100, s=10, color="#0072B2", alpha=0.6, lw=0)
    lim = [min(both.utility_rate_b.min(), both.utility_rate_c.min()) * 100 - 3, 103]
    ax.plot(lim, lim, color="0.45", lw=0.8, ls="--")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_aspect("equal")
    ax.set_xlabel("utility in tier B (%)")
    ax.set_ylabel("utility in tier C (%)")
    panel(ax, "b")
    save(fig, "fig_bc")


def fig_static():
    """Exact-execution benchmark of the conference version (test seeds 2000-2029, supplementary S3): quality-compute
    frontiers (a-c) and computation per snapshot (d). Data: ../results_test2/offline of the conference repository."""
    src = ROOT.parent / "results_test2" / "offline"
    fr = pd.read_csv(src / "frontier_test.csv")
    al = pd.read_csv(src / "allocation_test.csv").set_index("family")
    fam = [("fixed", "ALNS, fixed budget", "#8C564B", "p", "-"), ("stagnation", "ALNS, stagnation stop", "#9A9A9A", "^", "-"),
           ("oracle_stop", "oracle stop (hindsight)", "0.35", None, ":"), ("anytime", "AnytimeSwarm", "#000000", "o", "-")]
    per = [("fixed_ps", "#8C564B", "p", "ALNS, fixed budget per scale"),
           ("stagnation_ps", "#9A9A9A", "^", "ALNS, stagnation stop per scale")]
    fig, axes = plt.subplots(1, 3, figsize=(W2 * 0.68, 2.1), gridspec_kw={"wspace": 0.32})
    spec = [(fr[(fr.scale == "medium") & (fr.kappa == 1)], "regret_pct", "(a) medium fleet,\nlatency factor 1", 0.3),
            (fr[(fr.scale == "large") & (fr.kappa == 1)], "regret_pct", "(b) large fleet,\nlatency factor 1", 0.9),
            (fr[(fr.scale == "all") & (fr.kappa == 50)], "eff_regret", "(c) all fleets,\nlatency factor 50", 0.8)]
    for ax, (g, ycol, title, ymax) in zip(axes, spec):
        for f, lab, col, mk, ls in fam:
            d = g[(g.family == f) & (g.t_ms >= 0.8)].sort_values("t_ms")
            ax.plot(d.t_ms, d[ycol], color=col, ls=ls, lw=1.3 if f == "anytime" else 1.0, marker=mk, ms=3,
                    mec=col, zorder=3)
            if f == "anytime":
                s = d[np.isclose(d.param, 1e-5)]
                ax.plot(s.t_ms, s[ycol], marker="*", ms=8, color="#000000", mec="white", mew=0.5, ls="none", zorder=5)
        for f, col, mk, _ in per:
            d = g[g.family == f]
            ax.plot(d.t_ms, d[ycol], marker=mk, ms=5, mfc="white", mec=col, mew=1.0, ls="none", zorder=4)
        ax.set_xscale("log")
        ax.set_xlim(1, 600)
        ax.set_xticks([1, 10, 100], ["1", "10", "100"])
        ax.minorticks_off()
        ax.set_ylim(0, ymax)
        ax.set_xlabel("mean computation (ms)")
        ax.text(-0.02, 1.03, title, transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5, linespacing=1.1)
    axes[0].set_ylabel("regret (%)")
    hs = [Line2D([], [], color=c, ls=ls, marker=mk, ms=3, lw=1.1) for _, _, c, mk, ls in fam]
    hs += [Line2D([], [], marker=mk, ms=5, mfc="white", mec=c, mew=1.0, ls="") for _, c, mk, _ in per]
    hs.append(Line2D([], [], marker="*", ms=8, color="#000000", mec="white", ls=""))
    labs = [f[1] for f in fam] + [p[3] for p in per] + ["selected AnytimeSwarm setting"]
    legend_below(fig, axes, hs, labs, ncol=3)
    save(fig, "fig_static_frontier")

    share = al.n_none.iloc[0] / (al.n_none.iloc[0] + al.n_pos.iloc[0]) * 100
    groups = [f"no gain\n({share:.0f}% of\nsnapshots)", "low", "medium", "high"]
    cols = ["t_none", "t_low", "t_mid", "t_high"]
    series = [("fixed_ps", "ALNS, fixed budget per scale", "#C9A89E"),
              ("stagnation_ps", "ALNS, stagnation stop per scale", "#C8C8C8"), ("anytime", "AnytimeSwarm", "#3C3C3C")]
    fig, ax = plt.subplots(figsize=(W2 * 0.3, 2.1))
    x = np.arange(len(groups))
    w = 0.26
    for i, (f, lab, col) in enumerate(series):
        v = al.loc[f, cols].values
        ax.bar(x + (i - 1) * w, v, w * 0.92, color=col, label=lab, zorder=3)
        if f == "anytime":
            for xx, vv in zip(x + (i - 1) * w, v):
                ax.text(xx, vv + 2, f"{vv:.0f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x, groups)
    for t in ax.get_xticklabels():
        t.set_linespacing(1.0)
        t.set_fontsize(7.5)
    ax.set_ylabel("mean computation (ms)")
    ax.set_xlabel("improvement still available")
    ax.set_ylim(0, al[cols].values.max() * 1.18)
    ax.grid(axis="x", visible=False)
    ax.text(-0.02, 1.03, "(d)", transform=ax.transAxes, ha="left", va="bottom", fontsize=7.5)
    legend_below(fig, ax, [plt.Rectangle((0, 0), 1, 1, color=c) for *_, c in series], [s[1] for s in series], ncol=1)
    save(fig, "fig_static_allocation")


FIGS = {"errstructure": fig_errstructure, "s4c": fig_s4c, "s5": fig_s5, "s6": fig_s6, "s7": fig_s7,
        "demo_tracks": fig_demo_tracks, "demo_gazebo": fig_demo_gazebo,
        "s4_regimes": fig_s4_regimes, "s3": fig_s3_regimes, "replication": fig_replication, "latepen": fig_latepen,
        "calib": fig_calib, "s2_main": fig_s2_main, "s2_bc": fig_s2_bc, "study1": fig_study1, "static": fig_static}

if __name__ == "__main__":
    import analyze_study2  # noqa: F401,E402  (imported first: these modules set rcParams at import)
    import paper_calib  # noqa: F401,E402
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        style()
        FIGS[n]()
