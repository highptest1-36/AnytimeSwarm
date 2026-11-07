# Bản thảo LTCC cho Aerospace Science and Technology (AST)

## Hai thư mục

| Thư mục | Dùng để |
|---|---|
| `../AST_submission/` | **nộp bài**: một cấp, không thư mục con. `main.tex` tự chứa (số liệu, bảng, danh mục tài liệu, tham chiếu phụ lục đã ghi thẳng vào), `cas-dc.cls`, `cas-common.sty`, `cas-email.jpeg`, `Figure_1` … `Figure_8` (PDF), `main.pdf`, `Supplementary_material.pdf`, `Highlights.docx`, `Vitae.docx` |
| `overleaf_revised_manuscript/` (thư mục này) | **bản nguồn để sửa tiếp**: `main.tex`, `supplementary.tex`, `figures/`, `tables/`, `supp/`, script trong `_build/` |

Biên dịch thư mục nộp: `pdflatex main.tex` hai lần. Sau mỗi lần sửa nguồn, tạo lại thư mục nộp:
`python _build/assemble.py`, `python _build/make_supp.py`, `python _build/hyphens.py`, `bash _build/build.sh`,
`python _build/inline_bbl.py`, `python _build/hyphens.py`, `bash _build/build.sh`, `python _build/flatten.py`,
`python _build/make_submission_files.py`.

## Đã hoàn tất theo hướng dẫn AST

Bài 15 trang (cộng 1 trang highlights), abstract 170 từ, 6 keywords ngắn, 5 highlights ≤ 85 ký tự, trang tiêu đề có
ORCID và địa chỉ của 4 tác giả, CRediT, competing interest, funding, data availability, acknowledgements, tài liệu
kiểu elsarticle-num với tên tạp chí viết tắt LTWA và DOI, hình nộp riêng (Fig. 4 tách 4a/4b), vitae kèm ảnh, dấu
"–" đổi thành "-", không còn trang trống lớn.

## Còn lại cho anh/chị

1. **Khai báo AI** (Elsevier bắt buộc): tự viết, đặt ngay trước References. Vị trí đã để sẵn bằng một dòng chú thích
   trong `_build/back.tex` (và trong `main.tex` của thư mục nộp, trước "Acknowledgements").
2. **Duong Thanh Tran:** thiếu ảnh và tiểu sử (≤ 100 từ) cho `Vitae.docx`; tiểu sử hiện chỉ ghi đơn vị.
3. **CRediT:** đã chia vai trò hợp lý (Ha: ý tưởng, phương pháp, phần mềm, thí nghiệm, phân tích, dữ liệu, hình, bản
   thảo; Nguyen: kiểm chứng, thí nghiệm, hình, góp ý; Tran: phương pháp, phân tích, kiểm chứng, góp ý; Le: ý tưởng,
   phương pháp, hướng dẫn, nguồn lực, quản lý, góp ý). Anh/chị kiểm tra lại với các đồng tác giả.
4. **GitHub (Data availability trỏ tới https://github.com/highptest1-36/LTCC):**
   - repo cũ `AnytimeSwarm` hiện đang **public** và chứa toàn bộ lịch sử: bản thảo IEEE, tài liệu kế hoạch, phản hồi
     reviewer. Nên chuyển nó về **private** (Settings → General → Danger Zone → Change visibility).
   - tạo repo **trống, public** tên `LTCC` (không tạo README) rồi báo để push bản sạch đã chuẩn bị ở
     `D:\paper\TAIMMA_2027\AnytimeSwarm\LTCC_public` (code, protocol, kết quả thô, không có bản thảo).
5. **Declaration of competing interest:** điền công cụ khai báo trực tuyến lúc nộp (sinh file Word).
6. **Cover letter:** chưa soạn; cần thì tôi soạn.
