# Kế hoạch cải thiện bài (sau bản rút gọn 3486ae0, 29/10/2026)

Mục tiêu: nâng bài từ khoảng 6,5/10 lên 7,5–8/10 cho một tạp chí Q1 (RAS, JIRS). Mỗi điểm yếu được xử lý bằng một
giả thuyết kiểm định được, không chỉ bằng câu chữ. Các bước giữ đúng quy tắc của dự án: chỉ tinh chỉnh trên seed dev,
đóng băng protocol bằng SHA-256 trước khi chạy held-out, mỗi bộ seed chỉ dùng một lần, và báo cáo cả kết quả âm.

## 1. Chẩn đoán: các điểm yếu và nguyên nhân gốc

| # | Điểm yếu | Nguyên nhân gốc | Mức rủi ro với reviewer |
|---|---|---|---|
| W1 | Tính mới của deadline dạng đóng | Chance constraint cho từng khách hàng trong VRPTW đã có (Ehmke, Campbell & Urban 2015, EJOR 240(2):539–550, doi:10.1016/j.ejor.2014.06.045; Li, Tian & Leung 2010, IJPE 125(1):137–145). Bài chưa trích dẫn và chưa phân biệt | Cao nhất |
| W2 | Không biết mức tăng đến từ hình dạng tuyến tính của lề hay từ việc hiệu chỉnh trên dữ liệu | Thiếu baseline buffer tỷ lệ với thời gian chờ (c·h) | Cao |
| W3 | Không có baseline chance-constrained thật từ tài liệu | Chỉ có buffer cố định đại diện cho nhóm robust | Cao |
| W4 | Fallback được thiết kế sau khi xem held-out; chỉ được kiểm ở tầng B | Chưa có lượt bay xác nhận đủ power | Trung bình–cao |
| W5 | Tầng C không đủ power cho utility | 30 nhiệm vụ, độ lệch chuẩn khoảng 10,9 điểm %, kiểm định ở vùng có hiệu ứng nhỏ (nhiễu mid) | Trung bình |
| W6 | z và mô hình sai số chọn theo mức nhiễu, tức giả định đã biết mức nhiễu | Hiệu chỉnh offline theo từng mức | Trung bình |
| W7 | Mệnh đề chỉ đảm bảo Φ(z) "nếu tuyến bắt đầu đúng kế hoạch"; chưa kiểm chứng thực nghiệm | Chưa có phân tích coverage (độ tin cậy) | Trung bình |
| W8 | Phạm vi hẹp: một ALNS, một họ kịch bản, gió không đổi | Thiết kế ban đầu | Thấp–trung bình |
| W9 | Quy tắc dừng thành gánh nặng trong tên và câu chuyện | H3 cho thấy nó tương đương ngân sách cố định | Thấp (sửa bằng câu chữ) |

## 2. Hướng giải quyết khoa học

### W1 + W3: biến "phép biến đổi đại số" thành một luận điểm về cấu trúc sai số, và so trực tiếp với tài liệu

Luận điểm mới (có thể kiểm định): sai số thời gian hoàn thành trong vòng lặp kín có thành phần tương quan theo nhiệm
vụ. Gió không đổi trong một nhiệm vụ và độ lệch tốc độ có hệ thống làm sai số tích lũy cùng chiều trên mọi chặng. Nếu
sai số đến task j là e(h) = β·h + ε(h), với β là độ lệch theo nhiệm vụ (phương sai σβ²) và ε là nhiễu độc lập theo chặng
(phương sai σε²·h), thì

  Var e(h) = σβ²·h² + σε²·h,  nên  s(h) ≈ σβ·h khi h lớn.

Như vậy độ lệch chuẩn tăng tuyến tính chứ không theo √h. Phương pháp lan truyền mô-men kiểu Ehmke và cộng sự giả định
các chặng độc lập, nên phương sai cộng dồn tuyến tính theo h, tức s ∝ √h. Khi đó nó đánh giá thấp độ bất định ở cuối
tuyến, đúng nơi task bị trễ.

Việc cần làm:
1. Thêm một mệnh đề vào bài: dạng phương sai trên, chứng minh ngắn. Bất đẳng thức √(a²+b²) ≤ a+b cho thấy mô hình tuyến
   tính affine ước lượng s(h) theo hướng thận trọng.
2. Phân tích chỉ dùng dữ liệu dev (được phép): so sánh các mô hình s(h) tuyến tính, √h và √(a h² + b h) bằng AIC hoặc
   log-likelihood ngoài mẫu (hold-out theo nhiệm vụ trong dữ liệu dev), mỗi mức nhiễu một lần. Thêm một hình nhỏ về độ
   khớp mô hình sai số.
