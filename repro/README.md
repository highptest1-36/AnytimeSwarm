# AnytimeSwarm

**Deadline-Aware Adaptive Computation for Dynamic Multi-UAV Task Replanning**
Paper 2 / 2 cho TAIMMA 2027 (hạn nộp 05/11/2026) · Multi-UAV · Dynamic task allocation · Anytime optimization · chỉ cần CPU.

> Câu hỏi nghiên cứu: *Một bộ lập kế hoạch anytime đang cải thiện lời giải. Khi nào tiếp tục tính toán còn đáng giá, và khi nào nên dừng để UAV nhận kế hoạch sớm hơn?*

---

## 1. Bắt đầu trong 5 phút

```powershell
cd D:\paper\TAIMMA_2027\AnytimeSwarm
.\.venv\Scripts\Activate.ps1                 # venv Python 3.11 đã tạo sẵn ngày 24/10 (numpy, sklearn, ortools...)
python experiments/00_check_env.py           # in "ENVIRONMENT OK" + 20 unit test pass
```
Tạo lại venv nếu cần: `py -3.11 -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt`.
Không cần GPU, PyTorch hay API key.

## 2. Thứ tự chạy (chi tiết: [docs/02_EXPERIMENT_PROTOCOL.md](docs/02_EXPERIMENT_PROTOCOL.md))

| Bước | Lệnh | Seeds | Thời gian* | Kết quả |
|---|---|---|---|---|
| 0 | `python experiments/00_check_env.py` | – | 5 s | thư viện + unit test |
| 1 | `python experiments/01_pilot_timing.py` | dev | 1–2 phút | thời gian ra lời giải khả thi đầu tiên, ms/vòng lặp |
| 2 | `python experiments/02_generate_snapshots.py --split dev` | dev | 1–2 phút | 90 kịch bản, ~530 snapshot |
| 3 | `python experiments/03_train_improvement_model.py` | dev | 5–6 phút | `models/improvement_model.json`, chọn μ |
| 4 | `python experiments/04_run_static.py --split dev --quick` | dev | 40–50 phút (≈30 phút là lời giải tham chiếu) | thử nghiệm snapshot tĩnh |
| 5 | `python experiments/05_run_closed_loop.py --split dev --quick` | dev | 5–10 phút | nhiệm vụ vòng kín |
| — | **ĐÓNG BĂNG CONFIG** → `configs/frozen_<ngày>.yaml` | | | |
| 2 | `python experiments/02_generate_snapshots.py --split test` | test | 2 phút | snapshot test |
| 4 | `python experiments/04_run_static.py --split test` | test | 2–3 giờ (chạy qua đêm; tham chiếu ≈ 1 giờ) | kết quả chính H1/H2 |
| 5 | `python experiments/05_run_closed_loop.py --split test` | test | 20–40 phút | kết quả H3 |
| 6 | `python experiments/06_bootstrap.py --split test` | – | 1 phút | CI 95% mức kịch bản/nhiệm vụ |
| 7 | `python experiments/07_make_figures.py --split test` | – | 30 s | `results/figures/*.pdf` → `paper/figures/` |
| 8 | `python experiments/08_make_tables.py --split test` | – | 5 s | `results/tables/*.tex` → `paper/tables/` |
| 9 | `python experiments/09_visualize_mission.py` | – | 5 s | quỹ đạo + Gantt |

\*đo trên laptop này ngày 24/10. `run_dev.ps1` / `run_test.ps1` chạy cả chuỗi.
Nếu PowerShell chặn script: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (chỉ áp dụng cho cửa sổ hiện tại).

## 3. Ý tưởng trong một hình

