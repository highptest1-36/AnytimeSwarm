# Protocol đăng ký trước — Nghiên cứu 5 (fallback có tính chi phí trễ)

Viết ngày 31/10/2026, SAU kết quả held-out của nghiên cứu 1–4 (kể cả tầng C của nghiên cứu 4) và các lượt dev của nghiên
cứu 5, TRƯỚC mọi lượt chạy trên seed held-out mới 10000–10029 (tầng B). File đóng băng: `results/frozen_study5_sha256.txt`
(cùng commit git). Không chỉnh sau khi chạy; mọi thay đổi bắt buộc ghi vào mục "Sai lệch".

## 1. Động cơ
Utility của nghiên cứu 1–4 chỉ tính phần thưởng của task phục vụ đúng hạn. Một task đến trễ không được gì và cũng không
mất gì. Trong nhiều ứng dụng, một lần đến trễ có chi phí riêng: năng lượng và thời gian bay vô ích, một khách hàng đã bỏ
đi, một cam kết bị vi phạm.

Phân tích độ nhạy thăm dò (experiments/paper_latepen.py, không đăng ký trước, chỉ chấm điểm lại các lượt held-out đã có)
gán cho mỗi lần đến trễ chi phí λ lần phần thưởng trung bình của một task:

    u_λ = utility_rate − λ · late_served / n_tasks.

Kết quả (results/study4/report_latepen.md):
- Lợi thế của mô hình đề xuất so với mô hình danh nghĩa tăng theo λ: +5,07 (λ = 0), +9,63 (λ = 1), +14,19 (λ = 2) điểm %.
  Tương tự với planner thông thường.
- Fallback danh nghĩa có điểm hòa vốn λ* ≈ 0,49 (nghiên cứu 3), 1,11 (fallback cho moment propagation, nghiên cứu 4) và
  1,51 (tầng C). Lý do: fallback lập kế hoạch các task bị bỏ theo deadline danh nghĩa, nên nhiều task trong số đó đến trễ.
- So với proportional buffer, mô hình đề xuất kém hơn một chút ở mọi λ (−0,38 ở λ = 0, −1,00 ở λ = 1).

Vậy fallback danh nghĩa chỉ đúng khi việc đến trễ không tốn gì. Đây là điểm yếu lớn nhất còn lại của phương pháp, và cũng
là chỗ mô hình xác suất của phương pháp đề xuất có thể có lợi thế thật so với một buffer: buffer không có xác suất đúng
hạn, nên không có cách tự nhiên nào để biết một task bị bỏ có đáng thử hay không.

## 2. Phương pháp: fallback có tính chi phí trễ (journal_core/study5.py)
Một task có xác suất đúng hạn p, phần thưởng r và chi phí trễ λ r. Thử task có giá trị kỳ vọng p r − (1 − p) λ r, không âm
khi và chỉ khi

    p ≥ θ(λ) = λ / (1 + λ).

Với mô hình sai số affine của nghiên cứu 2, p ≥ Φ(z) tương đương f ≤ d~(z) (Proposition 1). Đặt z_λ = Φ⁻¹(θ(λ)).
Deadline lập kế hoạch:
- task được bảo vệ: d~_j(z_p), với z_p = max(z, z_λ);
- task bị chance constraint bỏ (không vehicle nào kịp d~_j(z_p) kể cả bay thẳng): min(d_j, d~_j(z_λ)); task không kịp cả
  deadline này thì bị bỏ.

Tính chất:
- λ = 0: z_λ = −∞, đúng là fallback danh nghĩa của nghiên cứu 3–4.
- λ lớn: z_λ ≥ z, không còn fallback, và chance constraint ở mức z_λ.
- Không thêm tham số cần tune: z giữ giá trị của nghiên cứu 4 (Z4_BY_LEVEL: 1 ở mid, 0,5 ở high); λ là đặc tính của ứng
  dụng, được cho trước.
- Mọi task phục vụ được giữ bảo đảm Φ(z_p) hoặc Φ(z_λ) của Proposition 1, nên mọi lần thử đều có giá trị kỳ vọng không âm
  nếu mô hình sai số đúng. Quy tắc bỏ qua ảnh hưởng của một task fallback lên các task sau nó trên cùng tuyến.

Code: `cost_fallback_problem`, `solve5`; tùy chọn `~z=auto4;lam=<λ>` trong experiments/b5_grid.py. Mọi file của nghiên
cứu 2–4 không bị sửa; study5.py chỉ bọc chúng. Unit test: tests/test_study5.py (6 test).

