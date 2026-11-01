# Recent works and reference verification notes (2026-10-28)

Sources: Crossref REST API (metadata, DOIs, volume/issue/pages), Semantic Scholar API (abstracts),
arXiv HTML full text (Calvo & Capitan only). DBLP blocked automated access, and MDPI/ScienceDirect
pages returned HTTP 403, so feature rows rely on the **abstracts** unless stated otherwise.
"n/a" = not determinable from what I could read.

## Part A: verification results

| Key | Status | Corrections / remarks |
|---|---|---|
| cashmore2018clock | verified | ICAPS 28, pp. 39-46, doi:10.1609/icaps.v28i1.13878 |
| shperberg2019allocating | verified | AAAI 33(01), pp. 2371-2378, doi:10.1609/aaai.v33i01.33012371 |
| shperberg2021situated | verified | Authors: Shperberg, Coles, Karpas, Ruml, Shimony (no Cserna). ICAPS 31, pp. 340-348, doi:10.1609/icaps.v31i1.15979 |
| dionne2011deadline | verified | SoCS 2011 (vol. 2, no. 1), pp. 39-46, doi:10.1609/socs.v2i1.18199 |
| vieira2003rescheduling | verified | J. Scheduling 6(1):39-62, doi:10.1023/A:1022235519958 |
| ouelhadj2009survey | verified | J. Scheduling 12(4):417-431 (2009; online 2008), doi:10.1007/s10951-008-0090-8 |
| ritzinger2016survey | verified | IJPR 54(1):215-231 (2016; online 2015), doi:10.1080/00207543.2015.1043403 |
| boddy1994deliberation | verified | Artificial Intelligence 67(2):245-285, doi:10.1016/0004-3702(94)90054-X |
| bhatia2022tuning | verified | Authors confirmed: Abhinav Bhatia, Justin Svegliato, Samer B. Nashed, Shlomo Zilberstein. ICAPS 32, pp. 556-564, doi:10.1609/icaps.v32i1.19842 |
| errico2018vrptw | verified, **venue corrected** | The 2018 paper is in the **EURO Journal on Transportation and Logistics** 7(3):223-251, doi:10.1007/s13676-016-0101-4, not EJOR. The same authors' EJOR paper is "A priori optimization with recourse for the VRP with hard time windows and stochastic service times", EJOR 249(1):55-66 (2016), doi:10.1016/j.ejor.2015.07.027. Both are in the .bib (second as `errico2016apriori`). |
| agra2013robust | verified | C&OR 40(3):856-866, doi:10.1016/j.cor.2012.10.002 |

## Part B: recent related works (2022-2026)

Features: TW = time windows/deadlines; Unc = execution/duration uncertainty modelled; Trig = replanning-trigger policy studied;
Comp = computation time / anytime / when-to-stop; Val = physics/SITL/real-flight validation; Arch = centralised/distributed.

1. **Calvo & Capitan (2025), IEEE T-RO 41:6494-6513, doi:10.1109/TRO.2025.3626651** (`calvo2025heterogeneous`)
   Heterogeneous MRTA for long-endurance UAV missions with recharging, task fragmentation/relays and coalitions; MILP + heuristic inside a planning-and-execution architecture that repairs or recomputes plans online after unexpected events.
   - TW: deadlines only; full text states "we do not have specific time windows in which tasks need to start".
   - Unc: no stochastic model. Robot delays, failures, battery depletion and new tasks are handled as events that trigger repair.
   - Trig: event-driven (repair first, full recompute if repair fails). Different trigger policies are not compared.
   - Comp: computation times reported (the heuristic takes minutes in the worst case). No anytime or stopping rule.
   - Val: **Gazebo simulation of a solar plant with PX4 SITL, in a ROS architecture** (full text). Real flights are listed as future work.
   - Arch: centralised planning, distributed execution.
   - Closest prior work to ours on the validation stack.

2. **Choudhury, Gupta, Kochenderfer, Sadigh & Bohg (2022), Autonomous Robots 46(1):231-247, doi:10.1007/s10514-021-10022-9** (`choudhury2022dynamic`)
   SCoBA: hierarchical allocation under time windows and task-completion uncertainty. Per-agent dynamic programming and tree-search policies, with an upper layer that resolves conflicts. Planning is interleaved with execution online.
   - TW: yes.
   - Unc: yes, stochastic task completion.
   - Trig: n/a (online interleaving; trigger policy not studied).
   - Comp: claimed efficient enough for online use. No anytime or stopping rule.
   - Val: simulation only (conveyor pick-and-place, multi-drone delivery dispatch in a city). No physics or SITL.
   - Arch: hierarchical (individual policies plus conflict resolution).