```
Sự kiện (task mới · UAV hỏng · deadline đổi)
        │
        ▼
Feasibility-First Repair  ── kế hoạch khả thi trong ~0.2–15 ms (giữ kế hoạch cũ, lọc vi phạm, chèn regret-2)
        │
        ▼
Anytime ALNS  ── luôn giữ lời giải tốt nhất; cooling theo vòng lặp ⇒ cùng seed = cùng quỹ đạo
        │            ▲
        ▼            │ tiếp tục
Adaptive Stopping Controller  (đóng góp chính)
   dừng khi  E[ΔJ trong H ms tới | lịch sử tìm kiếm]  ≤  C_delay(τ, H)  +  μ · scale · H
             (bộ dự đoán học trên dev)    (suy ra từ slack của kế hoạch)   (chi phí tính toán)
        │
        ▼
Phát hành kế hoạch tại t_now + κ · thời gian tính toán
```

## 4. Cấu trúc thư mục

```
AnytimeSwarm/
├── README.md, run_dev.ps1, run_test.ps1, requirements.txt
├── configs/default.yaml           thế giới, quy mô, hàm mục tiêu, ALNS, controller, ngân sách, κ
├── anytimeswarm/
│   ├── simulator/  entities, scenario (sinh kịch bản có seed), problem (ràng buộc, hàm mục tiêu,
│   │               trễ phát hành), executor (mô phỏng vòng kín theo sự kiện)
│   ├── algorithms/ insertion (cheapest, regret-k), repair (FFR), alns, local_search,
│   │               methods (registry mọi phương pháp), ortools_ref (solver tham chiếu)
│   ├── controller/ features (đặc trưng lịch sử tìm kiếm), improvement_model (learned/online),
│   │               delay_cost (C_delay từ slack), stopping (fixed / stagnation / adaptive)
│   ├── analysis.py (regret, net utility, bootstrap), plotting.py, utils.py
├── experiments/   00 → 09
├── tests/         test_feasibility, test_deadlines, test_energy, test_search (20 test)
├── docs/          kế hoạch, giao thức, tiến trình, nhật ký, kết quả, hướng dẫn viết bài
├── data/          kịch bản + snapshot (tự sinh)
├── models/        improvement_model.json
├── results/       registry.csv, pilot_timing.csv, static/, closed_loop/, traces/, bootstrap/, figures/, tables/, missions/
└── paper/         main.tex (LNCS), references.bib, figures/, tables/
```

## 5. Tài liệu
| File | Dùng khi nào |
|---|---|
| [docs/01_RESEARCH_PLAN.md](docs/01_RESEARCH_PLAN.md) | câu hỏi, giả thuyết, mô hình toán, định vị novelty, rủi ro |
| [docs/02_EXPERIMENT_PROTOCOL.md](docs/02_EXPERIMENT_PROTOCOL.md) | lệnh, tiêu chí chấp nhận, quy tắc công bằng |
| [docs/03_PROGRESS_TRACKER.md](docs/03_PROGRESS_TRACKER.md) | checklist hằng ngày, Go/No-Go, quyết định |
| [docs/04_EXPERIMENT_LOG.md](docs/04_EXPERIMENT_LOG.md) | nhật ký từng lần chạy |
| [docs/05_RESULTS_SUMMARY.md](docs/05_RESULTS_SUMMARY.md) | bảng số liệu cuối, ánh xạ hình/bảng ↔ bài báo |
| [docs/06_PAPER_WRITING_GUIDE.md](docs/06_PAPER_WRITING_GUIDE.md) | nội dung từng mục, mẫu câu claim, checklist nộp |

## 6. Ba quy tắc không được vi phạm
1. **Seed test (1000–1009) chỉ chạy sau khi khóa config.** μ, bộ dự đoán, tham số kịch bản đều chọn trên seed dev (0–9).
2. **Đo thời gian khi máy rảnh** — không chạy song song với RAVEN-UAV hay nhiều tiến trình Python; cắm sạc.
3. **Báo cáo trên toàn bộ snapshot/nhiệm vụ** — không lọc bỏ trường hợp phương pháp đề xuất thua; regret tính so với best-known (ALNS 3 s + OR-Tools), không gọi là "optimal".
