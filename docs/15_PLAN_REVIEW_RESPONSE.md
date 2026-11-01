# 15 — Đánh giá bản phản biện "LTCC – tiêu chuẩn Q1" và kế hoạch cải thiện

Ngày: 2026-11-02. Bản thảo được đánh giá: `paper_journal/ieee/main.pdf` (IEEE Access, commit 523966f).
Bản phản biện chỉ có PDF chính, không có supplementary, code và log. Vì vậy một số góp ý hỏi về những thứ đã có
trong supplementary, còn một số góp ý khác thì đúng và đã được xác minh trên code/dữ liệu bên dưới.

## 1. Đánh giá tổng quát bản phản biện

- Số liệu reviewer trích (Table 5, 6, Study 4C, Study 6) khớp với bản thảo. Reviewer đọc kỹ, không bịa số.
- Điểm 7.4/10 và các điểm thành phần là chủ quan, không dùng để ra quyết định.
- Góp ý mạnh nhất (Critical #1) là đúng và đã được xác minh: đây là việc phải sửa đầu tiên.
- Hai trong sáu góp ý lớn một phần đã được giải quyết trong supplementary (reliability diagram, Ehmke et al. đã được
  trích và dùng làm baseline). Phải đưa các ý đó lên bản chính cho rõ hơn, không cần chạy thêm.
- Bài reviewer nêu ("Uncertainty-Gated Distributed Dynamic Task Allocation…", Qian & Fu, Drones 10(10):782, 2026,
  doi 10.3390/drones10100782) đã được trích trong bản thảo (`ucdg2026drones`) và đã được xác minh trong
  docs/09_RECENT_WORKS.md. (Đính chính 02/11: lần tìm web đầu không ra đúng tiêu đề, nhưng bài có thật.) Đã thêm một câu
  ở Related Work để phân biệt rõ hơn với LTCC.

## 2. Đối chiếu từng góp ý với nghiên cứu hiện tại

### C1 — Không khớp giữa chi phí trễ trong công thức và thước đo (CRITICAL) → ĐÚNG, phải sửa

Đã xác minh:
- Reward không đồng nhất: `original/configs/*.yaml` có `reward_levels: [1, 2, 3, 5]`, `reward_probs: [0.4, 0.3, 0.2, 0.1]`,
  nên w̄ = 2.1.
- `sections/method.tex` (Eq. theta, Prop. 2) và `journal_core/study5.py` giả định chi phí trễ là λ·w_j, nên θ = λ/(1+λ) cho mọi task.
- `sections/setup.tex` dòng 88 và `experiments/analyze_study5.py` chấm u_λ = U − λ·n_late/n. Vì U = R_đúng hạn/R_tổng,
  mỗi task trễ bị phạt λ·w̄ (mean reward của mission), không phải λ·w_j.
- Ngưỡng đúng theo thước đo này là θ_j = λw̄/(w_j + λw̄). Ở λ = 1: w=1 → 0.677, w=2 → 0.512, w=3 → 0.412, w=5 → 0.296
  (code đang dùng 0.5 cho tất cả). 40% task có reward 1 bị nhận ở ngưỡng quá thấp, còn task reward 5 bị từ chối ở ngưỡng quá cao.
- Log không lưu reward của các task trễ (chỉ có `late_served`), nên không thể chấm lại Study 5/6 bằng phạt theo w_j.

Hướng sai lệch: quy tắc cost-aware được đặt sai so với thước đo, còn các đối thủ (proportional buffer, z không fallback)
được tune trực tiếp trên thước đo đó. Vì vậy kết quả hiện tại nhiều khả năng bất lợi cho phương pháp, không phóng đại
nó. Dù vậy, Proposition 2(iii) ("expected contribution ≥ 0") không đúng với hàm mục tiêu được chấm, nên phải sửa.
Không thể chỉ sửa câu chữ.

Cách sửa (chi tiết ở Pha 0 và Pha 2):
1. Tổng quát lý thuyết: chi phí trễ c_j cho từng task, θ_j = c_j/(w_j + c_j), z_j = Φ⁻¹(θ_j). Đây vẫn là dạng đóng
   theo từng task. Có hai trường hợp đặc biệt: chi phí tỉ lệ (c_j = λw_j → θ = λ/(1+λ), như bản hiện tại) và phí cố định
   (c_j = λw̄ → θ_j phụ thuộc w_j, đúng với thước đo của Study 5/6).
2. Mô tả trung thực Study 5/6: quy tắc được chạy với ngưỡng của mô hình chi phí tỉ lệ nhưng được chấm theo phí cố định,
   tức là một trường hợp mô hình chi phí bị đặt sai. Không gọi lại đó là kết quả "khớp".
3. Study 7a trên seed mới: chạy cả hai biến thể, mỗi biến thể được chấm theo đúng thước đo của nó (xem Pha 2).

### C2 — Phạm vi của Proposition 1–2 → ĐÚNG MỘT PHẦN, chủ yếu sửa phát biểu

- A. Normality/calibration: đúng. Reliability diagram đã có (Supp. Fig. `fig:Scoverage`, Study 4). Còn thiếu: đánh giá
  vùng đuôi (p cao, nơi chance constraint có ý nghĩa), chỉ số tổng hợp (ECE, Brier), và kiểm tra khi phân phối không
  còn Gaussian. Thêm các phân tích này ở Pha 1 và Pha 2 (7b).
- B. Cắt min(d_j, d̃_j): đúng về mặt phát biểu, không ảnh hưởng tính đúng. Khi cắt, tập ràng buộc là giao của chance
  constraint với deadline danh nghĩa, chặt hơn ràng buộc chưa cắt. Vì vậy (ii) "xác suất ≥ Φ(z)" vẫn đúng, còn (i)
  "tương đương" chỉ đúng khi không cắt. Việc cắt có tác dụng khi z < 0 (ví dụ z_λ = Φ⁻¹(1/3) ≈ −0.43 ở λ = 0.5). Sửa:
  phát biểu (i) cho d̃ chưa cắt và thêm một câu nhận xét rằng việc cắt giữ nguyên (ii) và Prop. 2(iii).
- C. Nhánh 1 + b₁ + z_λs₁ ≤ 0.05: bản thảo đã nói nhánh này chỉ xảy ra khi λ < 0.03, và không bao giờ xảy ra với λ ∈ {0.5, 1, 2}
  dùng trong thực nghiệm. Tuy vậy, Prop. 2(iii) không đúng trong nhánh này. Sửa: giới hạn (iii) cho λ có
  1 + b₁ + z_λs₁ > 0.05 và ghi rõ nhánh này không xuất hiện trong thực nghiệm.
- Tiêu chí cục bộ: đúng. Câu "bỏ qua trễ gây ra cho các task phía sau" đang nằm sau Prop. 2. Đưa nó vào phát biểu như
  một "local break-even criterion" và nói rõ đây không phải quyết định tối ưu toàn cục.

### C3 — Đơn vị độc lập của bootstrap → CÓ CƠ SỞ, ĐÃ KIỂM TRA: KẾT LUẬN KHÔNG ĐỔI

Nguy cơ có thật: `journal_core/execution.py` sinh gió và sai số từng chặng theo `scenario.seed`, uav_id và task_id. Vì vậy
9 mission (scale × profile) cùng một seed dùng chung hướng gió và cùng các luồng sai số. Kịch bản (vị trí task, thời gian
xuất hiện) thì độc lập theo (scale, profile, seed).

Đã chạy paired cluster bootstrap theo seed (30 cluster, 10 000 lần lấy mẫu, script ở scratchpad `cluster_check.py`):

| So sánh | Bootstrap theo mission | Cluster theo seed |
|---|---|---|
| S4 H9 LTCC − proportional buffer | −0.38 [−0.72, −0.05], p .025 | [−0.69, −0.07], p .016 |
| S4 H10 LTCC − moment propagation | −0.25 [−0.62, +0.12], p .19 | [−0.61, +0.11], p .17 |
| S4 H12 LTCC − buffer 60 s | +4.22 [+3.74, +4.68] | [+3.87, +4.59] |
| S5 H16 CA(1) − nominal fallback, u₁ | +2.42 [+1.81, +3.02] | [+2.00, +2.83] |
| S5 H19 CA(1) − nominal model, u₁ | +11.75 [+10.88, +12.57] | [+11.12, +12.38] |
| S5 CA(2) − nominal fallback, u₂ | +7.25 [+6.40, +8.11] | [+6.55, +7.94] |

Khoảng tin cậy theo cluster không rộng hơn (phương sai của trung bình theo seed nhỏ hơn mức giả định độc lập), nên
không có tương quan dương nào làm CI ban đầu quá hẹp. Việc cần làm: chạy cho toàn bộ H1–H23 trong analysis script,
đưa vào một bảng supplementary và thêm một câu ở Section V-D. Không cần chạy thêm mô phỏng.

### C4 — Định vị tính mới → ĐỒNG Ý, chỉ sửa câu chữ

- Ehmke, Campbell & Urban (2015) đã được trích (`ehmke2015ensuring`) và chính là baseline moment propagation. Reviewer
  không thấy được điều này vì nó chưa đủ nổi bật trong phần đóng góp.
- Viết lại phần contributions: tính mới không nằm ở Gaussian chance constraint, ALNS hay CBBA, mà ở (a) sai số finish-time
  hiệu chuẩn theo lead time từ thực thi vòng kín, (b) effective deadline dạng đóng đưa thẳng vào heuristic có sẵn, và
  (c) quy tắc fallback break-even theo chi phí trễ, không phụ thuộc mô hình (H22: nó cũng cải thiện moment propagation
  +2.71 pp). Ý (c) là cách biến kết quả "MP + CA tốt hơn LTCC" thành điểm mạnh của đóng góp, thay vì một điểm yếu.
- Chỉ trích bài Drones sau khi đã đọc và xác minh được tiêu đề, tác giả và DOI.

### C5 — External validity và PX4 → ĐỒNG Ý LÀ GIỚI HẠN; KHÔNG BAY THẬT

Bay thật không khả thi (phần cứng, chi phí, không có nguồn hỗ trợ). Đây là một giới hạn hợp lệ, phải nêu thẳng trong
Limitations, không né. Những việc làm được trong khả năng hiện có:
- Đổi phân phối trong SITL (gió Gazebo thay đổi theo thời gian, độ trễ truyền thông khác lognormal), với mô hình được
  hiệu chuẩn trên điều kiện cũ. Đây đúng là câu hỏi reviewer đặt ra.
- Bay cost-aware fallback ở tier C, nhưng chỉ khi tính power cho thấy số chuyến bay khả thi (Pha 3).

### C6 — Độ tin cậy của calibration → ĐỒNG Ý; một phần đã có

Đã có: reliability diagram (Supp., Study 4), cột `cov_n*/cov_k*/cov_p*` (số task, số lần đúng hạn, xác suất dự đoán theo
10 bin) trong mọi log tier B từ Study 4 trở đi. Còn thiếu: diagram cho Study 5/6, ECE/Brier, coverage ở các mức z thực sự
dùng, và kiểm tra dưới phân phối Student-t, hỗn hợp, tương quan theo thời gian (Pha 2, 7b). Reviewer đánh giá thí nghiệm
này có giá trị hơn việc thêm thuật toán tìm kiếm mới. Tôi đồng ý.

### Metadata và trình bày

| Mục | Hiện trạng (đã kiểm tra) | Xử lý |
|---|---|---|
| `\doi{10.1109/ACCESS.2024.0429000}` | Placeholder của template | Thay bằng placeholder chung của IEEE Access hoặc bỏ |
| `\history{Date of publication xxxx…}` | Placeholder của template | Giữ dạng placeholder (journal tự điền) hoặc bỏ, theo hướng dẫn nộp bài |
| Footer `VOLUME 11, 2023` | Lấy từ bài đã accept dùng làm template | Sửa thành năm hiện tại hoặc bỏ |
| "Vietnam Aerospace University" | main.tex dòng 64 và 105 | Tác giả xác nhận tên chính thức (reviewer cho rằng là Vietnam Aviation Academy) |
| "pre-registered" | abstract, introduction, conclusion, declarations | Protocol được tác giả tự khóa bằng git commit và SHA-256, không qua registry bên ngoài. Đổi thành "protocol frozen before the held-out runs (commit hashes listed)". Lưu trữ repo trên Zenodo (DOI, không sửa được) |
| Data availability "sau khi xuất bản" | declarations.tex | Đưa link repo/Zenodo ngay khi nộp (IEEE Access phản biện single-blind) |
| Table 1 (✓/–) | | Rà từng ô với bản gốc của từng bài |
| Effect size | Đã có đơn vị thực tế (macro Y) | Nhấn mạnh hơn ở Results, giảm nhấn mạnh p-value |
| Phân phối reward | Chỉ có trong Supp. Table S1 | Đưa lên Section V (cần cho C1) |

## 3. Nên làm và không nên làm

Nên làm (theo thứ tự giá trị trên chi phí):
1. Sửa C1 (lý thuyết + Study 7a). Đây là lỗi thật duy nhất ảnh hưởng đến tính đúng.
2. Sửa phát biểu Prop. 1–2 (C2-B, C2-C, tiêu chí cục bộ). Chỉ là văn bản.
3. Cluster bootstrap cho toàn bộ giả thuyết (C3). Đã chứng minh được là rẻ và không đổi kết luận.
4. Calibration và distribution shift ở tier B (C6, Study 7b). Đây là thí nghiệm mới có giá trị nhất.
5. Định vị lại tính mới và thêm Limitations (C4, C5). Chỉ là văn bản.
6. Bộ artefact Zenodo và sửa metadata.

Không nên làm:
- Không cố thêm mô hình hay thuật toán để thắng proportional buffer hoặc moment propagation. Reviewer cũng khuyên vậy,
  và câu chuyện "biểu diễn đơn giản + quy tắc quyết định dùng được cho mọi mô hình" đã đủ mạnh.
- Không chấm lại các held-out cũ bằng thước đo mới rồi gọi đó là kết quả chính (post hoc). Chỉ được báo cáo như phân
  tích độ nhạy, và thực ra cũng không làm được vì thiếu reward của task trễ.
- Không tune lại trên các seed đã dùng (0–9 dev; 3000–12029 held-out đều đã dùng).
- Không bỏ các kết quả âm (H9, H10, H14). Chúng là lý do reviewer tin bài.
- Không bay thật, và không viết như thể SITL thay được bay thật.
- Không trích tài liệu reviewer gợi ý khi chưa tự xác minh.

## 4. Kế hoạch thực hiện

Seed mới (chưa dùng): 13000–13029 (7a), 14000–14029 (7b), 15000+ (tier C, nếu làm).
Mọi lần chạy đo thời gian đi qua `tools/run_guarded.py`. Runner tier C gọi `tools/px4_log_cleanup.sh` sau mỗi chuyến bay.

### Pha 0 — Sửa văn bản, không chạy gì (0.5–1 ngày)
- method.tex: tổng quát Eq. (theta) thành c_j, nêu hai trường hợp đặc biệt. Prop. 2 phát biểu theo θ_j, giới hạn (iii)
  cho miền mẫu số > 0.05, và thêm chữ "local".
- method.tex: nhận xét về việc cắt min(d, d̃) sau Prop. 1.
- setup.tex: phân phối reward; mô tả Study 5/6 là trường hợp chi phí bị đặt sai (ngưỡng tỉ lệ, chấm theo phí cố định).
- introduction/related: viết lại contributions (C4); đổi "pre-registered"; rà Table 1.
- discussion: thêm đoạn Limitations (một họ simulator, giả định Gaussian, không bay thật, SITL bị rescale).
- main.tex: DOI, footer, affiliation (sau khi tác giả xác nhận).

### Pha 1 — Phân tích lại dữ liệu có sẵn (1 ngày)
- `experiments/robust_cluster.py`: cluster bootstrap theo seed cho H1–H23 → `tables/tab_cluster.tex` (supp.).
- `experiments/paper_calib.py`: reliability diagram cho Study 5/6 từ các cột `cov_*`; ECE, Brier, coverage ở mức z đã
  chọn; tách theo mức nhiễu → supp. figure, kèm một câu và một con số ở bản chính.
- Effect size trong đơn vị thực tế cho các so sánh chính.

### Pha 2 — Study 7 ở tier B, protocol V7 khóa trước khi chạy held-out (2–3 ngày)
Code:
- `original/.../executor.py` hoặc lớp bọc journal: log thêm `late_reward` và `ontime_reward`.
- `journal_core/study7.py`: cost-aware fallback với z_j theo từng task (`cost=prop|fee`); làm tương tự cho moment propagation.
- `journal_core/execution.py`: tùy chọn `err_dist` = gauss (mặc định, kết quả cũ không đổi) | student_t(ν=3, cùng phương
  sai) | mixture (ví dụ 90/10, thành phần ngoại lai ×3 sd) | ar1 (sai số tốc độ tương quan dọc route của mỗi UAV); độ trễ
  có đuôi nặng. Test: với `gauss`, log phải trùng bit với trước.

7a — Tính nhất quán của mô hình chi phí (seed 13000–13029):
- Phương pháp: CA-prop (= Study 5), CA-fee (θ_j), MP-CA-fee, proportional buffer tune theo từng λ và từng thước đo
  (trên dev), z không fallback được tune, nominal fallback, nominal model.
- Thước đo: u_fee = U − λ·n_late/n (như cũ) và u_prop = (R_đúng hạn − λ·R_trễ)/R_tổng.
- Họ giả thuyết chính (Holm, λ = 1): H24 CA-fee > CA-prop trên u_fee; H25 CA-fee không thua (NI) proportional buffer
  được tune trên u_fee; H26 CA-prop không thua (NI) proportional buffer được tune trên u_prop. λ = 0.5 và 2 là thứ cấp
  (trước đây proportional buffer thắng ở λ = 2).

7b — Distribution shift (seed 14000–14029):
- Mô hình sai số và z giữ nguyên như hiệu chuẩn trên nhiễu Gaussian ở dev. Không hiệu chuẩn lại, vì mục đích là đo độ
  bền khi phân phối bị đặt sai.
- Điều kiện: Student-t, hỗn hợp, AR(1), độ trễ đuôi nặng, so với Gaussian làm đối chứng. Mức độ được chọn trên dev seed
  sao cho độ lệch chuẩn sai số tương đương mức high (chỉ khớp quy mô, không tune phương pháp).
- Phương pháp: nominal, buffer 60 s, proportional buffer, MP-CA, LTCC-CA.
- Kết quả: U và u₁; coverage dự đoán và thực tế; ECE. Giả thuyết: LTCC-CA hơn nominal dưới mọi shift (superiority);
  báo cáo mức suy giảm coverage, không có giả thuyết về vị trí xếp hạng.
- Dev check trước khi khóa (seed 0–9): chạy thử để chắc code và độ lớn shift hợp lý, rồi khóa commit + SHA-256 trong
  `docs/16_PROTOCOL_V7.md`.

Thời gian máy ước tính dựa trên Study 5/6 (mỗi study chạy xong trong khoảng một ngày trên laptop này). Sẽ tính lại sau dev check.

### Pha 3 — Tùy chọn: tier C (2 ngày, chỉ làm nếu power cho phép)
- Tính power trước từ SD của hiệu theo mission ở 7a/7b. Mỗi chuyến bay khoảng 4.3 phút.
- Thiết kế: gió Gazebo thay đổi theo thời gian (khác điều kiện hiệu chuẩn), 3 phương pháp (nominal, LTCC + nominal
  fallback, LTCC-CA), chấm u₁.
- Nếu số mission cần cho power 80% vượt khoảng 40 (≈ 3 × 40 × 4.3 phút ≈ 9 giờ bay, chưa tính lặp lại do RTF), chỉ báo
  cáo như một kiểm tra nhất quán (cùng dấu, tương quan tier B–C), không đặt giả thuyết.

### Pha 4 — Viết lại bản thảo (1–2 ngày)
- Results thêm Study 7; abstract và conclusion theo các kết quả đã có; phần tóm tắt giả thuyết thêm H24–H26.
- Viết một "self-response" (`docs/17_RESPONSE_MATRIX.md`): mỗi góp ý → thay đổi → vị trí trong bản thảo. Dùng lại khi trả lời reviewer thật.
- Build main + supplementary (pdflatex + bibtex), kiểm tra log, không mở PDF.

### Pha 5 — Bộ artefact (0.5 ngày)
- Tag git, release và Zenodo DOI (code, config, các file SHA-256 đã khóa, CSV kết quả, script phân tích).
- README "reproduce a table" cho từng bảng và hình chính.
- Cập nhật Data and Code Availability bằng DOI.

## 5. Tiêu chí hoàn thành

- C1: lý thuyết và thực nghiệm dùng cùng một mô hình chi phí; Study 7a báo cáo đủ, kể cả khi H24–H26 không thỏa.
- C2: mỗi proposition chỉ khẳng định những gì đúng dưới giả định đã nêu.
- C3: bảng cluster bootstrap cho mọi giả thuyết chính.
- C6/C5: reliability + ECE ở bản chính hoặc supp.; kết quả distribution shift; Limitations nêu rõ không có bay thật.
- Không còn placeholder template, không còn chữ "pre-registered" khi không có registry, có DOI artefact.