## 3. Đối thủ được tune theo từng λ
Để so sánh công bằng nhất, các đối thủ được tune riêng cho từng λ trên dev, còn phương pháp đề xuất không được tune lại:
- PropBest: proportional buffer f + c h ≤ d, có hoặc không có fallback danh nghĩa (một buffer có fallback chỉ có fallback
  danh nghĩa, vì nó không có xác suất). Lưới c ∈ {0,1; 0,2; 0,3; 0,45; 0,6; 0,75; 0,9; 1,2} × {có, không fallback}.
- CCnf: mô hình đề xuất không fallback, z ∈ {−0,5; 0; 0,5; 1; 1,5}. Đây là cách đơn giản nhất để tính chi phí trễ: nâng z
  thay vì đổi fallback.
Mỗi họ có 16 hoặc 5 thành viên, chọn theo dev nên có lợi thế chọn trong mẫu; phương pháp đề xuất thì không.

## 4. Lựa chọn trên dev (seed 0–9; results/tier_b/dev5_tune.csv, dev5_tune2.csv; experiments/analyze_dev5.py)
Ma trận như nghiên cứu 4: 90 nhiệm vụ dev, nhiễu {mid, high}, độ trễ high, κ_B {10, 50, 200}, cửa sổ ×{1; 0,5}; 29 phương
pháp, 31 320 lượt. Quy tắc chọn đặt trước, như nghiên cứu 2 và 4: theo từng mức nhiễu và từng λ, chọn thành viên có u_λ dev
trung bình cao nhất qua hai hệ số cửa sổ và ba κ_B.

Lưới đầu (dev5_tune.csv) chọn hai giá trị nằm ở biên: c = 0,3 không fallback (mid, λ = 1) và z = 0 (high, λ = 0,5). Lưới
được mở rộng xuống (dev5_tune2.csv: c ∈ {0,1; 0,2} có và không fallback, z = −0,5). Lựa chọn không đổi, và mọi giá trị chọn
nay nằm trong lưới.

Lựa chọn (ghi trong journal_core/study5.TUNED), u_λ dev (%):

| λ | mức | PropBest | CCnf | CA(λ) | CCfb |
|---|---|---|---|---|---|
| 0,5 | mid | c = 0,45, có fallback: 58,49 | z = 1: 57,47 | 57,90 | 57,89 |
| 0,5 | high | c = 0,75, có fallback: 41,21 | z = 0: 39,09 | 41,62 | 41,20 |
| 1 | mid | c = 0,3, không fallback: 55,49 | z = 1: 55,62 | 55,25 | 53,92 |
| 1 | high | c = 0,45, không fallback: 35,52 | z = 0,5: 34,63 | 37,56 | 34,09 |
| 2 | mid | c = 0,45, không fallback: 51,84 | z = 1: 51,94 | 50,04 | 45,96 |
| 2 | high | c = 0,75, không fallback: 30,15 | z = 0,5: 29,89 | 29,97 | 19,86 |

Ước lượng dev của họ chính (CA(1) trừ phương pháp, u_1, gộp, bootstrap theo 90 nhiệm vụ; trong mẫu, có lợi cho các đối thủ
được chọn):
- CCfb: +2,40 [+1,37; +3,49], sd theo nhiệm vụ 5,15;
- PropBest(1): +0,90 [+0,05; +1,77], sd 4,12;
- CCnf(1): +1,28 [+0,42; +2,12], sd 4,16;
- Forty: +14,03 [+12,70; +15,35].

Ở λ = 2, CA(2) kém các đối thủ được tune (−0,99 so với PropBest, −0,91 so với CCnf), chủ yếu ở mid. Ở λ = 0,5, CA(0,5)
ngang PropBest (−0,09) và hơn CCnf (+1,48). Vậy trên dev, lợi thế không đều theo λ; điều này được báo cáo ở mục thứ yếu.

Cỡ mẫu: n = ((1,96 + 0,84) sd / δ)². Với hiệu ứng dev, so với PropBest cần khoảng 164 nhiệm vụ, so với CCnf khoảng 83.
270 nhiệm vụ held-out cho power cao nếu hiệu ứng không co lại quá một nửa; nếu co lại một nửa, power của superiority so với
PropBest còn khoảng 43%, còn power của NI vẫn trên 99%. Kiểm định chính vì vậy là NI, superiority theo trình tự cố định.

