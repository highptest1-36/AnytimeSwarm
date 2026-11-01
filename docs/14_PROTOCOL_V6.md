# Protocol đăng ký trước — Nghiên cứu 6 (CBBA làm baseline đã công bố; fallback cost-aware cho moment propagation)

Viết ngày 01/11/2026, SAU kết quả held-out của nghiên cứu 1–5 và các lượt dev của nghiên cứu 6, TRƯỚC mọi lượt chạy trên
seed held-out mới 12000–12029 (tầng B). File đóng băng: `results/frozen_study6_sha256.txt` (cùng commit git). Không chỉnh
sau khi chạy; mọi thay đổi bắt buộc ghi vào mục "Sai lệch".

## 1. Động cơ
Đánh giá sau nghiên cứu 5 nêu hai chỗ reviewer dễ hỏi:
1. Các baseline chủ yếu là biến thể cài lại trên cùng một search (ALNS). Chưa so với một thuật toán phân công nhiệm vụ đa
   UAV đã công bố và được dùng rộng rãi.
2. Fallback cost-aware mới chỉ được kiểm trên mô hình dạng đóng. Nếu lập luận "có xác suất đúng hạn thì định giá được việc
   đến trễ" là tổng quát, quy tắc phải cải thiện được cả moment propagation (Ehmke và cộng sự 2015), như fallback danh nghĩa
   đã làm ở nghiên cứu 4 (H11).

## 2. Phương pháp (journal_core/study6.py, experiments/b6_grid.py; unit test tests/test_study6.py, 7 test)
CBBA (Choi, Brunet và How, IEEE T-RO 2009), cài lại:
- pha xây bundle: mỗi agent lần lượt thêm task có điểm biên lớn nhất trong số task nó trả giá cao hơn người đang thắng;
  điểm biên = mức tăng lớn nhất của giá trị tuyến (P.route_value: thưởng − chi phí quãng đường − phạt đổi phân công) qua
  mọi vị trí chèn khả thi;
- pha đồng thuận (mạng liên lạc đầy đủ): giá cao nhất thắng (hòa thì agent chỉ số nhỏ); agent bị trả giá cao hơn nhả task
  đó và mọi task nó thêm sau task đó;
- bid warping (Johnson, Choi, Ponda và How, CDC 2012): giá thầu không vượt giá thầu trước trong cùng bundle. Cần thiết vì
  với cửa sổ thời gian, điểm biên không giảm dần; trên dev, bản không warping không hội tụ trong 200 vòng ở một số kịch bản;
- chạy lại từ đầu mỗi lần gọi; dừng khi hội tụ hoặc hết ngân sách cứng 250 ms; thời gian tính được đo như mọi phương pháp
  (độ trễ công bố κ_B τ + L);
- hai trigger: định kỳ 60 s (như các phương pháp khác) và theo sự kiện (cách dùng thông thường của CBBA).

CBBA trên mô hình đề xuất: cùng CBBA, chạy trên deadline của fallback cost-aware (λ = 1, z của nghiên cứu 4). Kiểm tra mô
hình có cải thiện được một thuật toán phân công đã công bố hay không.

Moment propagation với fallback cost-aware: task được bảo vệ ở z_p = max(z_MP, z_λ); task bị moment propagation bỏ được
nhận nếu thời điểm xong danh nghĩa ≤ d và E[F] + z_λ sd[F] ≤ d. z_MP của nghiên cứu 4 (1 ở mid, 0,5 ở high). λ = 0 trùng
fallback danh nghĩa (unit test).

Không tham số nào được tune trong nghiên cứu 6.

