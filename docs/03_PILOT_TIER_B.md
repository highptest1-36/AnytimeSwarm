# Pilot tầng B (seed dev) — kết quả và quyết định

Ngày 27–28/10/2026. Dữ liệu: `results/tier_b/pilot_dev.csv` (9 720 nhiệm vụ), bảng đầy đủ:
`results/tier_b/pilot_dev_summary.md`. Script: `experiments/b1_pilot.py`, `experiments/b1_analyze.py`.

## Thiết lập

90 nhiệm vụ dev (seed 0–9 × 3 quy mô × 3 profile) × 6 phương pháp × κ ∈ {1, 10, 50} × nhiễu thực thi
{nominal, low, mid} × độ trễ phát hành {none, high}. Config và predictor của bản hội nghị đóng băng (zero-shot).
Planner luôn dùng mô hình danh định; chỉ thực thi thay đổi. Python 3.12 (môi trường ROS), chạy tuần tự dưới guard,
không phải chờ lần nào. Mức nhiễu và trễ là giá trị tạm, chưa hiệu chỉnh bằng PX4/Gazebo.

## Kết quả chính

1. Nhiễu thực thi chi phối kết quả. Utility trung bình của AnytimeSwarm ở κ = 1, không trễ: nominal 0,897, low 0,790,
   mid 0,669. Mức giảm 10–23 điểm phần trăm lớn hơn nhiều so với chênh lệch giữa các planner (dưới 1 điểm, trừ
   alns_fixed 250 ms ở κ = 50). Sai số tích lũy dọc route vì replan chỉ xảy ra khi có sự kiện.
2. Không nhiễu: lợi thế của bản hội nghị được giữ. AnytimeSwarm hơn alns_fixed@40 (cùng compute) có ý nghĩa ở 5/6
   cấu hình (+0,46 đến +0,83 điểm).
3. Có nhiễu: lợi thế cùng compute nhỏ lại và phần lớn không có ý nghĩa. AnytimeSwarm hơn alns_fixed@40 với CI trên 0
   ở 2/12 cấu hình có nhiễu (low + trễ cao, κ = 1 và 10, +0,77 và +0,76 điểm). Ở 10 cấu hình còn lại, chênh lệch nằm
   trong [−0,09; +0,49] điểm, CI chứa 0. Tỉ lệ thắng theo nhiệm vụ vẫn 64–83%.
4. Chi phí trễ vẫn có tác dụng khi κ lớn. Ở κ = 50, AnytimeSwarm hơn alns_fixed 250 ms rõ ràng ở cả nhiễu low
   (+2,2 và +2,8 điểm) và mid không trễ (+1,8 điểm), với ít compute hơn khoảng 6 lần (38–42 ms so với 250 ms).
5. Bộ dừng tự tăng compute khi có nhiễu: thời gian tính trung bình mỗi lần gọi ở κ = 1 là 43 ms (nominal), 48 ms (low),
   53 ms (mid). Nhiễu làm kế hoạch cũ kém hơn nên search còn nhiều cải thiện để khai thác.
6. Validator độc lập: 0/4 779 kế hoạch vi phạm (`results/g0/validator.txt`).

## Go/No-Go

Tiêu chí đăng ký trước (kế hoạch mục 3b): ít nhất một cấu hình có nhiễu mà AnytimeSwarm hơn alns_fixed@40 với CI trên 0.
Kết quả 2/12, nên về hình thức là Go. Tuy vậy bằng chứng yếu và không nhất quán theo κ.
Kết luận trung thực: quy tắc dừng của bản hội nghị chuyển sang được môi trường có nhiễu mà không thua baseline nào,
nhưng lợi thế nhỏ hơn nhiều so với tổn thất do thực thi. Một bài journal chỉ dựa vào zero-shot transfer sẽ có đóng góp mỏng.

## Quyết định: Go có điều kiện, chuyển trọng tâm sang execution-aware AnytimeSwarm

Giữ AnytimeSwarm gốc làm phương pháp zero-shot (bằng chứng transfer). Phát triển phần mở rộng trên seed dev trước khi
đầu tư tầng C:
1. Replan theo độ lệch (deviation-triggered): ngoài sự kiện, gọi planner khi thời điểm hoàn thành dự kiến của một task
   lệch quá ngưỡng so với kế hoạch. Số lần gọi tăng nên phân bổ compute càng quan trọng; đây là nơi stopping rule có
   thể tạo khác biệt lớn hơn.
2. Chi phí trễ theo rủi ro: thay slack tất định bằng xác suất trễ deadline dưới phân phối thời gian hoàn thành
   (ước lượng từ dữ liệu dev, kiểm tra calibration), như công thức C_risk trong hướng dẫn gốc.
3. Hiệu chỉnh mức nhiễu và trễ bằng đo đạc PX4/Gazebo (G2–G4) trước khi đóng băng; mức hiện tại là tạm.
Mỗi biến thể so với cùng baseline, cùng compute, bootstrap theo nhiệm vụ, trên seed dev. Seed held-out
3000–3029 chỉ dùng sau khi đóng băng.

## Lưu ý khi diễn giải

Mức "low/mid" chưa được hiệu chỉnh nên độ lớn tổn thất (10–23 điểm) chưa phải số liệu để báo cáo. Kết quả pilot chỉ
dùng để chọn hướng; không đưa vào bài như bằng chứng.
