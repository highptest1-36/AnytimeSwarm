# AnytimeSwarm Journal: kế hoạch từ bản hội nghị lên ROS 2 / PX4 / Gazebo

Lập ngày 27/10/2026. Đầu vào: hướng dẫn cài đặt ROS 2/Gazebo/PX4 do người dùng cung cấp, đối chiếu với code và kết quả
trong `D:\paper\TAIMMA_2027\AnytimeSwarm` (bản TAIMMA 2027, không sửa).

## 0. Nguyên tắc

1. Thư mục `AnytimeSwarm\` của bản hội nghị giữ nguyên. Mọi việc cho journal nằm trong `AnytimeSwarm_Journal\`.
   Code gốc được chép sang `original\` kèm `MANIFEST.sha256` để chứng minh không bị đổi.
2. Mọi thứ cài trên ổ D: distro WSL ở `D:\WSL\Ubuntu-24.04\ext4.vhdx`. Các thư mục `~/PX4-Autopilot`, `~/px4_ros_ws`
   nằm trong file vhdx này nên cũng ở trên ổ D.
3. Ngày 27/10/2026 người dùng quyết định không nộp TAIMMA. Toàn bộ công sức chuyển sang bản journal. Bản hội nghị
   (code, kết quả, bản thảo 15 trang) là baseline và là phần lõi của bản thảo journal.
4. Không đo thời gian trong lúc RAVEN-UAV đang chạy. Lúc build PX4, CPU tải nặng; không build song song với các lần đo của RAVEN.
5. Không chạy lại hay tinh chỉnh trên các seed test đã dùng (1000–1009, 2000–2029, XL 2000–2029) nếu chưa có quyết định
   rõ ràng (mục 3). Journal dùng seed test mới, đăng ký trước.

## 1. Đối chiếu hướng dẫn với dự án hiện tại

### 1.1 Phần hướng dẫn đúng, giữ nguyên

| Mục | Kiểm tra ngày 27/10 |
|---|---|
| Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic | đúng cặp chính thức |
| PX4 `v1.17.0` | tag có trên GitHub (đã có cả 1.18.0-rc1; vẫn khóa 1.17.0) |
| `px4_msgs` nhánh `release/1.17` | có |
| Micro-XRCE-DDS-Agent `v2.4.3` | có (3.0.x đã ra; PX4 1.17 vẫn dùng 2.4.x) |
| Ba tầng A/B/C, không đưa 40 UAV vào Gazebo | hợp lý |
| Giữ predictor gốc, đóng băng, kiểm thử zero-shot trước khi retrain | rất quan trọng, giữ |
| Bootstrap theo nhiệm vụ (mission), không theo từng sự kiện | đã có trong `06_bootstrap.py` |

### 1.2 Chỗ hướng dẫn chưa khớp với dự án (phải sửa trong kế hoạch)

1. Seed. Hướng dẫn chỉ nhắc dev 0–9 và confirmatory 2000–2029. Thực tế có ba tập test đã dùng một lần: test1
   1000–1009, test2 2000–2029 (270 nhiệm vụ) và XL 40 UAV/280 task (2000–2029, `results_xl/`).
   Journal cần seed held-out mới: đề xuất 3000–3029 cho tầng B và 4000–4029 cho tầng C, ghi vào config trước khi chạy.
2. Thông số gốc cần ghi đúng: ngân sách static `[20, 50, 100, 250, 500]` ms, ngân sách closed-loop 250 ms,
   `check_ms=5`, `horizon_ms=10`, `mu=1e-5`, `kappa ∈ {1, 10, 50}`, thế giới 10 km, horizon 1800 s, tốc độ 10–16 m/s,
   service 30–90 s, cửa sổ deadline 180–600 s, năng lượng tính bằng "mét bay" (`hover_m_per_s = 6`).
3. Vấn đề cốt lõi mà hướng dẫn chưa thấy: thang thời gian. Trong code, kế hoạch được phát hành ở
   `t_pub = t_now + kappa * elapsed`. Ở `kappa = 1` (laptop chạy thời gian thực), 250 ms tính toán chỉ làm trễ 0,25 s,
   trong khi slack deadline tính bằng phút. Vì vậy chi phí trễ gần như bằng 0 và AnytimeSwarm chỉ còn lợi thế tiết
   kiệm tính toán. Paper cũng cho thấy lợi thế rõ nhất ở `kappa = 50`. Nếu chạy Gazebo ở RTF = 1 với nhiệm vụ 300–600 s,
   rất có thể không thấy khác biệt về reward. Thí nghiệm như vậy không kiểm định được giả thuyết.
   Cách xử lý (cần đăng ký trước):
   a) Định nghĩa `kappa` vật lý: `kappa_eff = (thời gian nhiệm vụ trôi qua trong lúc tính) / (thời gian CPU tính)`.
      Chạy PX4/Gazebo nhanh hơn thời gian thực bằng `PX4_SIM_SPEED_FACTOR` (lockstep), khi đó `kappa_eff ≈ RTF đo được`.
   b) Đo độ trễ đầu-cuối thật `T_total` (queue + repair + search + serialization + DDS + ACK của PX4) và đưa vào.
   c) Mô phỏng CPU onboard chậm hơn (giới hạn 1 nhân bằng `taskset`, hạ tần số) như kịch bản S4.
   d) Rút gọn thang thời gian nhiệm vụ theo tỉ lệ không thứ nguyên (mục 1.3) để slack không quá lớn so với độ trễ.
4. Ngữ nghĩa thực thi phải giống paper. Executor gốc khóa 1 task đang làm (commit horizon = 1); UAV rảnh phải chờ đến
   lúc phát hành kế hoạch; task không còn khả thi lúc phát hành bị trả về hàng chờ ("dropped by delay"); sự kiện đến
   khi planner đang bận thì xếp hàng. Route executor ROS 2 phải làm đúng như vậy cho mọi phương pháp, nếu không sẽ so
   sánh sai với bản hội nghị.
5. Thang không gian. Thế giới 200 × 200 m trong hướng dẫn quá nhỏ so với bản gốc (10 km, 10–16 m/s): thời gian bay giữa
   task chỉ còn vài giây, bài toán gần như không còn đánh đổi. Nên giữ các tỉ lệ không thứ nguyên của bản gốc
   (thời gian bay trung bình / cửa sổ deadline, service / cửa sổ, số task / UAV, tải đủ để completion 73–90%)
   thay vì giữ kích thước tuyệt đối. Ví dụ khởi điểm cho X500: bản đồ 800 × 800 m, tốc độ 5–8 m/s, service 10–30 s,
   cửa sổ 60–200 s, horizon 600 s, 3 UAV / 15 task. Hiệu chỉnh trên seed dev bằng tầng B trước khi lên Gazebo.
6. Zero-shot của predictor. 11 đặc trưng trong `controller/features.py` (log_elapsed, log_iters, gain_5ms, gain_20ms,
   gain_half, log_since_impr, ...). Cần kiểm tra đặc trưng nào phụ thuộc thang (đơn vị mét, reward tuyệt đối) trước
   khi nói zero-shot. Nếu có, chuẩn hóa theo thang và báo cáo đó là thay đổi.
7. Năng lượng. Mô hình gốc tính bằng mét bay. Gazebo/PX4 SITL có pin mô phỏng (tham số `SIM_BAT_*`) nhưng không phải
   mô hình tiêu thụ thật. Báo cáo là "energy proxy", ghi rõ.
8. Tầng B. Hướng dẫn đặt simulator kinematic trong ROS 2. Chạy 40 UAV × 30 seed × 6 phương pháp × nhiều mức trễ ở thời
   gian thực ROS 2 sẽ mất hàng tuần (mỗi nhiệm vụ 30 phút). Đề xuất: tầng B là simulator Python liên tục theo thời gian
   ảo (mở rộng `executor.py`: gia tốc, nhiễu vận tốc, gió, phân phối trễ truyền thông đo từ tầng C), chạy ngoài ROS,
   nhanh và tất định theo seed. ROS 2 dùng cho tầng C và để đo phân phối trễ. Như vậy tầng B vẫn dùng cùng planner và
   cùng gói metric.
9. Phần cứng. WSL thấy 7,7 GB RAM (mặc định 50% của 16 GB) và 2 GB swap. Đủ cho build có giới hạn số job và 1–3 UAV
   headless. Nếu thiếu RAM khi chạy 3 UAV, tạo `C:\Users\highp\.wslconfig` với `memory=12GB`, `swap=8GB`,
   `swapFile=D:\\WSL\\swap.vhdx`. File này cũng áp dụng cho VM của docker-desktop, nên chỉ làm khi cần và có đồng ý.
10. Baseline. Các biến thể đã có sẵn trong `methods.py`: `alns_fixed`, `alns_stagnation`, `anytime_online`
    (w/o learned predictor), `anytime_nodelay` (w/o delay cost), `anytime_noffr` (w/o FFR), `regret_repair`.
    Cần thêm: contextual adaptive-budget (chọn B ∈ {10, 20, 50, 100, 250} ms theo đặc trưng snapshot, học trên dev bằng
    hạ tầng `offline.py` có sẵn) và risk-aware delay cost (chỉ khi G4 cho thấy cần).

## 2. Kiến trúc

```
Windows 11 ── WSL2 Ubuntu 24.04 (D:\WSL\Ubuntu-24.04)
               ├── ROS 2 Jazzy, Gazebo Harmonic (ros_gz)
               ├── ~/PX4-Autopilot (v1.17.0, SITL, gz_x500)
               ├── ~/px4_ros_ws   (px4_msgs release/1.17, Micro-XRCE-DDS-Agent v2.4.3)
               └── ~/atswarm_ws   (các gói atswarm_*, src liên kết tới D:\...\AnytimeSwarm_Journal\ros2_ws\src)

