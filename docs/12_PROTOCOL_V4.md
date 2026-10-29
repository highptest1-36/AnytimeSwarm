# Protocol đăng ký trước — Nghiên cứu 4 (so sánh mô hình lập kế hoạch, tính tổng quát của fallback, xác nhận tầng C)

Viết ngày 29/10/2026, SAU kết quả held-out của nghiên cứu 1–3 và các lượt dev của nghiên cứu 4, TRƯỚC mọi lượt chạy trên
seed held-out mới 8000–8029 (tầng B) và 9000 trở lên (tầng C). Kế hoạch: docs/11_PLAN_IMPROVE.md. File đóng băng:
`results/frozen_study4_sha256.txt` (cùng commit git). Không chỉnh sau khi chạy; mọi thay đổi bắt buộc ghi vào mục "Sai lệch".

## 1. Động cơ
Ba điểm yếu của bản thảo sau nghiên cứu 3:
1. Chance constraint cho từng khách hàng trong VRPTW đã có trong tài liệu (Li, Tian và Leung 2010; Ehmke, Campbell và
   Urban 2015). Bài chưa so với phương pháp chuẩn, tức lan truyền mô-men dọc tuyến.
2. Chưa tách được phần đóng góp của hình dạng lề (tăng tuyến tính theo thời gian chờ) với phần đóng góp của việc hiệu
   chỉnh từ dữ liệu. Thiếu baseline buffer tỷ lệ c·h.
3. Tầng C chưa đủ power, và fallback chưa được bay.

## 2. Phân tích cấu trúc sai số (chỉ seed dev 0–9; experiments/b4_error_structure.py, paper_errstructure.py)
90 nhiệm vụ dev mỗi mức nhiễu, bay như khi hiệu chỉnh (ALNS 40 ms, trigger sự kiện, κ = 1, không độ trễ).

So sánh ba dạng độ lệch, ước lượng bằng hợp lý cực đại Gauss với trung bình b0 + b1 h:
- affine s0 + s1 h;
- số gia độc lập √(q0 + q1 h);
- dạng lai √(q0 + q1 h + q2 h²).

Kết quả:
- AIC của affine thấp hơn √ là 859 (mid) và 910 (high), thấp hơn dạng lai là 72 và 117.
- Kiểm tra chéo 5 phần, chia theo nhiệm vụ, cho cùng thứ hạng.
- Phần phương sai nằm giữa các nhiệm vụ chỉ chiếm 5–7%.
- Tương quan giữa sai số của một task và số gia sang task kế tiếp trên cùng tuyến là −0,20 (mid) và −0,05 (high), tức
  các chặng gần như độc lập.
- Ở mức một chặng, độ lệch của sai số thời gian bay tỷ lệ với thời lượng chặng: sd = c_v t, với c_v = 0,39 (mid) và
  1,15 (high).

Diễn giải: nhiễu (gió, sai số tốc độ) kéo dài suốt một chặng, nên sai số tỷ lệ với thời lượng chặng. Mô hình số gia độc
lập theo thời gian (var ∝ h) bị bác bỏ. Mô hình lan truyền mô-men đúng với dữ liệu phải dùng phương sai theo chặng
(c_v t)², độc lập giữa các chặng.

