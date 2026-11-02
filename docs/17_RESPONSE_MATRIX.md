# 17 — Bảng đối chiếu góp ý phản biện → thay đổi trong bản thảo

Nguồn góp ý: bản phản biện "LTCC – tiêu chuẩn Q1" (đánh giá ở docs/15_PLAN_REVIEW_RESPONSE.md).
Mỗi dòng: góp ý → việc đã làm → vị trí (file/mục) → trạng thái. Dùng lại khi viết thư trả lời reviewer thật.

| # | Góp ý | Việc đã làm | Vị trí | Trạng thái |
|---|---|---|---|---|
| C1 | Chi phí trễ λw_j trong Eq. (6) không khớp với điểm u_λ (phạt λw̄) | Tổng quát hóa: chi phí c_j, θ_j = c_j/(w_j+c_j), hai mô hình (tỉ lệ / cố định); Prop. 2 theo từng task; nêu rõ Study 5–6 dùng mô hình tỉ lệ nhưng chấm theo phí cố định; Study 7a chạy cả hai quy tắc, mỗi quy tắc chấm đúng thước đo của nó, đối thủ được tune lại cho từng thước đo | method.tex §Cost-aware fallback, Alg. 1, bảng ký hiệu; setup.tex (Study 5, Study 7); results §Study 7; journal_core/study7.py | Xong. 7a: H24 không có ý nghĩa (+0.24), H25 hỗ trợ (+1.34, sup.), H26 NI (+0.20); ở λ=2 quy tắc khớp thước đo bắt kịp buffer đã tune |
| C2-A | Giả định Gaussian, calibration ở đuôi | Câu nói rõ bảo đảm chỉ đúng dưới mô hình; mục Supp. calibration (ECE, đuôi p ≥ 0.8) cho Study 4–6; Study 7b thử các sai số ngoài mô hình | method.tex sau Prop. 1; supplementary §Calibration; results §Study 7 | Xong. 7b: 8/8 giả thuyết được hỗ trợ; đuôi chỉ hơi lạc quan khi có trễ dài hiếm gặp (92.6% so với 93.6%) |
| C2-B | Phép cắt min(d_j, d̃_j) | Nhận xét: phép cắt làm ràng buộc chặt hơn, (ii) vẫn đúng, (i) chỉ cho d̃ chưa cắt; chứng minh Prop. 2(iii) nhắc điều này | method.tex sau Prop. 1, chứng minh Prop. 2 | Xong |
| C2-C | Nhánh mẫu số ≤ 0.05 | Giả định của Prop. 2 loại nhánh này; ghi rõ nhánh này không có bảo đảm và chỉ xảy ra khi θ_j < 0.03, không xuất hiện trong thực nghiệm | method.tex sau Prop. 2 | Xong |
| C2-D | Tiêu chí cục bộ | Prop. 2(iii) đổi tên thành "Local break-even" + đoạn nói rõ không bảo đảm tối ưu toàn tuyến | method.tex | Xong |
| C3 | Đơn vị độc lập của bootstrap | Cluster bootstrap theo seed cho 36 kiểm định tier B (H1–H28): 35/36 giữ nguyên; H9 đổi sang "buffer tốt hơn có ý nghĩa" (p_Holm 0.032) | setup.tex §Protocol; Supp. §Sensitivity, Table S-cluster; experiments/robust_cluster.py | Xong |
| C4 | Định vị tính mới (Ehmke 2015, Qian & Fu 2026) | Contributions viết lại: Gaussian CC, kiểm tra khả thi cắm vào heuristic, ALNS, CBBA đều không mới; đóng góp nằm ở giao diện (sai số theo lead time hiệu chuẩn từ vòng kín → deadline dạng đóng) và quy tắc quyết định (break-even theo chi phí trễ, dùng được cho MP); thêm câu phân biệt với Qian & Fu | introduction.tex; related.tex | Xong |
| C5 | External validity, PX4 | Không bay thật (không có thiết bị/kinh phí) → nêu thẳng trong Limitations; Study 7b thay đổi phân phối sai số và độ trễ ở tier B | discussion.tex; results §Study 7 | Xong. Ưu thế so với nominal còn 4.83–5.67 pp dưới 4 dạng sai số lệch (so với 5.34 pp khi Gaussian) |
| C6 | Reliability diagram, coverage | Supp. Fig. calibration cho Study 4–6 (+7b), ECE, Brier (7b), đuôi | supplementary §Calibration; experiments/paper_calib.py | Xong (4–7b) |
| M1 | DOI/history/footer của template | DOI → `10.1109/ACCESS.2026.DOI`, footer → `VOLUME XX, 2026`; history giữ placeholder chuẩn của IEEE Access | main.tex | Xong |
| M2 | Affiliation | Giữ nguyên theo yêu cầu tác giả | — | Không đổi |
| M3 | "Pre-registered" | Đổi thành protocol được khóa trước held-out (SHA-256 + commit), nói rõ không nộp registry ngoài | abstract, intro, setup, conclusion, supp, tab_hyp | Xong |
| M4 | Data availability chỉ hứa sau xuất bản | Theo quyết định của tác giả (02/11): "available from the authors upon reasonable request"; code lưu ở repo private, cung cấp khi tạp chí yêu cầu | declarations.tex | Xong |
| M5 | Table 1 ✓/– | Mỗi ô dựa trên bằng chứng ghi trong docs/09_RECENT_WORKS.md (lập 01/11); lần này chưa đọc lại bản gốc từng bài | tables/tab_related.tex | Nên tác giả rà lại trước khi nộp |