## 5. Ma trận tầng B (experiments/configs/S5_B.yaml)
Seed held-out MỚI 10000–10029 × {small, medium, large} × {arrivals, failures, deadlines} = 270 nhiệm vụ; 12 cấu hình như
nghiên cứu 4. 17 phương pháp, tất cả ALNS 40 ms, trigger định kỳ 60 s trừ phương pháp thông thường:
- CA(1), CA(0,5), CA(2): alns_fixed@40~z=auto4;lam=λ (đề xuất);
- CCfb: alns_fixed@40~z=auto4;fb=nominal (nghiên cứu 4);
- thành viên của CCnf: z ∈ {0; 0,5; 1}, không fallback;
- thành viên của PropBest: c = 0,45 và 0,75 có fallback, c = 0,3, 0,45 và 0,75 không fallback;
- MP: mp=auto;fb=nominal; MPnf: mp=auto;
- Buf: buf=60; Forty: mô hình danh nghĩa; Conv: alns_fixed@40+event.

Mỗi thành viên chạy ở cả hai mức nhiễu; PropBest(λ) và CCnf(λ) được ghép theo mức nhiễu trong phân tích. Tổng 55 080 lượt,
4 worker. Chạy: tools/run_study5.sh.

## 6. Giả thuyết và kiểm định tầng B (experiments/analyze_study5.py)
Như nghiên cứu 2–4:
- mỗi nhiệm vụ lấy trung bình chênh lệch qua 12 cấu hình;
- bootstrap cặp theo nhiệm vụ 10 000 lần, CI 95% percentile, p hai phía;
- kiểm định không kém (NI): p một phía bằng tỷ lệ trung bình bootstrap ≤ −0,5 điểm %.

Chỉ số chính: u_1 (λ = 1, một lần đến trễ tốn bằng phần thưởng trung bình của một task). Đây là giá trị đơn giản nhất
khác 0, và nằm trong khoảng hòa vốn của fallback danh nghĩa (0,5–1,5). CA(1) là fallback có tính chi phí trễ với λ = 1.

Họ chính, Holm trên 4 phép, α = 0,05, CA(1) trừ phương pháp, điểm u_1:
- H16: CA(1) > CCfb (fallback danh nghĩa, phương pháp của nghiên cứu 4).
- H17: CA(1) không kém PropBest(1) (biên −0,5 điểm %). Theo trình tự cố định: chỉ khi NI đạt mới kiểm "CA(1) > PropBest(1)"
  (hai phía, α = 0,05).
- H18: CA(1) không kém CCnf(1) (biên −0,5). Trình tự cố định như H17.
- H19: CA(1) > Forty (mô hình danh nghĩa).

Thứ yếu, đặt trước là mô tả:
- λ = 0,5 và λ = 2: CA(λ) so với CCfb, PropBest(λ), CCnf(λ), MP, MPnf, Buf, Forty, Conv, cùng điểm u_λ.
- Độ bền khi λ khi tune khác λ khi dùng: CA(λ) so với PropBest(1) và CCnf(1) chấm ở λ = 0,5 và 2; CA(1) so với CA(λ) chấm ở
  u_λ (cái giá của việc đặt sai λ).
- Theo mức nhiễu và 4 vùng ở λ = 1.
- Số task trễ; utility ở λ = 0 (cái giá của quy tắc khi việc trễ không tốn gì); ms mỗi lần gọi.

Kết quả âm được báo cáo như kết quả dương. Không loại nhiệm vụ nào.

Quy tắc diễn giải đặt trước:
- H16 đạt: khi việc đến trễ có chi phí, quy tắc mới tốt hơn fallback danh nghĩa.
- H17/H18 NI đạt, superiority không đạt: "phương pháp đề xuất, không tune lại, ngang các đối thủ được tune riêng cho chi
  phí trễ".
- Superiority đạt: "tốt hơn cả đối thủ được tune riêng cho chi phí trễ".
- NI không đạt: báo cáo đối thủ tốt hơn, nêu rõ chênh lệch; claim về lợi thế của mô hình xác suất bị hạ.

## 7. Tầng C
Quyết định sau tầng B, ghi thành phụ lục §11 trước mọi chuyến bay, với seed mới từ 11000 trở lên. Không có chuyến bay nào
của nghiên cứu 5 trước khi phụ lục được commit.

## 8. Đo thời gian và máy
Như nghiên cứu 2–4: laptop i7-11800H, WSL2, 4 worker; các phương pháp xen kẽ trong cùng cấu hình; không chạy song song với
lưới khác. Lưới dev chạy 8 worker; mọi phương pháp dùng cùng ngân sách 40 ms nên điều này không ảnh hưởng đến lựa chọn.