3. Cài baseline lấy từ tài liệu: kiểm tra khả thi theo lan truyền mô-men (Ehmke và cộng sự 2015). Thời điểm bắt đầu phục
   vụ được xấp xỉ chuẩn; phép max với thời điểm mở cửa sổ dùng xấp xỉ Clark; phương sai mỗi chặng được hiệu chỉnh trên
   cùng dữ liệu dev, để so sánh công bằng. Baseline được cắm vào cùng repair và ALNS, có cùng fallback và cùng ngân sách.
   Đo cả utility lẫn ms mỗi lần gọi, vì mỗi lần kiểm tra chèn phải lan truyền dọc tuyến, chi phí O(độ dài tuyến) thay vì O(1).
4. Viết lại related work, thêm một đoạn phân biệt ba điểm:
   - mô hình sai số hiệu chỉnh trong vòng lặp kín, phản ánh tương quan,
   - deadline dạng đóng với chi phí kiểm tra O(1), dùng được trong replanning dưới một giây,
   - đánh giá có độ trễ công bố kế hoạch và replanning định kỳ.

Đóng góp 1 khi đó trở thành: "dưới sai số có thành phần tương quan theo nhiệm vụ, chance constraint cho từng task có
dạng đóng, rẻ hơn và không kém (hoặc tốt hơn) lan truyền mô-men với giả định độc lập". Đây là một luận điểm khoa học,
không chỉ là một mẹo cài đặt.

### W2: thang ablation tách từng thành phần của lề

Các phương pháp cùng repair, ALNS, trigger và fallback, chỉ khác mô hình lề:

1. buffer cố định 60 s (đã có),
2. buffer tỷ lệ c·h, với c chọn trên dev trong lưới {0,05; 0,1; 0,2; 0,3} (mới),
3. hiệu chỉnh chỉ phần trung bình, z = 0 (đã có ở dạng ablation),
4. hiệu chỉnh cả trung bình và độ lệch, z theo dev (proposed),
5. lan truyền mô-men kiểu Ehmke (mới, xem W1).

Thang này trả lời rõ phần đóng góp của hình dạng, của việc hiệu chỉnh trung bình, của độ lệch và của giả định tương quan.

### W6: hiệu chỉnh trực tuyến, không cần biết mức nhiễu

Biến thể "online": bắt đầu từ mô hình gộp mọi mức nhiễu (prior từ dev), sau mỗi task hoàn thành thì cập nhật
(b0, b1, s0, s1) bằng bình phương tối thiểu đệ quy có trọng số quên. Dùng một z chung cho mọi mức, chọn trên dev.
Kiểm định không kém hơn biến thể biết mức nhiễu, với biên 0,5 điểm %. Nếu đạt, giới hạn "giả định biết mức nhiễu"
được gỡ khỏi bài.

### W7: kiểm chứng Mệnh đề (ii) bằng coverage

Ghi lại cho từng task được bảo vệ: thời gian chờ h lúc công bố, z áp dụng, và kết quả đúng hạn hay trễ. Vẽ biểu đồ độ
tin cậy: tỷ lệ đúng hạn thực tế theo từng nhóm thập phân vị của h, so với mức mục tiêu Φ(z) (69% với z = 0,5; 50% với
z = 0). Tách riêng các task được thực hiện đúng như kế hoạch và các task bị replanning thay đổi. Phân tích này là mô tả,
nhưng cho reviewer thấy đảm bảo của mệnh đề có thực trên dữ liệu.

### W4 + W5: lượt bay xác nhận fallback, đủ power, đặt ở vùng có hiệu ứng lớn

1. Chọn vùng kiểm định tầng C theo hiệu ứng dự báo, không theo thói quen. Tầng B cho thấy fallback trừ proposed là
   +5,25 điểm % ở vùng nhiễu cao, cửa sổ ×0,5, so với khoảng +0,5 ở vùng mid, cửa sổ ×1. Vùng nhiễu mid mà study 2 dùng
   là nơi có hiệu ứng nhỏ nhất, nên H4 khó có ý nghĩa ngay từ thiết kế.
2. Hiệu chỉnh mô hình sai số tầng C cho mức high: khoảng 9 chuyến bay dev (seed 0–2), khoảng 40 phút.
3. Tính trước cỡ mẫu: chạy tầng B với tham số đã co tỷ lệ trên các nhiệm vụ dev 3 UAV để ước lượng hiệu ứng δ. Dùng
   độ lệch chuẩn thận trọng sd = 10,9 (từ study 2 tầng C):
   n = ((1,96 + 0,84)·sd/δ)². Với δ = 4 điểm % thì n khoảng 58; với δ = 5 thì khoảng 37.
4. Thiết kế tuần tự nhóm: phân tích trung gian ở n/2 với biên O'Brien–Fleming, được dừng sớm nếu vượt biên. Biên được
   đăng ký trước, nên không phải "nhìn trộm" dữ liệu.
5. So sánh chính: fallback với proposed của study 2, phụ là với buffer. Seed held-out mới 9000–90xx.
6. Chạy khi máy rảnh (đóng Chrome) để RTF nằm trong [1,6; 2,2]. Giữ nguyên quy tắc lặp lại một lần.

Thời gian ước tính: khoảng 58 nhiệm vụ × 2 phương pháp × 4,3 phút, tức khoảng 8,3 giờ (1–2 đêm). Dừng sớm có thể còn
khoảng 4 giờ.

