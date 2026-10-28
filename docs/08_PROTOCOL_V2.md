# Protocol đăng ký trước — Nghiên cứu 2 (proposed replanner vs. baseline từ tài liệu)

Viết ngày 28/10/2026, TRƯỚC mọi lượt chạy trên seed held-out của nghiên cứu 2. Mọi lựa chọn dựa trên seed dev (tầng B 0–9,
tầng C 0–2) và trên kết quả nghiên cứu 1 (seed 3000–3029 / 4000–4009, chỉ dùng để định hướng, không tinh chỉnh tham số).
File đóng băng: `results/frozen_study2_sha256.txt` (cùng commit git). Không chỉnh sau khi chạy; mọi thay đổi bắt buộc ghi
vào mục "Sai lệch".

## 1. Phương pháp đề xuất (proposed)
- Mô hình lập kế hoạch có ràng buộc xác suất: thời điểm hoàn thành dự kiến f_j phải thỏa f_j + m(h_j) + z s(h_j) ≤ d_j với
  h_j = f_j − t0; vì m, s tuyến tính, tương đương deadline hiệu dụng d~_j = t0 + (d_j − t0 − b0 − z s0)/(1 + b1 + z s1)
  (journal_core/study2.py: buffered_problem). Mô hình sai số: hiệu chỉnh trên dev (models/error_model_dev.json; tầng C
  models/error_model_tierc_dev.json). z theo mức nhiễu, chọn trên dev (results/tier_b/dev2b_explore.csv): mid 0,5; high 0.
- Dừng anytime: bộ dự đoán học được (đóng băng từ bản hội nghị) so với chi phí trễ theo rủi ro của độ lệch còn lại quanh
  deadline hiệu dụng + độ trễ truyền kỳ vọng + chi phí tính μH.
- Trigger: sự kiện, và ít nhất mỗi 60 s (thời gian tầng B).
- FFR + ALNS: không đổi so với bản hội nghị (cùng toán tử, tham số, seed).

## 2. Baseline (đều dùng cùng FFR + ALNS, cùng trigger định kỳ 60 s trừ khi ghi khác)
| Mã | Mô tả | Nguồn |
|---|---|---|
| regret_repair | chỉ sửa kế hoạch, không tìm kiếm | sàn |
| alns_fixed | ngân sách cố định 250 ms | Ropke & Pisinger 2006 |
| alns_fixed@40 | ngân sách cố định 40 ms (bằng tính toán TB của AnytimeSwarm trên dev hội nghị) | |
| alns_scaled~ms=1 | ngân sách tỉ lệ số task mở (1 ms/task, chọn trên dev trong {0,5; 1; 2}) | |
| alns_stagnation | dừng khi không cải thiện trong 20% ngân sách | |
| profile | performance profile tĩnh (dev) so với chi phí thời gian | Boddy & Dean 1994; Zilberstein 1996 |
| online_curve | dự báo hiệu năng trực tuyến (khớp a − b e^{−ct}) so với chi phí thời gian | Svegliato et al. 2018 |
| anytime | AnytimeSwarm (bản hội nghị) | |
| anytime_risk | AnytimeSwarm-R (nghiên cứu 1) | |
| alns_fixed@40~buf=60 | đệm thời gian cố định 60 s (chọn trên dev trong {30, 60, 120}) | robust buffer, VRPTW bền vững |
| alns_fixed@40+event | planner thông thường: ngân sách cố định, chỉ replan theo sự kiện | |
Ablation: proposed+event (bỏ trigger định kỳ); alns_fixed@40~z=auto (mô hình đề xuất, dừng cố định 40 ms);
proposed~z=0 (chỉ hiệu chỉnh sai số trung bình).

## 3. Ma trận
- Tầng B chính (experiments/configs/S2_B_main.yaml): seed 5000–5029 × {small, medium, large} × {arrivals, failures,
  deadlines} = 270 nhiệm vụ; nhiễu {mid, high}; độ trễ high; κ_B {10, 50, 200}; cửa sổ thời gian ×{1; 0,5} → 12 cấu hình;
  15 phương pháp.
- Tầng B đối chứng tầng C (S2_B_gz.yaml): 30 nhiệm vụ gz (seed 6000–6009), mid, κ_B 50, 4 phương pháp như tầng C.
- Tầng C: 30 nhiệm vụ (seed 6000–6009 × 3 profile), 3 UAV X500, PX4 SITL + Gazebo, mid, κ_B 50, F = 2; phương pháp:
  proposed, ALNS 40 ms, đệm cố định 60 s (cả ba trigger định kỳ 60 s), ALNS 40 ms chỉ theo sự kiện.
  Lượt có RTF ngoài [1,6; 2,2] hoặc lỗi khởi động: chạy lại MỘT lần cùng seed, giữ bản gốc (đăng ký trước).

## 4. Giả thuyết và kiểm định
Chỉ số chính: utility rate. Đơn vị lấy mẫu: nhiệm vụ; với mỗi nhiệm vụ lấy trung bình chênh lệch qua các cấu hình của
ma trận, bootstrap cặp 10 000 lần, CI 95% percentile, p hai phía.
- H1 (chính, tầng B): proposed > mỗi baseline trong {alns_fixed@40, alns_scaled, online_curve, profile, anytime_risk,
  alns_fixed@40~buf=60} (đều trigger định kỳ). Holm trên 6 phép, α = 0,05.
- H2 (tầng B): proposed > alns_fixed@40+event (planner thông thường).
- H3 (vai trò quy tắc dừng, tầng B): trong cùng mô hình và trigger, proposed so với alns_fixed@40~z=auto: tương đương
  với biên ±0,5 pp (TOST, hai CI 90%). Mô tả thêm: tại κ_B = 200, proposed so với alns_fixed 250 ms.
- H4 (tầng C): proposed > alns_fixed@40 (định kỳ) và > alns_fixed@40+event. Holm trên 2. Báo cáo thêm: đệm cố định,
  thứ hạng tầng B (gz) vs tầng C, tương quan theo nhiệm vụ.
Mô tả (không kiểm định chính thức): hiệu ứng theo κ, cửa sổ, mức nhiễu, quy mô; số lần gọi và ms/lần gọi; ablation.
Kết quả âm được báo cáo như kết quả dương. Không loại nhiệm vụ nào.

## 5. Đo thời gian và máy
Như protocol 1: laptop i7-11800H, WSL2, Python 3.12.3, 4 worker tầng B, phương pháp xen kẽ trong cùng cấu hình; tầng B và
tầng C không chạy song song; guard RAVEN/PX4.

## 6. Sai lệch
(trống khi đóng băng)
