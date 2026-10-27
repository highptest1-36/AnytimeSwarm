# G0 — Tái lập bản hội nghị trên Linux

Ngày 27/10/2026. Số liệu chi tiết: `results/g0/stage_a.txt`, `results/g0/compare.md`, `results/g0/validator.txt`.
Script: `tools/g0_stage_a.sh`, `tools/g0_stage_b.sh`, `tools/g0_compare.py`, `tools/independent_validator.py`.

## Thiết lập

| | Bản hội nghị (24/10) | Tái lập (27/10) |
|---|---|---|
| Hệ điều hành | Windows 11 | WSL2 Ubuntu 24.04 trên cùng laptop |
| Python | 3.11.9 | 3.11.9 (uv, `~/venvs/atswarm311`); kiểm tra thêm 3.12.3 (`~/venvs/atswarm`) |
| Gói | numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, scikit-learn 1.9.1, ortools 9.15.6755 | giống hệt |
| Config | `configs/frozen_2026-10-24.yaml` (sha256 2b8c25a5…) | cùng file |
| Predictor | `models/improvement_model.json` (sha256 b22254d9…) | cùng file cho static và closed loop; một bản train lại trên Linux để so sánh |
| Seed | dev 0–9 (90 nhiệm vụ, 531 snapshot) | giống |
| CPU | i7-11800H | giống; guard Linux chặn RAVEN và PX4/Gazebo chạy song song (không phải chờ lần nào) |

Không chạy lại seed test (1000–1009, 2000–2029). Quyết định D1 cho phép chạy lại test2 một lần để kiểm tra tính tất
định; việc này chưa làm và không cần cho kết luận dưới đây.

## Kết quả

Quy ước: số ngoài ngoặc là lần chạy Linux, số trong ngoặc là bản hội nghị trên Windows.

1. Phần tất định (không phụ thuộc thời gian). 90 kịch bản dev giống bản gốc đến từng bit. 531 snapshot giống ở
   99,978% số giá trị; 315 chỗ khác nằm hết ở trường năng lượng, lệch 1 ulp (tối đa 7,3e-12 trên giá trị khoảng 10⁴),
   do thư viện toán Windows và Linux làm tròn khác nhau. Route, tập task, thời gian và deadline giống hệt.
   Python 3.11.9 và 3.12.3 trên Linux cho snapshot giống hệt nhau, nên planner chạy được trong node ROS 2 (Python 3.12)
   mà không đổi kết quả.
2. Lời giải tham chiếu (ALNS 3 s, OR-Tools 5 s, giới hạn thời gian). Best-known giống hệt ở 99,2% snapshot, chênh
   trung bình 1,1e-5 (tương đối), lớn nhất 0,46%.
3. Predictor train lại từ trace Linux. 52 035 mẫu (Windows 52 031). AUC out-of-fold 0,922 (0,926), Spearman 0,167
   (0,167), MAE 0,0113 (0,0113). Hệ số chuẩn hóa có cosine similarity 0,997. Quy tắc chọn mu cho cùng mu = 1e-5,
   thời gian dừng trung bình 38,7 ms (38,9 ms).
4. Tốc độ tìm kiếm. Linux nhanh hơn 21%: 10,2 vòng ALNS/ms so với 8,4 trên Windows (alns_fixed 500 ms). Do đó ở cùng
   ngân sách ms, regret trên Linux thấp hơn một chút (ví dụ alns_fixed 20 ms: 0,155% so với 0,180%).
5. Benchmark static, bootstrap theo kịch bản. Trong 405 phép so sánh AnytimeSwarm với baseline (theo quy mô, ngân sách,
   kappa), dấu của chênh lệch trùng ở 89,6%, kết luận có ý nghĩa thống kê trùng ở 96,0%. Các trường hợp đổi kết luận
   đều là CI chạm sát 0 ở cả hai lần chạy (ví dụ large, 20 ms, so với alns_fixed: Linux [-0,0006; 0,0139],
   Windows [0,0001; 0,0203]).
6. Closed loop, 90 nhiệm vụ. Utility trung bình của mỗi (phương pháp, kappa) lệch nhau tối đa 0,0021. Ví dụ ở kappa = 50:
   AnytimeSwarm 0,890 (0,889), alns_fixed 0,855 (0,856), alns_fixed@40 0,883 (0,881), alns_stagnation 0,884 (0,882).
   Kết luận có ý nghĩa thống kê trùng ở 42/45 phép so sánh; 3 trường hợp khác là CI sát 0.
7. Kiểm tra cùng compute (offline, gộp mọi quy mô), là kết luận chính của bài. Cả 24 dòng trùng cả dấu lẫn ý nghĩa.
   Ví dụ regret ở kappa = 1 so với fixed: −0,046 (−0,047), so với stagnation: −0,036 (−0,031); eff_regret ở
   kappa = 50 so với fixed: −0,163 (−0,168).

## Kết luận G0

Kết quả của bản hội nghị tái lập được trên Linux. Phần tất định trùng đến sai số làm tròn. Phần đo thời gian cho cùng
kết luận chính; chênh lệch số tuyệt đối giải thích được bằng tốc độ CPU/OS (Linux nhanh hơn 21%). Từ đây, mọi thí
nghiệm journal chạy trên Linux và báo cáo tốc độ tìm kiếm (vòng/ms) cùng kết quả, để người đọc quy đổi giữa máy.

Validator độc lập: xem `results/g0/validator.txt`.