## 3. Mô hình lập kế hoạch (journal_core/study4.py, experiments/b4_grid.py)
Mọi mô hình dùng cùng repair, cùng ALNS với ngân sách cố định 40 ms, cùng trigger định kỳ 60 s và cùng fallback danh
nghĩa của nghiên cứu 3. Chỉ phép kiểm tra chấp nhận thời điểm hoàn thành f_j khác nhau:
- Đề xuất (CC): f + m(h) + z s(h) ≤ d, tương đương f ≤ d~ dạng đóng; mô hình sai số theo mức nhiễu như nghiên cứu 2–3.
- Buffer tỷ lệ (PropBuf): f + c h ≤ d.
- Lan truyền mô-men (MP), theo Ehmke và cộng sự (2015):
  - thời gian bay một chặng có thời lượng danh nghĩa t ~ N((1 + a) t + c, (c_v t)²);
  - thời gian phục vụ ~ N((1 + a_s) s, (c_s s)²);
  - các chặng độc lập; max(đến, mở cửa sổ) xấp xỉ theo Clark (1961);
  - chấp nhận nếu E[F] + z sd[F] ≤ d;
  - tham số theo chặng hiệu chỉnh trên dev (models/mp_model_dev.json).

  Khi gỡ một task, phương sai của một chặng dài có thể lớn hơn tổng phương sai của hai chặng nó thay thế. Vì vậy mọi tuyến
  được lọc thêm một lần trước khi công bố; số task bị lọc được ghi lại (n_mp_fix).
- Hiệu chỉnh trực tuyến (Onl):
  - mô hình sai số gộp cả hai mức nhiễu (dữ liệu dev, trọng số n0 cặp);
  - khớp lại ở mỗi lần gọi với các cặp (h, e) của các task đã hoàn thành trong nhiệm vụ;
  - một z chung, không cần biết mức nhiễu.

Unit test: tests/test_study4.py (7 test).

## 4. Lựa chọn trên dev (seed 0–9; results/tier_b/dev4_tune.csv, dev4_tune2.csv, dev4_tune3.csv; experiments/analyze_dev4.py)
Quy tắc chọn đặt trước, như nghiên cứu 2: mỗi mô hình một tham số; theo từng mức nhiễu, chọn giá trị có utility dev
trung bình cao nhất qua hai hệ số cửa sổ và κ_B ∈ {10, 50, 200}; riêng Onl dùng một giá trị cho cả hai mức.
Lưới và kết quả (utility %, mid / high):
- CC, z ∈ {0; 0,25; 0,5; 1; 1,5; 2}. z của nghiên cứu 2 (0,5 / 0) được chọn khi chưa có fallback và đạt 61,24 / 46,92.
  Chọn z = 1 (mid), 0,5 (high): 61,89 / 48,31.
- PropBuf, c ∈ {0,05; 0,1; 0,2; 0,3; 0,45; 0,6; 0,8; 1}. Chọn c = 0,45 (mid), 0,6 (high): 61,92 / 47,99.
- MP, z ∈ {0; 0,5; 1; 1,5; 2}. Chọn z = 1 (mid), 0,5 (high): 62,23 / 47,74.
- Onl, n0 ∈ {50, 300}, z ∈ {0; 0,25; 0,5; 0,75; 1}. Chọn n0 = 50, z = 0,5: 61,40 / 47,30.

Trên dev, ba mô hình tĩnh chênh nhau dưới 0,2 điểm % tính gộp, nên không kỳ vọng mô hình nào hơn rõ mô hình nào. Các giá
trị được ghi trong journal_core/study4.py (Z4_BY_LEVEL, PROP_BY_LEVEL, ZMP_BY_LEVEL, ONLINE).

## 5. Ma trận tầng B (experiments/configs/S4_B.yaml)
Seed held-out MỚI 8000–8029 × {small, medium, large} × {arrivals, failures, deadlines} = 270 nhiệm vụ. Nhiễu {mid, high};
độ trễ high; κ_B {10, 50, 200}; cửa sổ ×{1; 0,5}, tức 12 cấu hình. 11 phương pháp, tất cả trigger định kỳ 60 s trừ
phương pháp thông thường:
- CC: alns_fixed@40~z=auto4;fb=nominal (mô hình đề xuất, ngân sách cố định);
- PropBuf: alns_fixed@40~prop=auto;fb=nominal;
- MP: alns_fixed@40~mp=auto;fb=nominal;
- MPnf: alns_fixed@40~mp=auto (không fallback);
- Onl: alns_fixed@40~online=auto;fb=nominal;
- Full: proposed~z=auto4;fb=nominal (phương pháp đầy đủ với quy tắc dừng học được);
- Buf: alns_fixed@40~buf=60;
- Forty: alns_fixed@40 (mô hình danh nghĩa);
- Conv: alns_fixed@40+event (planner thông thường);
- RepCC: regret_repair~z=auto4;fb=nominal;
- Rep: regret_repair (chỉ repair, mô hình danh nghĩa).

