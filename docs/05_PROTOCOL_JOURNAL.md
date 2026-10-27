# Protocol đăng ký trước cho thí nghiệm chính của journal

Viết ngày 28/10/2026, TRƯỚC khi chạy bất kỳ seed held-out nào. Mọi lựa chọn dưới đây dựa trên seed dev
(tầng B 0–9, tầng C 0–2). Config đóng băng: `experiments/configs/frozen_journal.yaml` (sha256 ghi trong
`results/frozen_journal_sha256.txt` cùng commit git). Không chỉnh gì sau khi chạy held-out; mọi thay đổi bắt buộc
được ghi thành "deviation from protocol" kèm lý do.

## 1. Phương pháp so sánh

| Tên | Mô tả | Vai trò |
|---|---|---|
| regret_repair | chỉ feasibility-first repair, không search | sàn |
| alns_fixed | ALNS ngân sách cố định 250 ms | baseline truyền thống |
| alns_fixed@40 | ALNS 40 ms (bằng compute trung bình của AnytimeSwarm trên dev hội nghị) | baseline cùng compute |
| alns_stagnation | ALNS dừng khi không cải thiện trong 20% ngân sách | baseline dừng sớm cổ điển |
| anytime | AnytimeSwarm bản hội nghị, đóng băng (zero-shot) | phương pháp gốc |
| anytime_nodelay | AnytimeSwarm bỏ chi phí trễ | ablation |
| anytime_risk | AnytimeSwarm-R: chi phí trễ theo rủi ro (mô hình sai số hiệu chỉnh trên dev + độ trễ kỳ vọng) | phương pháp mới |
| anytime_risk~zero | AnytimeSwarm-R với mô hình sai số bằng 0 (chỉ còn phần độ trễ) | ablation |
| anytime_risk~<level> | AnytimeSwarm-R với mô hình sai số của mức nhiễu khác | độ nhạy khi mô hình sai |

Mọi biến thể ALNS dùng chung operator, tham số và seed, nên đi cùng một quỹ đạo tìm kiếm và chỉ khác thời điểm dừng.
Predictor, μ = 1e-5, H = 10 ms, check 5 ms: giữ nguyên bản hội nghị.

## 2. Giả thuyết và phép kiểm định

Chỉ số chính: utility rate (tổng thưởng task phục vụ kịp deadline / tổng thưởng mọi task của nhiệm vụ).
Đơn vị lấy mẫu lại: nhiệm vụ (bootstrap cặp, 10 000 lần, CI 95% percentile).

- H1 (chính, tầng B). Trên ma trận chính, AnytimeSwarm-R có utility cao hơn (a) alns_fixed@40, (b) anytime,
  (c) alns_stagnation. Kiểm định gộp: với mỗi nhiệm vụ, lấy trung bình chênh lệch utility qua 16 cấu hình của ma trận
  chính, rồi bootstrap trên 270 nhiệm vụ. Ba phép so sánh hiệu chỉnh Holm (alpha 0,05). Báo cáo thêm từng cấu hình
  (mô tả, không hiệu chỉnh) và số cấu hình thắng/hòa/thua.
- H2 (compute). Thời gian tính trung bình mỗi lần gọi của AnytimeSwarm-R không lớn hơn của anytime (kiểm định gộp
  như trên, một phía).
- H3 (trigger). Replan định kỳ 60 s (thời gian tầng B) cho utility cao hơn chỉ replan theo sự kiện, với từng phương
  pháp (gộp theo nhiệm vụ). Mô tả: lợi thế của AnytimeSwarm-R còn hay không dưới từng trigger.
- H4 (vật lý, tầng C). Với PX4 + Gazebo, cùng nhiễu (CRN), AnytimeSwarm-R có utility cao hơn alns_fixed@40 và anytime
  (bootstrap trên 30 nhiệm vụ, Holm). Báo cáo thêm: thứ hạng phương pháp tầng B (cùng kịch bản, thang gz) và tầng C
  có nhất quán không (hệ số Kendall giữa trung bình theo phương pháp; tương quan utility theo nhiệm vụ).
- H5 (quy mô). Ở 40 UAV / 280 task (tầng B, XL), so sánh như H1 trên ma trận XL. Không đặt kỳ vọng tăng theo quy mô.

Kết quả âm được báo cáo như kết quả dương. Không loại nhiệm vụ nào.

## 3. Ma trận thí nghiệm

### Tầng B — ma trận chính (H1–H3)
- Seed held-out 3000–3029; quy mô small (5/25), medium (10/50), large (20/140); profile arrivals, failures, deadlines
  → 270 nhiệm vụ.
- Nhiễu thực thi {low, mid}; độ trễ {none, high}; κ_B {10, 50}; trigger {event, periodic:60} → 16 cấu hình.
- Phương pháp: regret_repair, alns_fixed, alns_fixed@40, alns_stagnation, anytime, anytime_nodelay, anytime_risk,
  anytime_risk~zero.

### Tầng B — quy mô XL (H5)
- 40 UAV / 280 task, seed 3000–3029 × 3 profile = 90 nhiệm vụ; nhiễu mid; độ trễ {none, high}; κ_B {10, 50};
  trigger event; phương pháp alns_fixed, alns_fixed@40, alns_stagnation, anytime, anytime_risk.

### Tầng B — độ nhạy (mô tả)
- Nhiễu high (ngoài dải hiệu chỉnh), κ_B = 1 (máy nhanh), trigger deviation:30, mô hình sai số sai
  (anytime_risk~low dưới nhiễu mid, anytime_risk~mid dưới nhiễu low), trên quy mô small/medium/large, seed held-out.

### Tầng C — PX4 SITL + Gazebo (H4)
- Kịch bản gz (3 UAV X500, 15 task, thế giới 1 km, nhiệm vụ 450 s; tầng B thu nhỏ với S_X = 0,1, S_T = 0,25, giữ
  mọi tỉ lệ không thứ nguyên). Seed held-out 4000–4009 × 3 profile = 30 nhiệm vụ.
- Nhiễu mid (CRN như tầng B, gió thu nhỏ theo S_X/S_T), κ_B = 50 (κ_C = 12,5), trigger event, PX4_SIM_SPEED_FACTOR = 2.
- Phương pháp: alns_fixed, alns_fixed@40, anytime, anytime_risk (mô hình sai số và độ trễ hiệu chỉnh trên chuyến bay
  dev tầng C).
- Tiêu chí hợp lệ: RTF đo được trong [0,8F; 1,1F]; nhiệm vụ lỗi kỹ thuật (crash PX4/Gazebo) được chạy lại một lần với
  cùng seed và ghi vào log; không có lựa chọn theo kết quả.

## 4. Đo thời gian và máy

Laptop i7-11800H (8 nhân), WSL2 Ubuntu 24.04, Python 3.12.3, gói ghim phiên bản (README). Tầng B chạy 4 worker song
song; trong mỗi cấu hình mọi phương pháp chịu cùng tải máy (xếp xen kẽ). Guard tạm dừng khi RAVEN (Windows) hoặc
PX4/Gazebo (WSL) chạy. Tầng B và tầng C không chạy cùng lúc. Báo cáo tốc độ tìm kiếm (vòng ALNS/ms) để quy đổi máy.
