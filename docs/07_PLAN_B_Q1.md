# Kế hoạch B: nâng bài lên mức Q1 (bắt đầu 28/10/2026)

Nguồn: phản biện độc lập (tóm tắt trong chat 28/10) + yêu cầu tác giả: gọi phương pháp mới là "proposed", so sánh với
các nghiên cứu khác (cài lại làm baseline, trích dẫn), hình/bảng chuyên nghiệp, hình kiến trúc chi tiết (chữ đen, to).

Nguyên tắc khoa học (không thương lượng):
- Seed held-out cũ (B 3000–3029, C 4000–4009) đã dùng: giữ kết quả, báo cáo trong bài (nghiên cứu 1), KHÔNG tinh chỉnh
  trên chúng. Phát triển mới chỉ trên seed dev (B 0–9, C 0–2). Đánh giá mới trên seed held-out MỚI: tầng B 5000–5029,
  tầng C 6000–6014, sau khi đóng băng protocol v2 (docs/08_PROTOCOL_V2.md, hash, commit).
- Baseline từ tài liệu chỉ cài khi thuật toán được mô tả đủ rõ; ghi rõ "re-implementation in the spirit of [x]".
  Không khẳng định hơn các bài không cài lại được (chỉ so sánh định tính bằng bảng tính năng).
- Kết quả báo cáo như chạy ra.

## 1. Phương pháp đề xuất (proposed) — AnytimeSwarm-X (tên tạm)
Một bộ điều khiển metareasoning quyết định cả KHI NÀO replan và KHI NÀO dừng tính, trên mô hình thực thi đã hiệu chỉnh:
- X1 Dừng anytime học được + chi phí trễ theo rủi ro (đã có: anytime_risk).
- X2 Lập kế hoạch có ràng buộc xác suất: deadline hiệu dụng d_j − (m(h_j) + z·s(h_j)), h_j = thời gian tới khi hoàn
  thành dự kiến; publish/thực thi vẫn dùng deadline thật. z chọn trên dev.
- X3 Trigger theo giá trị: replan khi độ lệch thực thi dự báo làm mất giá trị (hoặc độ lệch > θ) hoặc quá T_max; θ, T_max
  chọn trên dev.
Ablation: bỏ từng thành phần.

## 2. Baseline (cài lại, cùng ALNS/cùng seed khi có thể)
- ALNS ngân sách cố định 250 ms / 40 ms [Ropke & Pisinger 2006]; ngân sách co giãn theo quy mô (ms ∝ số task, chỉnh trên dev).
- Dừng khi trì trệ (stagnation).
- Meta-level control với dự báo hiệu năng trực tuyến [Svegliato et al. 2018]: khớp đường cong chất lượng trực tuyến,
  dừng khi lợi ích biên kỳ vọng ≤ chi phí thời gian.
- Performance profile + monitoring [Hansen & Zilberstein 2001]: profile chất lượng–thời gian ngoại tuyến (dev), dừng myopic.
- Trigger: theo sự kiện, định kỳ / rolling horizon [Ouelhadj & Petrovic 2009], theo ngưỡng lệch.
- Đệm thời gian cố định (robust buffer) như thực hành VRPTW bền vững.
- AnytimeSwarm (bản trước) và AnytimeSwarm-R (nghiên cứu 1).

## 3. Quét chế độ (regime sweep) — chỉ ra khi nào dừng thích nghi có tác dụng
κ ∈ {10, 50, 200}; độ chặt cửa sổ thời gian (slack ×1, ×0,5); nhiễu {mid, high}; quy mô small/medium/large (+XL riêng).

## 4. Tầng C
Seed 6000–6014 × 3 profile = 45 nhiệm vụ? (tùy thời gian: ~3,5 phút/chuyến), 2 điều kiện (mid κ50, high κ50 hoặc κ200),
phương pháp: proposed, ALNS 40 ms, Svegliato-style, AnytimeSwarm. Định vị: kiểm tra độ trung thực + xác nhận chiều.

## 5. Thống kê
Bootstrap cặp theo nhiệm vụ, Holm cho họ chính; kiểm định tương đương TOST với biên ±0,5 pp cho các phát biểu "không thua";
báo cáo cỡ hiệu ứng và phân tích công suất. Đồng hồ: dùng wall clock như trước, báo cáo nhiễu lặp lại.

## 6. Bài báo
- Tiêu đề/abstract định vị: hệ thống metareasoning cho replan đa UAV (khi nào replan + khi nào dừng), proposed vs. baseline
  từ tài liệu, nghiên cứu đăng ký trước 2 tầng.
- Hình kiến trúc mới (TikZ, chi tiết, biểu tượng UAV/bản đồ/ROS 2/PX4, chữ đen cỡ lớn).
- Bảng so sánh tính năng với nghiên cứu gần đây (định tính) + bảng/hình kết quả định lượng chuyên nghiệp.
- Sửa toàn bộ lỗi diễn giải phản biện nêu (delay-cost ablation, error-model attribution, κ=1, Prop 1(ii), "six methods",
  định nghĩa cột bảng, khai báo sai lệch B–C, κ của benchmark tĩnh, tài liệu situated planning/DAS/rescheduling).

## 7. Tiến độ
- [x] P1 code baseline + proposed (journal_core/study2.py, experiments/b2_grid.py, b2_build_profile.py; trigger
      hybrid trong kinematic_executor; 15 test cũ vẫn đạt)
- P2a (dev2_explore, 28/10): đệm theo h = d − t0 sai (h quá lớn cho task xa → đệm phình, nhiễu high sập về 0).
  Ở mid/w1: z=0,5 + periodic 72,8% vs baseline tốt nhất 67,8%. Sửa: deadline hiệu dụng dạng đóng chính xác
  d~ = t0 + (d − t0 − b0 − z s0)/(1 + b1 + z s1) (ràng buộc trên chính thời điểm hoàn thành). Thêm baseline đệm cố định.
- P2b (dev2b_explore): chạy lại với công thức đúng.
- [ ] P2 dev exploration, chọn tham số, Go/No-Go
- [ ] P3 protocol v2 + freeze
- [ ] P4 held-out tầng B (5000–5029)
- [ ] P5 held-out tầng C (6000–)
- [ ] P6 phân tích, hình, bảng
- [ ] P7 viết lại bản thảo + hình kiến trúc