## Vòng 2 (02/11/2026)

| # | Góp ý vòng 2 | Việc đã làm | Vị trí | Trạng thái |
|---|---|---|---|---|
| R2-1 | Ngưỡng phí cố định dùng w̄=2.1, còn u_λ phạt λW/n | Giữ quy tắc (W chưa biết khi nhiệm vụ đang chạy; dùng W/n là thông tin tương lai, chạy lại trên seed held-out đã dùng sẽ vi phạm protocol). Thêm điểm u'_λ = U − λw̄ n_late/W khớp chính xác với c_j = λw̄; chấm lại 7a: H24 +0.26, H25 +1.35, λ=2 +0.10 (không đổi kết luận). W/n: trung bình 2.10, CV 8%, 1.64–2.76 | setup.tex Study 7; results 7a; supp Table S-s7const; experiments/paper_s7const.py | Xong |
| R2-2 | Hình 1 còn λ/(1+λ) | Đổi thành c_j/(w_j+c_j); chú thích Hình 1 cập nhật; sửa luôn chữ bị cắt "feasibility-first repair" | figures_src/fig_overview.tex; method.tex | Xong |
| R2-3 | "better or equal" ở λ=2 | Abstract, Introduction, Results, Discussion: "không khác biệt có ý nghĩa, chưa chứng minh tương đương"; buffer vẫn hơn khi chi phí tỉ lệ | abstract, introduction, results, discussion | Xong |
| R2-4 | Prop. 1: s(h) ≥ 0 và trường hợp s(h)=0 | Thêm giả định s0,s1 ≥ 0 và nhánh tất định trong chứng minh | method.tex | Xong |
| R2-5 | "Robustness under the tested model departures" | Abstract, Introduction, Discussion, Conclusion dùng "four tested departures" và nói rõ không suy ra cho mọi sai số | các mục tương ứng | Xong |
| R2-6 | Chú thích Hình 8 | Nêu đủ bốn điều kiện và tham số; control không thuộc họ giả thuyết chính | results.tex | Xong |
| R2-7 | Đánh đổi utility–budget (5–40 ms) | Không có dữ liệu (held-out chỉ 40 ms); bỏ câu suy đoán "tight budget", nêu ưu điểm thực của dạng đóng (đơn giản, cắm được vào CBBA), MP hơn khi chi phí trễ cao | discussion.tex | Xong (không chạy mới) |
| R2-8 | Bootstrap theo block | Đã đúng: trung bình mỗi mission qua cấu hình rồi mới cluster theo seed | — | Không cần sửa |
| R2-9 | Reproducibility package | Giữ "upon reasonable request" theo quyết định tác giả; chuẩn bị sẵn REPRODUCE.md + gói zip cục bộ | REPRODUCE.md; ../submission_package/ | Xong |
| R2-10 | PX4 cho cost-aware fallback | Không làm (power thấp, reviewer không bắt buộc); đã nằm trong Limitations/Future work | — | Không làm |