### W8: độ tổng quát (thứ yếu, mô tả)

- Mô hình không phụ thuộc planner: so CC + chỉ regret-2 repair (không search) với repair danh nghĩa. Gần như không tốn
  thêm thời gian chạy.
- Độ bền khi mô hình sai: một ma trận nhỏ với gió đổi hướng hoặc độ lớn giữa nhiệm vụ và thời gian phục vụ đuôi nặng.
  Cần thêm tùy chọn cho simulator tầng B, mặc định tắt và có unit test để đảm bảo kết quả cũ không đổi.

### W9: đồng bộ câu chuyện (chỉ sửa câu chữ)

Phương pháp được trình bày là mô hình lập kế hoạch (lề hiệu chỉnh + chance constraint dạng đóng + fallback) cộng
replanning định kỳ. Quy tắc dừng là thành phần có thể thay thế. Kết luận của bài nói rõ ngân sách cố định 40 ms là đủ
trên mô hình này. Giữ cấu hình đã đóng băng để không phá tính nhất quán giữa các study.

## 3. Study 4 (đăng ký trước, seed mới)

Tầng B, seed held-out 8000–8029 (chưa dùng), cùng ma trận 12 cấu hình như study 2 và 3.

Phương pháp: proposed với fallback (cấu hình study 3), buffer tỷ lệ c·h + fallback, lan truyền mô-men + fallback,
proposed online-calibrated + fallback, buffer cố định 60 s, ALNS 40 ms, planner thông thường. Thêm hai nhánh phụ:
CC + repair-only và repair-only danh nghĩa.

Giả thuyết chính (Holm, α = 0,05):
- H9: proposed > buffer tỷ lệ c·h (gộp).
- H10: proposed không kém lan truyền mô-men (biên −0,5 điểm %), kiểm định theo trình tự cố định: không kém trước, rồi
  mới đến hơn. Kèm H10b: ms mỗi lần gọi thấp hơn.
- H11: biến thể online không kém biến thể biết mức nhiễu (biên −0,5).

Mô tả: coverage (W7), thang ablation (W2), nhánh repair-only (W8).

Ước tính máy: khoảng 9 × 270 × 12 = 29 160 lượt chạy, tức khoảng 2–3 giờ. Study 3 chạy 16 200 lượt trong 69 phút.

Tầng C (study 4C): như mục W4 + W5, seed 9000–90xx.

## 4. Thứ tự làm và điều kiện dừng

| Pha | Việc | Tải máy | Thời gian |
|---|---|---|---|
| P0 | Tra cứu tài liệu, viết đoạn related work, mệnh đề về cấu trúc sai số, so sánh mô hình s(h) trên dev | Nhẹ | 0,5 ngày |
| P1 | Cài 3 baseline/biến thể mới + unit test; chọn c, phương sai chặng, z chung trên dev 0–9 | 1–2 giờ chạy dev | 1–1,5 ngày |
| P2 | Viết và đóng băng docs/12_PROTOCOL_V4.md; chạy study 4 tầng B | 2–3 giờ, máy rảnh | 0,5 ngày |
| P3 | Bay hiệu chỉnh mức high, tính cỡ mẫu, đóng băng, bay study 4C | 1–2 đêm | 2 ngày |
| P4 | Cập nhật bài: đóng góp, related work, mệnh đề, kết quả study 4, hình coverage; giữ khoảng 16 trang (đưa phần cũ sang supplementary) | Nhẹ | 1 ngày |

Quy tắc quyết định đặt trước (để không bị thiên lệch khi viết):
- Nếu H10 thất bại, tức lan truyền mô-men tốt hơn: báo cáo trung thực. Đóng góp 1 chuyển thành "dạng đóng đạt X% chất
  lượng với chi phí thấp hơn Y lần", và bài khuyến nghị lan truyền mô-men khi có đủ thời gian tính.
- Nếu H9 thất bại: giá trị nằm ở hình dạng tuyến tính chứ không ở việc hiệu chỉnh. Hạ claim tương ứng.
- Nếu study 4C không có ý nghĩa dù đủ power: báo cáo như vậy. Phần thảo luận về khoảng cách giữa tầng B và tầng C trở
  thành một kết quả.

## 5. Kết quả kỳ vọng với bài

- Đóng góp 1 có luận điểm khoa học (cấu trúc sai số tương quan) và được so trực tiếp với phương pháp chuẩn của tài liệu.
- Ablation đầy đủ, cho biết từng phần của lề đóng góp bao nhiêu.
- Giới hạn "biết mức nhiễu" có thể được gỡ.
- Fallback được xác nhận trên seed mới ở cả hai tầng, với cỡ mẫu tính trước.
- Mệnh đề được kiểm chứng thực nghiệm bằng coverage.

Điểm dự kiến: 7,5–8/10 nếu H9–H11 và study 4C phần lớn đạt; khoảng 7/10 nếu một phần thất bại nhưng được báo cáo
trung thực.