3. **Cong, Li, Zhu & Wang (2026), Drones 10(9):684, doi:10.3390/drones10090684** (`cong2026event`)
   ET-PBBA: event-triggered, path-based (A*) bid assignment for energy-aware dynamic multi-UAV allocation with online task release, deadlines, energy limits and failures.
   - TW: deadlines (yes).
   - Unc: vehicle failures. Duration uncertainty not modelled (n/a).
   - Trig: **yes**. Event-time activation is compared with 10 s periodic allocation and raises completion by 0.046 to 0.065.
   - Comp: n/a.
   - Val: a single-UAV trajectory replay with 9.16 cm mean error. The authors call this auxiliary evidence, not online multi-UAV execution, and the abstract does not name the platform.
   - Arch: n/a (compared against auction, CBBA and centralised Hungarian).

4. **Li, Liu, Zheng & Liu (2026), Drones 10(9):649, doi:10.3390/drones10090649** (`li2026pathmatrix`)
   Coupled dynamic task allocation and path planning as dynamic multi-objective optimisation, solved with a three-role multi-swarm crow search. A path matrix feeds back to allocation, and the method inherits the execution state.
   - TW: n/a.
   - Unc: n/a (dynamic events).
   - Trig: rolling-horizon refinement of leading flight segments. Its latency, not the trigger policy, is evaluated: replanning latency falls by 48.8-70.5%.
   - Comp: replanning latency reported. No anytime or stopping rule.
   - Val: simulated dynamic urban scenarios (n/a for physics or SITL).
   - Arch: n/a.

5. **Zhao, Li, Zhu & Zhu (2026), Drones 10(7):523, doi:10.3390/drones10070523** (`zhao2026assignment`)
   AC-DMTA: a CBBA-family method in which agents communicate only when local uncertainty could invalidate the current assignment. It uses interval bids and certificates for winner and bundle stability.
   - TW: n/a.
   - Unc: yes, through uncertainty sets on stale or asymmetric state records (information uncertainty, not duration).
   - Trig: communication is event-triggered (certificate-gated), compared with periodic CBBA and ED-CBBA.
   - Comp: n/a (communication bytes are the focus).
   - Val: four benchmark environments with 20 paired seeds, plus delay and packet-loss stress tests. n/a for physics or SITL.
   - Arch: distributed.

6. **Ali, Athar & Maqsood (2026), Expert Systems (Wiley) 43(12):e70459, doi:10.1111/exsy.70459** (`ali2026sitl`)
   Federated PPO for UAV swarm navigation, including priority-based dynamic task allocation: a secondary target emerges mid-mission and triggers swarm partitioning.
   - TW: n/a.
   - Unc: n/a.
   - Trig: event-driven (new target). The trigger policy is not studied.
   - Comp: reallocation time reported. No anytime or stopping rule.
   - Val: **SITL with ArduPilot and Gazebo Harmonic, using MAVLink** (ArduPilot, not PX4).
   - Arch: federated or decentralised learning.
   - Note: the journal is Wiley *Expert Systems*, not Elsevier ESWA.

7. **Huang, Jiang, Yan & Bai (2024), Drones 8(6):236, doi:10.3390/drones8060236** (`huang2024dynamic`)
   Heterogeneous multi-UAV dynamic assignment under uncertainty, using a fuzzy multi-constraint model (binary interval theory) solved with 4DI-GWO.
   - TW: n/a.
   - Unc: **yes**. Uncertain target location, mission execution time and survival probability are modelled as interval or fuzzy quantities.
   - Trig: dynamic time slices adjust how often the problem is re-solved (a periodic or adaptive trigger).
   - Comp: n/a.
   - Val: numerical only.
   - Arch: n/a (likely centralised, but this is not stated).

Considered but not included: Dai et al. (2025), RA-L 10(3):2654-2661, doi:10.1109/LRA.2025.3534682, which uses RL for heterogeneous MRTA and scheduling, is decentralised, and is about 100x faster than MIP. It is mainly static, though it is reactive. Han & Guo (2025), Applied Sciences 15(8):4220, doi:10.3390/app15084220, applies rolling-horizon adaptive PSO to UAV task allocation. I did not read its abstract.

## Manuscript entries checked (all four exist as stated)

| # | Entry | DOI | Exact bibliographic data |
|---|---|---|---|
| i | Hwang, Oh, Lee, Lee, Lee & Hwang, "Assignment-Preserving Replanning for Dynamic Task Allocation in Multi-UAV Systems" | 10.3390/app16199414 | Applied Sciences 16(19):9414, 2026 (published 22 Sep 2026). Six authors: Se-Yun Hwang, Seunghoon Oh, Jae-Chul Lee, Soonsup Lee, Jong-Hyun Lee, Ho-Jin Hwang |
| ii | Shen, Hu, Wan, Sun & Tan, "Edge-Responsive Local-Repair Particle Swarm Optimization for Dynamic Spatiotemporal Task Allocation of IoT-Connected UAV Swarms" | 10.1109/ACCESS.2026.3717031 | IEEE Access 14:115169-115190, 2026 |
| iii | Qian & Fu, "Uncertainty-Gated Distributed Dynamic Task Allocation for Multi-UAV Systems Under Intermittent Communication" | 10.3390/drones10100782 | Drones 10(10):782, 2026 (published 16 Oct 2026) |
| iv | Wang, Sun & Huang, "An adaptive large neighborhood search for the multi-depot dynamic vehicle routing problem with time windows" | 10.1016/j.cie.2024.110122 | Computers & Industrial Engineering 191:110122, May 2024. First author: Sihan Wang |