Tổng 35 640 lượt chạy, 4 worker.

## 6. Giả thuyết và kiểm định tầng B (experiments/analyze_study4.py)
Như nghiên cứu 2–3:
- chỉ số chính là utility rate;
- mỗi nhiệm vụ lấy trung bình chênh lệch qua 12 cấu hình;
- bootstrap cặp 10 000 lần, CI 95% percentile, p hai phía;
- kiểm định không kém (NI): p một phía bằng tỷ lệ trung bình bootstrap ≤ −0,5 điểm %.

Họ chính, Holm trên 5 phép, α = 0,05:
- H9: CC > PropBuf (gộp). Nếu thất bại, hình dạng lề và hiệu chỉnh trung bình không mang thêm giá trị so với một buffer tỷ
  lệ đã tinh chỉnh; claim tương ứng bị hạ.
- H10: CC không kém MP (biên −0,5 điểm %). Theo trình tự cố định: chỉ khi NI đạt mới kiểm "CC > MP" (hai phía, α = 0,05).
- H11: MP > MPnf, tức fallback cũng cải thiện lan truyền mô-men (tính tổng quát của fallback).
- H12: CC > Buf (buffer cố định 60 s), gộp.
- H13: CC > Forty (mô hình danh nghĩa), gộp.

Thứ yếu, đặt trước là mô tả:
- H10b: số vòng lặp ALNS trên mỗi ms lập kế hoạch, CC so với MP;
- Onl so với CC (NI, biên −0,5);
- Full so với CC (quy tắc dừng);
- RepCC so với Rep (mô hình độc lập với search);
- CC và Full so với Conv;
- theo từng vùng (4 vùng);
- số task trễ, mất, bỏ; n_mp_fix;
- biểu đồ độ tin cậy (coverage): task đã thực hiện của CC và Forty, nhóm theo xác suất đúng hạn dự báo
  Φ((d − f − m(h))/s(h)) ở lần công bố cuối, so với tỷ lệ đúng hạn thực tế.

Kết quả âm được báo cáo như kết quả dương. Không loại nhiệm vụ nào.

Quy tắc diễn giải đặt trước:
- H10 NI đạt, superiority không đạt: "dạng đóng tương đương lan truyền mô-men dọc tuyến".
- H10 NI không đạt: báo cáo MP tốt hơn, nêu rõ chênh lệch và chi phí.
- H11 đạt: fallback là cơ chế tổng quát cho chance constraint cứng.

## 7. Tầng C (nghiên cứu 4C)
Mục tiêu: xác nhận trên PX4 SITL + Gazebo một hiệu ứng lớn, đặt ở vùng tầng B dự báo hiệu ứng lớn nhất. Study 2 đã kiểm ở
nhiễu mid, cửa sổ ×1, tức vùng có hiệu ứng nhỏ nhất.

Hiệu chỉnh: 9 chuyến bay dev, seed 0–2 × 3 profile, ALNS 40 ms, trigger sự kiện, κ_B = 10, tốc độ mô phỏng 2, nhiễu high,
cửa sổ ×1 (results/tier_c/calib_dev_high, RTF trung bình 1,87, nhỏ nhất 1,72). Mô hình high của tầng C:
m = −6,25 + 0,332 h, s = 0,43 + 0,488 h (69 task), ghi trong models/error_model_tierc_dev4.json (bản sao của file đóng
băng cộng thêm mức high; experiments/c4_calibrate_high.py). Hệ số theo h gần với tầng B (0,29 và 0,64).

