# Việc tác giả cần tự kiểm tra trước khi nộp journal

Những mục dưới đây tôi không tự xác minh được (cần truy cập thư viện, quyết định của nhóm tác giả, hoặc thông tin
cá nhân). Đánh dấu [x] khi xong.

## Tài liệu tham khảo
- [ ] Mở từng DOI trong `paper_journal/references.bib` (8 mục thêm cho journal ở cuối file). Mục cần chú ý nhất:
      `ponda2012chance` (ACC 2012, trang 4528–4533, DOI 10.1109/ACC.2012.6315626), xác nhận trang và DOI.
- [ ] Các mục kế thừa từ bản hội nghị đã có ghi chú kiểm tra trong `D:\paper\TAIMMA_2027\AnytimeSwarm\docs\07_MANUAL_TODO.md`
      (Horvitz 1987 số trang, Hansen & Zilberstein 2001 bản đầy đủ). Kiểm tra lại các mục còn mở ở đó.
- [ ] Các bài 2026 (`hwang2026apr`, `shen2026localrepair`, `ucdg2026drones`, `alnsdvrp2024`): xác nhận đã xuất bản
      chính thức, đúng tập/trang.

## Tác giả và khai báo
- [ ] Danh sách tác giả, thứ tự, đơn vị, email, tác giả liên hệ (đang giữ như bản hội nghị).
- [ ] Mục CRediT trong `paper_journal/sections/declarations.tex`: vai trò từng người cho đúng thực tế.
- [ ] Lời cảm ơn và nguồn tài trợ (nếu có mã đề tài).
- [ ] Khai báo sử dụng công cụ AI theo chính sách của Elsevier, nếu nhóm tác giả có dùng (Elsevier yêu cầu mục
      "Declaration of generative AI and AI-assisted technologies in the writing process").
- [ ] ORCID của từng tác giả khi nộp trên Editorial Manager.

## Lựa chọn journal và định dạng
- [ ] Journal đích (đang để Robotics and Autonomous Systems). Kiểm tra Guide for Authors hiện hành: giới hạn từ của
      abstract, highlights (3–5 gạch đầu dòng, mỗi dòng ≤ 85 ký tự, file riêng), graphical abstract (tùy chọn).
- [ ] Bài không còn nộp TAIMMA. Nếu bản hội nghị đã từng gửi đi đâu, nêu trong thư gửi biên tập (cover letter).
- [ ] Kho mã công khai: chọn nơi (GitHub/Zenodo) và cập nhật mục "Data and code availability". Hiện repo GitHub
      `highptest1-36/AnytimeSwarm` chưa được force-push lịch sử mới đứng tên Cao-Phuc Ha (xem hướng dẫn trong chat).

## Văn phong (quy tắc của bạn đã áp dụng)
- Câu ngắn, không "we/our", claim mềm, không gạch đầu dòng, không in đậm/nghiêng trong thân bài, số tuyệt đối kèm
  tương đối. Bản journal CÓ mục Discussion and limitations vì journal thường yêu cầu; nếu không muốn, có thể gộp vào
  Conclusion.