## 3. Lượt dev (seed 0–9; results/tier_b/dev6.csv cùng dev5_tune.csv; experiments/analyze_study6.py --dev)
Ma trận như nghiên cứu 4–5, 4 phương pháp mới × 1 080 lượt. CBBA hội tụ ở mọi lần gọi, trung bình 2,7 vòng và 5,5 ms
mỗi lần gọi (theo sự kiện 15,2 ms vì mỗi lần gọi có nhiều task mới hơn). Hiệu ứng dev ở λ = 1 (điểm %, sd theo nhiệm vụ):
- đề xuất trừ CBBA: +13,01 (sd 6,61); ở λ = 0: +5,10 (sd 4,93);
- CBBA trên mô hình đề xuất trừ CBBA: +11,66 (sd 6,80); ở λ = 0: +3,17;
- MP cost-aware trừ MP fallback danh nghĩa: +2,81 (sd 5,06), cần khoảng 25 nhiệm vụ cho power 80%;
- MP cost-aware trừ MP không fallback: +3,16 (sd 4,95), khoảng 19 nhiệm vụ.
Ở λ = 0, MP cost-aware kém MP fallback danh nghĩa 2,80 (đúng như thiết kế: quy tắc trả utility lấy độ đúng hạn).

## 4. Ma trận tầng B (experiments/configs/S6_B.yaml)
Seed held-out MỚI 12000–12029 × {small, medium, large} × {arrivals, failures, deadlines} = 270 nhiệm vụ; 12 cấu hình như
nghiên cứu 4–5. 9 phương pháp:
- CA: alns_fixed@40~z=auto4;lam=1+periodic:60 (đề xuất);
- CBBA: cbba+periodic:60; CBBAe: cbba+event;
- CBBACA: cbba~z=auto4;lam=1+periodic:60;
- MPCA: alns_fixed@40~mp=auto;lam=1+periodic:60;
- MP: alns_fixed@40~mp=auto;fb=nominal+periodic:60; MPnf: alns_fixed@40~mp=auto+periodic:60;
- CCfb: alns_fixed@40~z=auto4;fb=nominal+periodic:60; Forty: alns_fixed@40+periodic:60.
Tổng 29 160 lượt, 4 worker. Chạy: tools/run_study6.sh.

## 5. Giả thuyết và kiểm định (experiments/analyze_study6.py)
Như nghiên cứu 2–5: chênh lệch trung bình theo nhiệm vụ qua 12 cấu hình; bootstrap cặp 10 000 lần; CI 95% percentile;
p hai phía. Điểm u_1 (λ = 1).

Họ chính, Holm trên 4 phép, α = 0,05:
- H20: CA > CBBA (định kỳ).
- H21: CBBACA > CBBA (mô hình đề xuất cải thiện một thuật toán phân công đã công bố).
- H22: MPCA > MP (fallback cost-aware tốt hơn fallback danh nghĩa trong moment propagation).
- H23: MPCA > MPnf.

Thứ yếu, mô tả: mọi so sánh ở λ ∈ {0; 0,5; 1; 2} (đặc biệt λ = 0, tức utility của nghiên cứu 1–4); CA so với CBBAe,
CBBACA, MPCA, CCfb, Forty; CBBA so với Forty; theo mức nhiễu và 4 vùng; số task trễ; ms và số vòng mỗi lần gọi.

Quy tắc diễn giải:
- H20 đạt: phương pháp đề xuất tốt hơn một thuật toán phân công đa UAV đã công bố, trong cùng mô phỏng và cùng chi phí
  thời gian tính.
- H21 đạt: lợi ích đến từ mô hình lập kế hoạch, không phụ thuộc vào search.
- H22 và H23 đạt: quy tắc cost-aware là cơ chế tổng quát cho mọi mô hình có xác suất đúng hạn.
- Kết quả âm được báo cáo như kết quả dương. Không loại nhiệm vụ nào.

Lưu ý: CBBA được thiết kế cho phân công phân tán; ở đây nó chạy tập trung với mạng đầy đủ, tức trường hợp thuận lợi nhất
về liên lạc. So sánh vì vậy không nói gì về ưu điểm phân tán của CBBA (khả năng chịu mất liên lạc), mà chỉ về chất lượng
kế hoạch dưới thực thi bất định.

## 6. Đo thời gian và máy
Như nghiên cứu 2–5: laptop i7-11800H, WSL2, 4 worker; các phương pháp xen kẽ trong cùng cấu hình; không chạy song song với
lưới khác.

## 7. Sai lệch
(trống khi đóng băng)

## 8. Kết quả
(trống khi đóng băng)
