# Reproducing the results of the LTCC manuscript

Manuscript: *Lead-Time-Scaled Chance Constraints With a Cost-Aware Fallback for Fast Multi-UAV Replanning Under
Uncertain Execution* (Ha, Nguyen Vu Minh, Le). This package contains the planner, both simulation tiers, the frozen
protocols, the raw held-out results and the scripts that produce every number, table and figure of the manuscript and
its supplementary material.

## 1. Layout

| Path | Content |
|---|---|
| `original/` | frozen conference code (`anytimeswarm` package: scenario generator, ALNS, repair, stopping rules), configs, predictor, `MANIFEST.sha256` |
| `journal_core/` | journal code: kinematic executor (tier B), execution and latency models, planning models of studies 2-7 (`study2.py` ... `study7.py`) |
| `journal_ros/`, `ros2_ws/` | tier C: ROS 2 mission manager and executor for PX4 SITL + Gazebo |
| `experiments/` | grid runners (`b*_grid.py`), configs (`configs/S*_B.yaml`), analysis and figure scripts |
| `tools/` | freeze scripts (`p*_freeze.sh`), held-out runners (`run_study*.sh`), machine guard, PX4 log cleanup |
| `tests/` | unit tests of every planning model (pytest) |
| `docs/` | written protocols (`05`, `08`, `10`, `12`, `13`, `14`, `16`), plans and the review response (`15`, `17`) |
| `results/` | `frozen_*_sha256.txt` freeze lists, `tier_b/*.csv` raw run results, `tier_c/` flight summaries, `study*/report*.md`, `heldout_logs/` |
| `paper_journal/` | manuscript sources (`ieee/`), generated tables and numbers (`tables/`), figures (`figures/`, TikZ in `figures_src/`) |

## 2. Studies, protocols and freezes

Every study was frozen before its held-out runs: the protocol, configurations, code and tests were hashed (SHA-256)
into `results/frozen_*_sha256.txt` and committed; the held-out runner checks these hashes before it starts. The
protocols were not lodged with an external registry; the git history gives the commit of every freeze, and deviations
are listed at the end of each protocol. The protocols of studies 1-6 are written in Vietnamese and that of study 7 in
English; their primary hypotheses are listed in Table 4 of the manuscript, and the table below summarises the rest.

| Study | Protocol | Freeze commit (date) | Held-out seeds | Config | Runner | Analysis (outputs) |
|---|---|---|---|---|---|---|
| 1 | `docs/05_PROTOCOL_JOURNAL.md` | a561c7a (2026-10-28) | 3000-3029 (B), 4000-4009 (C) | `B_main.yaml`, `C_main.yaml` | `tools/run_heldout_all.sh` | `analyze_heldout.py`, `make_paper_numbers.py` (`numbers.tex`) |
| 2 | `docs/08_PROTOCOL_V2.md` | d0ca1ad (2026-10-28) | 5000-5029 (B), 6000-6009 (C) | `S2_B_main.yaml`, `S2_B_gz.yaml` | `tools/run_study2_all.sh` | `analyze_study2.py` (`numbers_s2.tex`) |
| 3 | `docs/10_PROTOCOL_V3.md` | 281b67a (2026-10-29) | 7000-7029 | `S3_B.yaml` | `tools/run_study3.sh` | `analyze_study3.py`, `paper_study3_extras.py` |
| 4, 4C | `docs/12_PROTOCOL_V4.md` | 074268e (2026-10-29) | 8000-8029 (B), 9000-9011 (C) | `S4_B.yaml`, `S4C_B_gz.yaml` | `tools/run_study4.sh` | `analyze_study4.py`, `analyze_study4c.py`, `paper_s4x.py`, `paper_s4c.py` |
| 5 | `docs/13_PROTOCOL_V5.md` | 0ff733a (2026-10-31) | 10000-10029 | `S5_B.yaml` | `tools/run_study5.sh` | `analyze_study5.py` (`numbers_s5.tex`) |
| 6 | `docs/14_PROTOCOL_V6.md` | 21cb576 (2026-11-01) | 12000-12029 | `S6_B.yaml` | `tools/run_study6.sh` | `analyze_study6.py` (`numbers_s6.tex`) |
| 7a, 7b | `docs/16_PROTOCOL_V7.md` | fc78b5e (2026-11-02) | 13000-13029, 14000-14029 | `S7a_B.yaml`, `S7b_B.yaml`, `S7b_lat_B.yaml` | `tools/run_study7.sh` | `analyze_study7.py` (`numbers_s7.tex`) |

