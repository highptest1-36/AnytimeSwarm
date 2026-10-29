# Protocol đăng ký trước — Nghiên cứu 3 (proposed + dự phòng danh nghĩa)

Viết ngày 29/10/2026, SAU khi có kết quả held-out của nghiên cứu 2 (tầng B 5000–5029, tầng C 6000–6009) và kết quả dev
của nghiên cứu 3, TRƯỚC mọi lượt chạy trên seed held-out 7000–7029. Nghiên cứu 3 là phần mở rộng có tính khám phá, sinh
ra từ một điểm yếu thấy trên held-out của nghiên cứu 2; vì vậy nó được kiểm định lại trên seed mới, chưa từng dùng.
File đóng băng: `results/frozen_study3_sha256.txt` (cùng commit git). Không chỉnh sau khi chạy; mọi thay đổi bắt buộc ghi
vào mục "Sai lệch".

## 1. Động cơ
Nghiên cứu 2: proposed thua đệm cố định 60 s khi nhiễu cao và cửa sổ thời gian ×0,5 (−2,0 pp). Giải thích: deadline hiệu
dụng d~_j của nhiều task rơi trước thời điểm đến sớm nhất có thể, nên planner coi task là vô vọng và bỏ hẳn, dù xe có thể
không còn việc gì tốt hơn.

## 2. Phương pháp (journal_core/study3.py, experiments/b3_grid.py)
proposed~fb=nominal: như proposed của nghiên cứu 2 (cùng z, mô hình sai số, quy tắc dừng, trigger định kỳ 60 s), trừ một
điểm. Task nào vô vọng dưới d~_j nhưng vẫn khả thi dưới deadline danh nghĩa d_j thì giữ deadline d_j (task dự phòng).
Task được bảo vệ giữ nguyên d~_j, nên task dự phòng chỉ được chèn vào phần trống mà các task được bảo vệ để lại.
study2.py đóng băng và không bị sửa; study3.py bọc nó.

## 3. Lựa chọn trên dev (seed 0–9, results/tier_b/dev3_fallback.csv, log dev3_fallback_log.txt)
Ứng viên: fb=nominal, fb=60 (deadline d_j − 60 s cho task dự phòng). Quy tắc chọn đặt trước: biến thể có utility trung
bình dev cao nhất; Go nếu nó cải thiện vùng nhiễu cao/cửa sổ ×0,5 so với proposed và không thua quá 0,3 pp ở vùng nào.
Kết quả dev (fallback trừ proposed, pp): fb=nominal +2,28 [+1,51; +3,10] gộp; mid×1 +0,95, mid×0,5 +2,25, high×1 +0,50,
high×0,5 +5,42; so với đệm 60 s ở high×0,5 +4,18. fb=60: +0,54 gộp, high×0,5 +2,17. → chọn fb=nominal, Go.
Đánh đổi thấy trên dev: nhiều task trễ hơn (8,5 so với 5,8 mỗi nhiệm vụ) và mất 1,65 task do kế hoạch đến muộn (proposed 0).

## 4. Ma trận (experiments/configs/S3_B.yaml)
Tầng B, seed held-out MỚI 7000–7029 × {small, medium, large} × {arrivals, failures, deadlines} = 270 nhiệm vụ; nhiễu
{mid, high}; độ trễ high; κ_B {10, 50, 200}; cửa sổ ×{1; 0,5} → 12 cấu hình; 5 phương pháp: proposed~fb=nominal,
proposed, alns_fixed@40~buf=60, alns_fixed@40 (cả bốn trigger định kỳ 60 s), alns_fixed@40+event (thông thường).
Tầng C không chạy lại cho nghiên cứu 3 (giới hạn, ghi trong bài).

## 5. Giả thuyết và kiểm định (experiments/analyze_study3.py)
Như nghiên cứu 2: chỉ số chính utility rate; mỗi nhiệm vụ lấy trung bình chênh lệch qua các cấu hình của ô; bootstrap cặp
10 000 lần, CI 95% percentile, p hai phía. Họ chính, Holm trên 4 phép, α = 0,05 (fallback trừ phương pháp):
- H5: > proposed, gộp 12 cấu hình.
- H6: > đệm cố định 60 s, vùng nhiễu high, cửa sổ ×0,5 (3 cấu hình: 3 κ × độ trễ high).
- H7: > alns_fixed@40, gộp.
- H8: > đệm cố định 60 s, gộp.
Mô tả: chênh lệch theo vùng (4 vùng), so với planner thông thường, số task trễ/mất/bỏ, ms/lần gọi; lặp lại kết quả nghiên
cứu 2 trên seed mới (proposed trừ đệm, proposed trừ 40 ms, theo vùng). Kết quả âm được báo cáo như kết quả dương. Không
loại nhiệm vụ nào.

## 6. Đo thời gian và máy
Như nghiên cứu 2: laptop i7-11800H, WSL2, 4 worker, phương pháp xen kẽ trong cùng cấu hình; không chạy song song với tầng
C hay lưới khác. Máy đồng thời được dùng cho trình duyệt (ghi nhận; ms/lần gọi chỉ so sánh tương đối trong cùng lượt).

## 7. Sai lệch
(trống khi đóng băng)