## 9. Sai lệch
(trống khi đóng băng; điền ngày 31/10/2026 sau khi lượt held-out kết thúc)

1. Không có sai lệch nào trong thiết kế, seed, phương pháp hay kiểm định. Kiểm tra SHA-256 đạt trước lượt chạy
   (results/heldout_logs/progress_study5.txt); 55 080 lượt, không lỗi, không loại nhiệm vụ nào.
2. Lỗi trùng tên macro trong analyze_study5.py (đóng băng): vòng lặp thứ yếu ghi đè macro FP{CCfb,Prop,CCnf,Forty}One (p đã
   hiệu chỉnh Holm) bằng p chưa hiệu chỉnh, và ghi lại FD/FAbs cùng giá trị. Ở đây cả hai p đều < 0,001 nên chữ hiển thị
   giống hệt; bảng p Holm đúng nằm trong results/study5/report.md. File đóng băng không bị sửa.
3. Máy: Chrome được đóng trong khoảng giữa lượt chạy (khoảng 17:10 giờ địa phương, sau khoảng 37% số cấu hình). Mọi phương
   pháp dùng cùng ngân sách 40 ms và xen kẽ trong cùng cấu hình, nên so sánh không bị ảnh hưởng.
4. Ngoài protocol, để viết bài: experiments/paper_s4x.py tạo thêm macro XDabsFive*/XCIFive* (giá trị tuyệt đối và khoảng
   tin cậy) từ numbers_s5.tex; không có phân tích mới.

## 10. Kết quả
Tầng B (seed 10000–10029, 270 nhiệm vụ, 55 080 lượt; results/study5/report.md). Họ chính ở λ = 1, CA(1) trừ phương pháp,
u_1, điểm %:
- H16 được ủng hộ: so với fallback danh nghĩa +2,42 [+1,81; +3,02], p Holm < 0,001 (45,81% so với 43,40%). Số task trễ mỗi
  nhiệm vụ 4,96 so với 7,39 (ít hơn 33%).
- H17 được ủng hộ: NI đạt; superiority theo trình tự cố định đạt: so với PropBest(1) +0,90 [+0,38; +1,44], p < 0,001.
- H18 được ủng hộ: NI đạt; superiority đạt: so với CCnf(1) +1,78 [+1,25; +2,31], p < 0,001.
- H19 được ủng hộ: so với mô hình danh nghĩa +11,75 [+10,88; +12,57]; so với planner thông thường +12,54.

Theo mức nhiễu ở λ = 1: lợi thế so với các đối thủ được tune đến từ nhiễu high (+2,10 so với PropBest, +3,49 so với CCnf);
ở mid ngang nhau (−0,30 và +0,08); ở mid với cửa sổ gốc, cả hai đối thủ tốt hơn (−2,08 và −1,68).

Thứ yếu:
- λ = 0,5: CA(0,5) ngang PropBest (+0,21 [−0,22; +0,64]), hơn CCnf (+1,65) và CCfb (+0,63).
- λ = 2: CA(2) hơn CCfb +7,25, ngang CCnf (−0,02 [−0,47; +0,42]), kém PropBest(2) −1,02 [−1,58; −0,47] và kém MPnf −1,10.
- Độ bền: PropBest tune cho λ = 1 dùng ở λ = 2 kém CA(2) 1,05 [0,42; 1,69], dùng ở λ = 0,5 kém CA(0,5) 1,46; CCnf tune cho
  λ = 1 kém CA(0,5) 3,32 ở λ = 0,5. CA(1) dùng ở λ = 2 kém CA(2) 1,22; dùng ở λ = 0,5 ngang CA(0,5) (+0,02).
- Giá ở λ = 0: CA(1) có utility thấp hơn fallback danh nghĩa 1,20 điểm % (53,13% so với 54,33%).

Diễn giải theo §6: ở λ = 1, phương pháp đề xuất, không tune lại, tốt hơn cả đối thủ được tune riêng cho chi phí trễ. Lợi thế
không đều theo λ: ở λ = 2, một proportional buffer không fallback được tune cho λ = 2 tốt hơn. Giả thuyết giải thích (chưa
kiểm định): quy tắc định giá từng task fallback riêng lẻ và bỏ qua độ trễ mà task đó gây cho các task sau trên cùng tuyến.