Development used seeds 0-9 (tier B) and 0-2 (tier C) only. Each tier B study has 270 missions (30 seeds x 3 fleet
scales x 3 event profiles) in 12 configurations (2 disturbance levels x 3 latency factors x 2 window factors; study 7b:
6 execution conditions x 6 configurations).

Analyses added after the runs, without new runs, and marked as such in the manuscript:
`robust_cluster.py` (seed-cluster bootstrap, `numbers_robust.tex`, `tab_cluster.tex`), `paper_calib.py` (calibration,
`numbers_calib.tex`, `fig_calib.pdf`), `paper_latepen.py` (re-scoring with a late cost), `paper_s7const.py` (study 7a
with the exact fixed-cost score), `paper_s7fig.py` (figure of study 7 and per-regime numbers), `paper_extra.py`,
`paper_errstructure.py`, `paper_replication.py`, `paper_demo.py`.

## 3. Environment

Tier B: Linux (tested on WSL2 Ubuntu 24.04) or Windows, Python 3.12 with numpy, scipy, pandas, scikit-learn, pyyaml,
matplotlib and OR-Tools (`setup/06_python_envs.sh`). Tier C additionally needs ROS 2 Jazzy, Gazebo Harmonic, PX4 v1.17.0,
px4_msgs release/1.17 and the Micro-XRCE-DDS Agent v2.4.3 (`setup/02`-`05`).

    python -m pytest -q tests/                       # unit tests of all planning models

## 4. Reproducing the tables and figures from the raw results (minutes)

Every number in the manuscript is a macro from `paper_journal/tables/numbers*.tex`; none is typed by hand. From the
CSV files in `results/tier_b/` and `results/tier_c/`:

    cd experiments
    python analyze_study2.py; python analyze_study3.py; python paper_study3_extras.py
    python analyze_study4.py; python analyze_study4c.py; python paper_s4x.py; python paper_s4c.py
    python paper_latepen.py; python analyze_study5.py; python analyze_study6.py; python paper_extra.py
    python analyze_study7.py; python paper_s7fig.py; python paper_s7const.py
    python robust_cluster.py; python paper_calib.py
    cd ..
    python experiments/paper_figs_final.py        # final style of every data figure (presentation only)
    python experiments/paper_tables_final.py      # tabm_*.tex: short captions, method names, table notes
    cd paper_journal/figures_src
    pdflatex fig_overview; pdflatex fig_tierc      # TikZ diagrams; copy both PDFs to ../figures/
    cd ../ieee
    pdflatex main; bibtex main; pdflatex main; pdflatex supplementary; bibtex supplementary; pdflatex supplementary; pdflatex main

`paper_s7fig.py` redraws `fig_s7.pdf` after `analyze_study7.py` (protocol V7, deviation 4). `paper_figs_final.py` then
redraws all data figures in one style from the same data, and `paper_tables_final.py` copies the generated tables to
`tabm_*.tex` with short captions and the method names of the text; neither changes a number. Bootstrap resampling uses
a fixed seed, so the intervals and p-values are reproduced exactly.

## 5. Re-running the experiments (hours)

    python experiments/b7_grid.py --config experiments/configs/S7a_B.yaml --split heldout --resume

(analogously `b2_grid.py` ... `b7_grid.py` with the configs of section 2; `tools/run_study*.sh` run a whole study
including the freeze check). One tier B study takes about 4 h on an 8-core laptop with 4 workers.

Two sources of variation remain. ALNS stops at a wall-clock budget of 40 ms, so the number of search iterations, and
with it the plan, depends on the speed of the machine; a repeated run of the same missions changed the mean utility of a
method by up to 0.12 percentage points (Section VII of the manuscript). All execution disturbances use common
random numbers keyed to the mission seed, UAV and task, and are reproduced exactly. Tier C flights additionally depend
on the real-time factor of Gazebo; runs outside [1.6, 2.2] were repeated as stated in the protocols.