Ước lượng hiệu ứng: tầng B tương ứng trên seed dev (gz, 30 nhiệm vụ, nhiễu high, κ_B 50, results/tier_b/dev4c_gz.csv).
Proposed + fallback (z = 0,5) trừ các phương pháp, ở cửa sổ ×0,5:
- không fallback: +9,39 điểm % (sd 13,6);
- mô hình danh nghĩa: +5,52 (sd 8,7);
- planner thông thường: +4,30 (sd 9,6).

Ở cửa sổ ×1 hiệu ứng nhỏ hơn: +4,73, +2,41, +1,30. Study 2 cho thấy độ lệch chuẩn theo nhiệm vụ của tầng C gần bằng tầng B
(10,92 so với 11,17).

Cỡ mẫu: n = ((1,96 + 0,84) sd / δ)². Với hiệu ứng tầng C giả định chỉ bằng 75% tầng B, cần khoảng 35 nhiệm vụ cho so sánh
với mô hình danh nghĩa và khoảng 29 cho so sánh với bản không fallback. Chọn 36 nhiệm vụ: seed 9000–9011 × 3 profile.

Thiết kế:
- 3 phương pháp, cùng trigger định kỳ 60 s (giây tầng B), κ_B = 50, tốc độ 2, nhiễu high, cửa sổ ×0,5:
  - FB: proposed~z=0.5,fb=nominal (phương pháp đầy đủ của nghiên cứu 4, mức high);
  - NoFb: proposed~z=0.5 (cùng mô hình, không fallback);
  - Nom: alns_fixed@40 (cùng search, mô hình danh nghĩa).
- Chạy bằng journal_ros/run_batch4.sh và run_mission4.sh qua journal_ros/study4c.py. Các node đóng băng của nghiên cứu 2
  không bị sửa: wrapper thay gz_scenario bằng kịch bản có cửa sổ thu hẹp, và thay solve2 bằng solve3 có fallback cho
  phương pháp FB. Đã kiểm tra bằng ATSWARM_DRYRUN và một chuyến bay dev (seed 3, arrivals).
- Seed lặp ngoài, phương pháp lặp trong, để các phương pháp xen kẽ theo thời gian.
- RTF hợp lệ trong [1,6; 2,2]. Lượt ngoài khoảng được lặp lại một lần cùng seed và lượt lặp thay thế; phân tích độ nhạy
  dùng lượt gốc.

Giả thuyết (experiments/analyze_study4c.py), họ chính Holm trên 2 phép, FB trừ phương pháp, utility rate, bootstrap cặp theo
nhiệm vụ:
- H14: FB > Nom;
- H15: FB > NoFb.

Tuần tự nhóm, biên O'Brien–Fleming cho 2 lần nhìn (α hai phía 0,05):
- phân tích giữa chừng sau seed 9000–9005 (18 nhiệm vụ), ngưỡng danh nghĩa 0,0052;
- nếu cả hai giả thuyết bị bác bỏ (p Holm < 0,0052, hiệu dương) thì dừng sớm;
- nếu không, bay tiếp 9006–9011 và phân tích cuối với ngưỡng 0,048.

Mô tả: số task trễ, ms/lần gọi, RTF; dự báo của tầng B trên cùng nhiệm vụ (experiments/configs/S4C_B_gz.yaml) và tương
quan theo lượt chạy.

## 8. Đo thời gian và máy
Như nghiên cứu 2–3:
- laptop i7-11800H, WSL2, 4 worker;
- các phương pháp xen kẽ trong cùng cấu hình;
- không chạy song song với tầng C hay lưới khác;
- trình duyệt có thể mở (ghi nhận); ms và vòng lặp/ms chỉ so sánh tương đối trong cùng lượt.

## 9. Sai lệch
(trống khi đóng băng)

## 10. Kết quả
(điền sau lượt chạy)