Feature rows:

- **(i) Hwang et al. 2026 (APR).** Repairs the plan while protecting still-valid assignments and route structure. It releases protected tasks only when needed to recover feasibility.
  - TW: yes, including changes to task time windows.
  - Unc: no duration model. Robustness is checked over 10 random seeds.
  - Trig: event-driven (new tasks, UAV failures, time-window changes). The trigger policy is not studied.
  - Comp: computation time is reported and is substantially shorter than global ALNS replanning. No anytime or stopping rule.
  - Val: numerical (n/a for physics or SITL).
  - Arch: n/a.
  - Baselines include two global ALNS methods.
- **(ii) Shen et al. 2026 (LRPSO-DTA).** Local-repair PSO for online arrivals. It locks short-horizon sequences and updates only the affected dependencies.
  - TW: spatiotemporal tasks; explicit windows n/a.
  - Unc: n/a (stochastic arrival bursts).
  - Trig: event-driven local repair compared with full replanning. This compares the scope of the replan, not trigger policies.
  - Comp: designed for low latency. The gap to CPLEX is 5.8%, and cumulative cost is about 60% lower than full replanning. No anytime or stopping rule.
  - Val: numerical.
  - Arch: n/a (edge-enabled).
- **(iii) Qian & Fu 2026 (UCDG-PD).** One-task-per-UAV distributed allocation. A lower-confidence-bound chance constraint gates graph edges, then entropic or price-based consensus assigns tasks.
  - TW: deadlines plus task release and expiry (yes).
  - Unc: **yes**. Chance constraints on edge reliability (uncertain task return or reachability) are calibrated by a held-out coverage audit: 0.944 against a nominal 0.95.
  - Trig: decision epochs; the trigger policy is not studied.
  - Comp: n/a.
  - Val: trajectory-level simulation with UAV motion and energy models. No physics or SITL.
  - Arch: distributed.
  - Conceptually closest to our calibrated-buffer idea.
- **(iv) Wang, Sun & Huang 2024 (multi-depot dynamic VRPTW with ALNS).** The full abstract was not retrievable (ScienceDirect returned 403, and Crossref, Semantic Scholar and OpenAlex had no abstract). An indexed fragment confirms that requests arrive stochastically during the operating period, with time windows and multiple depots.
  - TW: yes.
  - Unc: request arrivals only (n/a beyond that).
  - Trig: n/a.
  - Comp: n/a.
  - Val: n/a (vehicle routing, not UAVs).
  - Arch: n/a.

## Gap summary relevant to our positioning

- Only Cong et al. 2026 compares event-triggered with periodic triggering directly, and only for a single period (10 s).
- None of the papers above treats when to stop the replanner (metareasoning or a learned stopping rule) for task allocation. Computation time is at most reported as an outcome.
- Calibrated uncertainty appears only in Qian & Fu 2026, as an edge-reliability LCB. None calibrates finish-time error to buffer deadlines.
- SITL or physics validation appears in Calvo & Capitan 2025 (Gazebo + PX4 SITL + ROS) and Ali et al. 2026 (Gazebo + ArduPilot SITL).

## Bổ sung 01/11/2026 (bảng tab_related, cột "Late cost" và "Online"; nguồn: tóm tắt trên trang nhà xuất bản)
- Taş, Dellaert, van Woensel & de Kok (2013), Computers & OR 40(1):214–224, doi:10.1016/j.cor.2012.06.008
  (`tas2013stochastic`). VRP với thời gian đi ngẫu nhiên và soft time windows; mục tiêu = chi phí vận chuyển + chi phí phục
  vụ sớm/trễ kỳ vọng; tabu search. TW ✓, Unc ✓, Late cost ✓, Online –.
- Ehmke, Campbell & Urban (2015), EJOR 240(2):539–550 (`ehmke2015ensuring`). VRPTW với mức phục vụ (chance constraint
  theo khách hàng), lan truyền mô-men trong heuristic. TW ✓, Unc ✓, Late cost – (ràng buộc mức phục vụ, không phải chi
  phí), Online –.