AnytimeSwarm_Journal\
  original\          bản chép code hội nghị + MANIFEST.sha256 (không sửa)
  setup\             script cài đặt 01–05 + logs\
  docs\              kế hoạch, protocol, log
  journal_core\      (G3) planner journal: import từ original, thêm adapter, kinematic sim
  ros2_ws\src\       (G2–G3) atswarm_interfaces, atswarm_planner, atswarm_mission_manager,
                     atswarm_route_executor, atswarm_px4_adapter, atswarm_logger
  simulation\        Gazebo world, tham số xe, kịch bản sự kiện
  experiments\       configs YAML, seed đông lạnh, runner, manifest
  results\           raw, processed, figures, tables
```

Điểm nối planner: `anytimeswarm.algorithms.methods.solve(method, P, old_routes, budget_ms, cfg, seed, predictor, kappa)`
nhận một `Problem` (snapshot) và trả `solution.routes`, `elapsed_ms`, `iters`, `stop_reason`. Node `atswarm_planner`
chỉ cần dựng `Problem` từ trạng thái fleet giống `MissionExecutor.snapshot()` rồi gọi `solve`. Planner chạy ở process
riêng; route executor giữ luồng `OffboardControlMode` ≥ 2 Hz (dùng 10 Hz) trong lúc planner tính.

Đồng hồ: thời gian tính đo bằng `time.perf_counter_ns()` (monotonic wall clock), thời gian nhiệm vụ đo bằng `/clock`
của Gazebo. Logger ghi cả hai cùng RTF.

## 3. Quyết định đã chốt (27/10/2026)

| # | Câu hỏi | Quyết định | Lý do |
|---|---|---|---|
| D1 | E0 tái lập | Chạy lại đầy đủ dev 0–9 trên Linux. Chạy lại test2 2000–2029 một lần, chỉ để kiểm tra lời giải trùng (không tune, không chọn tham số) | Tái lập trên test là kiểm tra code, không phải đánh giá mới; số liệu journal lấy từ seed mới |
| D2 | Seed held-out journal | 3000–3029 (tầng B), 4000–4029 (tầng C), ghi vào config đông lạnh trước khi chạy | ba tập test cũ đã nhìn kết quả |
| D3 | kappa vật lý | `kappa_eff` = thời gian nhiệm vụ trôi / thời gian CPU, tạo bằng (a) speed factor PX4/Gazebo, (b) độ trễ đo được, (c) CPU onboard chậm; các mức đăng ký trước sau pilot | ở RTF = 1 chi phí trễ ≈ 0, thí nghiệm sẽ vô nghĩa |
| D4 | Thang nhiệm vụ Gazebo | giữ tỉ lệ không thứ nguyên của bản gốc | bản đồ 200 m làm mất đánh đổi |
| D5 | `.wslconfig` | chưa tạo. Chỉ tạo khi chạy 3 UAV có GUI bị thiếu RAM | file này cũng áp dụng cho docker-desktop |
| D6 | Git | nên `git init` cho `AnytimeSwarm_Journal` (người dùng tự commit hoặc yêu cầu) | manifest cần commit hash |
| D7 | Đích journal | Robotics and Autonomous Systems trước; nếu phần tối ưu đủ sâu, xem xét journal về tối ưu/vận trù | giữ như hướng dẫn |

## 3b. Thứ tự làm tối ưu

Rủi ro lớn nhất không nằm ở phần kỹ thuật ROS. Nó nằm ở câu hỏi khoa học: khi có thực thi liên tục, nhiễu và độ trễ thật,
AnytimeSwarm còn hơn các baseline không. Câu hỏi này trả lời được rẻ ở tầng B (Python, chạy nhanh). Vì vậy thứ tự là:

1. G0 tái lập bản gốc trên Linux. Đồng thời G2 thực hành bay tay (đã có demo Offboard 1 và 2 UAV).
2. Pilot tầng B trên seed dev: thêm gia tốc, nhiễu, trễ vào executor; quét `kappa_eff`.
   Go/No-Go khoa học: ở ít nhất một vùng `kappa_eff` hợp lý về vật lý, AnytimeSwarm có regret hoặc reward tốt hơn
   alns_fixed ở cùng compute với CI 95% không chứa 0 trên seed dev. Nếu No-Go, chuyển trọng tâm sang execution-aware
   (risk-aware delay cost) trước khi đầu tư tầng C.
3. G2/G3 tích hợp ROS 2 (adapter, route executor, planner node); đo phân phối độ trễ thật.
4. G4 pilot tầng C, chốt config, đăng ký trước protocol.
5. G5 thí nghiệm chính một lần trên seed mới, rồi G6 kiểm toán và viết bài.

## 4. Các chặng (gate) và tiêu chí hoàn thành

### G1 — Môi trường (đang làm ngày 27/10)
1. WSL2 Ubuntu 24.04 trên ổ D, user `highp`. Xong.
2. ROS 2 Jazzy + ros_gz; talker/listener chạy; `gz sim -s -r shapes.sdf` chạy headless.
3. PX4 v1.17.0 build `px4_sitl`; `HEADLESS=1 make px4_sitl gz_x500` cất cánh được.
4. `px4_ros_ws` build; `MicroXRCEAgent udp4 -p 8888`; `ros2 topic echo /fmu/out/vehicle_odometry` có dữ liệu.
5. `setup/05_smoke_test.sh 1` rồi `05_smoke_test.sh 2`: mỗi UAV có namespace riêng (`/px4_1/fmu/...`), ghi RTF.
Tiêu chí: log trong `setup/logs/` cho thấy cả năm mục đạt.

Kết quả 27/10/2026 (đạt 5/5, trừ cất cánh — để sang G2 cùng Offboard):
- ROS 2 Jazzy, ros_gz, gz-sim 8.15.0 (Harmonic). talker/listener OK. `gz sim -s -r shapes.sdf` RTF 1,00.
- PX4 `v1.17.0` build `px4_sitl_default` 1141/1141 (`ubuntu.sh --no-nuttx`).
- `px4_msgs` release/1.17 (235 msg) + Micro-XRCE-DDS-Agent v2.4.3 build trong 6 phút 52 giây.
- 1 UAV: `/px4_1/fmu/out/vehicle_odometry` có dữ liệu, RTF 1,00.
- 2 UAV: `/px4_1` và `/px4_2`, mỗi bên 65 topic, RTF 1,00, RAM WSL dùng < 1 GB ngoài cache.
- Lưu ý cho adapter: với `px4 -i N` namespace là `/px4_N/fmu/...` (không phải `/fmu/...`); một số topic có hậu tố
  phiên bản: `vehicle_status_v1`, `vehicle_local_position_v1`, `battery_status_v1`, `home_position_v1`.

### G0 — Tái lập bản gốc (sau G1, không cần ROS)
1. Tạo venv Linux trong WSL, `pip install -r original/requirements.txt`, ghi phiên bản.
2. `pytest original/tests` (20 test) trên cả Windows và Linux.
3. Chạy dev split (02 → 05) và so với `results/` gốc: lời giải ở cùng số vòng lặp phải trùng (ALNS cooling theo vòng
   lặp nên quỹ đạo tất định); runtime khác thì giải thích bằng CPU/OS.
4. Viết validator khả thi độc lập (không import `Problem.schedule`) kiểm tra deadline, năng lượng, reserve, thời gian.
Tiêu chí: báo cáo `docs/02_REPRODUCTION.md`, toàn bộ lời giải qua validator.

Tiến độ 27/10:
- Môi trường: `~/venvs/atswarm311` (CPython 3.11.9, đúng phiên bản gói như bản hội nghị) và `~/venvs/atswarm`
  (Python 3.12 của ROS + cùng phiên bản gói, thấy rclpy). Unit test 22/22 đạt.
- Stage A (tất định, `tools/g0_stage_a.sh`, `results/g0/stage_a.txt`): 90 kịch bản dev giống bản gốc đến từng bit;
  531 snapshot giống 99,978% số lá, mọi khác biệt (315) nằm ở trường `energy`, lệch 1 ulp (≤ 7e-12), do libm
  Windows/Linux; Python 3.11 và 3.12 trên Linux cho kết quả giống hệt nhau.
- Stage B (có đo thời gian, `tools/g0_stage_b.sh`, chạy dưới guard Linux `tools/run_guarded.py`): đang chạy.

### G2 — Multi-UAV SITL + điều khiển
1. Offboard cho 1 UAV, ENU ↔ NED đúng. Xong ngày 27/10: `demo/offboard_waypoints.py`, 1 UAV và 2 UAV bay hết route,
   hạ cánh, disarm (log `setup/logs/demo_*.txt`). Cần `NAV_DLL_ACT=0` vì airframe 4001 đặt mặc định 2 (đòi có GCS);
   biến môi trường `PX4_PARAM_NAV_DLL_ACT` không có tác dụng vì `param set-default` của airframe ghi đè.
2. `atswarm_px4_adapter`: arm, takeoff, goto waypoint, hold service, RTL, land; heartbeat 10 Hz.
3. `atswarm_route_executor`: nhận route, phát waypoint, báo hoàn thành task theo vị trí thật (bán kính chấp nhận).
4. `atswarm_mission_manager`: phát `NEW_TASK`, `UAV_FAILURE`, `DEADLINE_CHANGE` theo trace có seed.
5. `atswarm_interfaces`: msg/action `MissionEvent`, `FleetState`, `ReplanRequest`, `ReplanResult` (có `event_id`,
   `plan_version`, `stop_reason`, `predicted_gain`, `delay_cost`).
Tiêu chí: 2 UAV bay hết một route cố định, log có thời điểm đến thật.

### G3 — Tích hợp planner
1. `journal_core/adapter.py`: FleetState → `Problem` (giống `MissionExecutor.snapshot`), routes → waypoint.
2. `atswarm_planner` gọi `solve`; quy tắc sự kiện đến khi đang tính: xếp hàng (như bản gốc), áp dụng cho mọi phương pháp;
   `plan_version` chặn kế hoạch cũ.
3. Kiểm tra: UAV đang làm task đã khóa vẫn bay trong lúc planner tính; heartbeat không gián đoạn.
4. Tầng B: `journal_core/kinematic_executor.py` + `journal_core/execution.py` mở rộng executor gốc (gia/giảm tốc
   hình thang, gió hằng theo nhiệm vụ, sai số tốc độ theo cặp (UAV, task), sai số thời gian phục vụ, trễ phát hành
   lognormal + mất gói/timeout), chạy thời gian ảo. Xong 27/10: `tests/test_kinematic.py` 9/9, trong đó nhiễu = 0 và
   trễ = 0 cho kết quả trùng executor gốc. Nhiễu dùng số ngẫu nhiên chung (CRN) giữa các phương pháp. Planner chỉ thấy
   telemetry: UAV đang bay được báo bằng ước lượng danh định từ vị trí thật, không thấy tương lai.
   Quan sát sơ bộ (kiểm tra sanity, planner tất định, 2 nhiệm vụ medium): mức nhiễu "low" đã làm utility giảm từ
   0,96 xuống 0,82, sai số thời điểm hoàn thành p95 khoảng 50 s, vì sai số tích lũy dọc route giữa hai lần replan
   (replan chỉ khi có sự kiện). Hệ quả cho journal: cần xét thêm replan theo độ lệch (deviation-triggered), khi đó số
   lần gọi planner tăng và việc phân bổ thời gian tính càng quan trọng. Đây là ứng viên đóng góp mới, quyết định sau pilot.
Tiêu chí: một nhiệm vụ 3 UAV/15 task chạy hết vòng kín với AnytimeSwarm và alns_fixed.

### G4 — Pilot (chỉ seed dev)
1. Đo phân phối độ trễ thật trên ROS 2 (T_queue ... T_ack) và RTF khi 1/2/3 UAV, các speed factor.
2. Hiệu chỉnh thang nhiệm vụ Gazebo và mức `kappa_eff` trên seed dev 0–9 để có completion 70–90% và còn dư địa cho search.
3. Chạy mọi phương pháp trên cùng trace; so sánh tầng B và tầng C cùng kịch bản (kiểm tra tầng B có dự đoán đúng tầng C).
4. Đo sai số dự báo thời gian đến (planner vs thực tế) → quyết định có cần risk-aware delay cost không.
Tiêu chí: `configs/frozen_journal_<ngày>.yaml` + protocol đăng ký trước (giả thuyết, metric chính, seed, mức trễ).

### G5 — Thí nghiệm journal (seed held-out, chạy một lần)
1. E1 tầng B: 5/10/20/40 UAV × 3 profile × trễ {0, thấp, cao, burst} × nhiễu {0, thấp, vừa}, 30 seed. Ma trận chính
   và ma trận sensitivity tách riêng.
2. E2 tầng C: 3 UAV, 15–30 seed, các phương pháp: FFR-only, alns_fixed, alns_fixed@matched, alns_stagnation,
   contextual budget, anytime_nodelay, AnytimeSwarm.
3. E3: kịch bản trễ S0–S4 trên tầng B (phân phối lấy từ đo tầng C) và một phần trên tầng C.
4. E4: zero-shot (predictor gốc đóng băng) trước; retrain trên dev journal chỉ là thí nghiệm phụ.
5. Bootstrap theo nhiệm vụ, effect size + CI 95%, báo cáo cả trường hợp AnytimeSwarm thua.
Tiêu chí: bảng A (closed-loop vật lý), B (trễ), C (generalization), D (ablation).

### G6 — Kiểm toán
Manifest (OS, phiên bản ROS/Gazebo/PX4/px4_msgs/agent, commit, phần cứng, seed), rosbag + log PX4 cho tầng C,
kiểm tra không rò rỉ dev/test, kiểm tra lại mọi số liệu trong bài so với file kết quả.

## 5. Rủi ro chính

| Rủi ro | Hệ quả | Giảm thiểu |
|---|---|---|
| kappa_eff ≈ 1 ở Gazebo | không thấy khác biệt reward | speed factor, CPU chậm, thang nhiệm vụ (mục 1.2.3) |
| RTF < 1 khi 3 UAV trên laptop | thời gian nhiệm vụ bị kéo giãn | headless, lockstep, đo và báo cáo RTF; dùng sim time cho deadline |
| 7,7 GB RAM trong WSL | build/3 UAV bị OOM | giới hạn job; `.wslconfig` (D5) |
| Predictor phụ thuộc thang | zero-shot thất bại | kiểm tra đặc trưng ở G0; báo cáo trung thực |
| Lợi thế không tăng theo quy mô (bản XL) | không được claim scale | giữ claim mềm như paper |
| Đầu tư ROS trước khi biết kết quả khoa học | tốn công nếu No-Go | Go/No-Go ở tầng B trước (mục 3b) |
