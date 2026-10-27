# Quan sát thí nghiệm: nhìn được AnytimeSwarm chạy ở từng tầng

Ngày 28/10/2026. Mục tiêu: mỗi loại thí nghiệm đều có cách nhìn tận mắt, không chỉ đọc bảng kết quả.

## 1. Gazebo, PX4, ROS 2, RViz2 khác nhau thế nào

| Thành phần | Vai trò | Ví von | Có cửa sổ? |
|---|---|---|---|
| Gazebo | mô phỏng thế giới vật lý: thân UAV, động cơ, gió, cảm biến giả | "thế giới thật" giả lập, giống engine game | có: cảnh 3D, thấy UAV bay |
| PX4 SITL | phần mềm lái (autopilot) chạy trên máy tính: ước lượng vị trí, giữ thăng bằng, bay tới điểm đặt | "phi công" | không; chỉ có shell `pxh>` |
| ROS 2 | hệ thống truyền tin giữa các chương trình (topic, message), cộng bộ công cụ (ghi log, vẽ, xem đồ thị) | "mạng bưu điện" nối các chương trình | bản thân không có |
| RViz2 | công cụ của ROS 2 vẽ dữ liệu: task, route, deadline, vị trí theo hiểu biết của planner | "màn hình điều phối" | có: bản đồ 2D/3D |
| AnytimeSwarm | planner: chia task cho UAV, quyết định lúc nào dừng tính | "người điều phối" | không; in log ra terminal |

Một UAV trong Gazebo bay được là nhờ cả chuỗi: Gazebo giả lập cảm biến, PX4 tính lệnh động cơ, ROS 2 chở lệnh
waypoint từ planner tới PX4 và chở vị trí từ PX4 về planner. Gazebo cho thấy "chuyện gì thật sự xảy ra", RViz2 cho thấy
"planner nghĩ gì".

## 2. Vì sao phần lớn thí nghiệm không chạy trong Gazebo

Pilot tầng B vừa chạy 9 720 nhiệm vụ, mỗi nhiệm vụ 30 phút mô phỏng. Trong Gazebo ở thời gian thực, việc đó mất khoảng
200 ngày, và laptop chỉ chạy được 3–5 UAV PX4 cùng lúc trong khi bài có quy mô tới 40 UAV. Vì vậy:
- Tầng B (Python, thời gian ảo) dùng cho thống kê: nhiều seed, nhiều mức nhiễu, tới 40 UAV. Chạy không giao diện,
  nhưng nhiệm vụ nào cũng xem lại được bằng viewer.
- Tầng C (Gazebo + PX4 + ROS 2) dùng để kiểm chứng trên vật lý thật với 3 UAV. Chạy được có cửa sổ để quan sát.
Cả hai tầng dùng cùng planner, cùng file kịch bản, cùng chú thích màu, để kết quả so sánh được với nhau.

Khi tôi chạy lệnh, tôi điều khiển Ubuntu qua dòng lệnh và không nhìn thấy màn hình, nên benchmark luôn chạy headless.
Cửa sổ Gazebo bạn từng thấy là lần tôi thử GUI: WSLg đưa cửa sổ của Ubuntu ra desktop Windows.

## 3. Ba chế độ quan sát

| Chế độ | Tầng | Dùng khi | Trạng thái |
|---|---|---|---|
| A. Xem lại nhiệm vụ tầng B | B | hiểu kết quả thống kê: vì sao phương pháp này thắng/thua ở một nhiệm vụ cụ thể | có ngay (`demo/live_mission.py`) |
| B. Trực tiếp: Gazebo + RViz2 | C | xem UAV PX4 bay theo kế hoạch AnytimeSwarm, sự kiện xảy ra, replan | xây ở G3 |
| C. Xem lại một lần chạy tầng C | C | benchmark chạy headless, sau đó xem bất kỳ lần chạy nào | xây ở G3–G4 (rosbag + log Gazebo) |

### Chế độ A — có ngay