- Zhou & Tokekar (2022), IEEE T-RO 38(5):3064–3084, doi:10.1109/TRO.2022.3158227 (`zhou2022risk`). Phân công đa robot
  theo CVaR, thuật toán tham lam tuần tự. TW –, Unc ✓, Online – (không báo cáo replanning trong nhiệm vụ).
- Gao, Zheng, Mei, Zheng & Zhong (2025), Drones 9(9):633, doi:10.3390/drones9090633 (`gao2025drcc`). Phân công UAV
  dị thể có time windows, chance constraint phân phối bền vững (Wasserstein), xấp xỉ CVaR → MILP. TW ✓, Unc ✓ (nhiên
  liệu), Online –.
- Wang, Jia, Guo & Hou (2024), Aerospace 11(3):214, doi:10.3390/aerospace11030214 (`wang2024uncertain`). Ước lượng
  nhanh thời điểm hoàn thành và xác suất vi phạm time window dưới thời gian bay bất định, không cần Monte Carlo. TW ✓,
  Unc ✓, Online –.
- Johnson, Choi, Ponda & How (2012), IEEE CDC, pp. 4702–4708, doi:10.1109/CDC.2012.6425867 (`johnson2012nonsubmodular`).
  Bid warping cho CBBA với hàm điểm không submodular; dùng trong cài đặt CBBA của nghiên cứu 6 (không có trong bảng).

## Bổ sung 01/11/2026 (đợt 2): cập nhật trích dẫn sang tài liệu 2021–2025
Mỗi mục đã kiểm chứng qua trang nhà xuất bản, DOI, RePEc/DBLP hoặc kho lưu trữ của trường (xem lịch sử phiên làm việc).
- skaltsis2023review: J. Intell. Robot. Syst. 109:76 (2023), doi:10.1007/s10846-023-02011-0 (Cranfield DSpace).
- chakraa2023mrta: Robot. Auton. Syst. 168:104492 (2023), doi:10.1016/j.robot.2023.104492.
- soeffker2022review: EJOR 298(3):801–820 (2022), doi:10.1016/j.ejor.2021.07.014 (RePEc, DBLP).
- rostami2021correlated: Oper. Res. 69(2):436–455 (2021), doi:10.1287/opre.2020.2037 (RePEc, INFORMS).
- bomboi2022stochastic: 4OR 20(2):217–239 (2022, online 2021), doi:10.1007/s10288-021-00476-z (TU Dortmund).
- mara2022alns: Comput. Oper. Res. 146:105903 (2022), doi:10.1016/j.cor.2022.105903.
- herrmann2023metareasoning: Springer Synthesis Lectures on Computer Science (2023), ISBN 978-3-031-32236-5 (UMD).
- rojasviloria2021drones: Int. Trans. Oper. Res. 28(4):1626–1657 (2021), doi:10.1111/itor.12783.
- bruni2023drone: Transp. Res. C 156:104322 (2023), doi:10.1016/j.trc.2023.104322 (PoliTo IRIS). Bảng: TW –, Unc ✓
  (thời gian bay bất định, robust optimisation).
- cheng2024weather: MSOM 26(4):1402–1421 (2024), doi:10.1287/msom.2022.0339 (RePEc, INFORMS). Bảng: TW ✓, Unc ✓ (gió),
  Late cost ✓ (chỉ số rủi ro tính cả xác suất và độ lớn của việc trễ), Online ∘ (lịch được sửa buổi chiều theo dự báo).
- wang2022phases: Aerospace 9(9):491 (2022), doi:10.3390/aerospace9090491 (MDPI, DOAJ). CBBA cải tiến cho nhiệm vụ động
  và time windows.
- lacerda2022decision: AI Communications 35(4):433–441 (2022), doi:10.3233/AIC-220118 (IOS Press, DBLP).
- dukkanci2021energy: Transp. Res. C 125:102985 (2021), doi:10.1016/j.trc.2021.102985.
- zhao2025throughput: IEEE Trans. Computers 74(2):442–454 (2025, online 10/2024), doi:10.1109/TC.2024.3483636.
Không dùng (không kiểm chứng được): Svegliato và cs. ICRA 2022 "Metareasoning for safe decision making"; Aerostack2
(mới là preprint arXiv); PBW-CBBA (không rõ năm, nơi đăng).
Bỏ khỏi bài chính (không thiết yếu, đã có tài liệu mới thay): pillac2013review, dean1988analysis, russell1991right,
hansen2001monitoring, dionne2011deadline, potvin1993parallel, shaw1998cp, kirkpatrick1983annealing,
vieira2003rescheduling, ouelhadj2009survey, gendreau1996stochastic, bent2004scenario.
Kết quả: bài chính 54 tài liệu, 29 (54%) từ 2021 trở lại; tài liệu cũ còn lại là phương pháp thống kê, công cụ, bài toán
gốc và các baseline được cài lại.