```bash
wsl -d Ubuntu-24.04          # từ PowerShell
cd $J
~/venvs/atswarm/bin/python demo/live_mission.py
```
Một cửa sổ mở ra với hai bản đồ cạnh nhau: AnytimeSwarm (trái) và ALNS cố định 250 ms (phải), trên cùng một nhiệm vụ
(cùng task, cùng sự kiện, cùng gió và nhiễu). Tam giác màu là UAV kéo theo vệt bay, chấm cam là task đang chờ (to = thưởng
cao), xanh là phục vụ kịp, X đỏ là phục vụ trễ, X xám là bỏ lỡ. Hộp chữ cho biết thời gian nhiệm vụ, thưởng thu được,
lần replan gần nhất (lý do, số ms CPU, số vòng lặp, lý do dừng). Hãy để ý dòng "CPU": AnytimeSwarm thường dừng ở
30–50 ms, ALNS luôn dùng đủ 250 ms; khi κ lớn, 250 ms đó thành vài giây trễ khiến UAV phải đứng chờ.

Thử các tình huống khác (chỉ seed dev 0–9):
```bash
~/venvs/atswarm/bin/python demo/live_mission.py --scenario large-failures-3 --exec mid --kappa 50
~/venvs/atswarm/bin/python demo/live_mission.py --methods anytime,alns_fixed@40,alns_stagnation --kappa 10
~/venvs/atswarm/bin/python demo/live_mission.py --methods anytime --exec nominal --speed 120
~/venvs/atswarm/bin/python demo/live_mission.py --save ~/mission.gif        # ghi GIF thay vì mở cửa sổ
```
`--scenario`: small/medium/large – arrivals/failures/deadlines – seed. `--exec`: nominal, low, mid, high.
`--lat`: none, low, high. `--speed`: số giây nhiệm vụ mỗi giây thật.

### Chế độ B — trực tiếp trong Gazebo (mục tiêu của G3)

Một lệnh duy nhất:
```bash
ros2 launch atswarm_bringup demo.launch.py n_uav:=3 method:=anytime scenario:=gz-arrivals-0 gui:=true
```
sẽ khởi động: XRCE agent, 3 PX4 SITL, Gazebo có cửa sổ, `mission_manager` (phát task và sự kiện theo kịch bản),
`atswarm_planner` (AnytimeSwarm), `route_executor` + `px4_adapter` (biến route thành waypoint), `atswarm_viz`
(vẽ task, route, deadline lên RViz2) và RViz2. Bạn thấy ba thứ cùng lúc:
- Gazebo: 3 quadrotor X500 cất cánh, bay tới task, dừng phục vụ, bay tiếp.
- RViz2: bản đồ task với cùng chú thích màu như chế độ A, route hiện tại của từng UAV, task mới hiện ra khi có sự kiện,
  route vẽ lại sau mỗi lần replan.
- Terminal planner: mỗi lần replan in lý do, số ms, số vòng lặp, lý do dừng, dự báo cải thiện so với chi phí trễ.
Thế giới Gazebo được thu nhỏ theo tỉ lệ không thứ nguyên (khoảng 800 × 800 m thay vì 10 km) để nhìn thấy UAV và để
nhiệm vụ kết thúc trong 10 phút.

### Chế độ C — xem lại lần chạy tầng C

Benchmark tầng C chạy headless (nhanh, ổn định RTF). Mỗi lần chạy ghi:
- rosbag các topic `/atswarm/*` và vị trí UAV → `ros2 bag play <thư mục>` + RViz2 để xem lại đúng như lúc chạy;
- log Gazebo (`gz sim --record`) → mở lại bằng Gazebo GUI để xem chuyển động 3D;
- log `.ulg` của PX4 → PlotJuggler để xem quỹ đạo, vận tốc, sai số bám.

## 4. Trình tự hợp lý

1. Bây giờ: dùng chế độ A để hiểu cơ chế (mất vài giây cho một nhiệm vụ). Song song tôi phát triển execution-aware
   AnytimeSwarm trên tầng B (seed dev). Mọi biến thể mới đều xem được ngay bằng chế độ A.
2. G2–G3: xây các gói ROS 2 và `atswarm_viz` để có chế độ B. Mốc kiểm tra đầu tiên là bạn chạy được lệnh launch ở trên
   và thấy 3 UAV làm hết một nhiệm vụ nhỏ.
3. G4: đo sai số bay và độ trễ thật từ tầng C, hiệu chỉnh mức nhiễu tầng B. Chạy cùng một kịch bản ở tầng B và tầng C,
   xem cạnh nhau, để kiểm tra tầng B có mô phỏng đúng không.
4. G5: thí nghiệm chính. Tầng B chạy hàng loạt headless; tầng C chạy headless có ghi log; vài nhiệm vụ đại diện chạy lại
   có cửa sổ và quay video cho phần minh họa của bài và tài liệu bổ sung.
