# Hướng dẫn thực hành: tự chạy ROS 2 + PX4 + Gazebo và xem UAV bay

Mục tiêu: tự gõ từng lệnh, hiểu mỗi thành phần làm gì, nhìn UAV cất cánh, bay theo waypoint, hạ cánh.
Tất cả lệnh dưới đây đã chạy thử trên laptop này ngày 27/10/2026 (PX4 v1.17.0, ROS 2 Jazzy, Gazebo 8.15.0).

## 0. Bức tranh tổng thể

```
 Gazebo (gz sim)                 PX4 SITL (autopilot)                    ROS 2
 ─────────────────               ──────────────────────────               ──────────────────────────
 thế giới 3D, vật lý,   <──────> gz_bridge                                node của bạn:
 động cơ, cảm biến giả           EKF2 (ước lượng vị trí)                  offboard_waypoints.py
 (/clock, RTF)                   controller vị trí/tư thế                 (sau này: AnytimeSwarm
                                 commander (arm, mode, failsafe)           planner + route executor)
                                 uxrce_dds_client ──UDP 8888──> MicroXRCEAgent ──DDS──> topic /fmu/...
                                 mavlink ──────────UDP 14550──> QGroundControl (bản đồ, trạng thái)
```

Gazebo giả lập vật lý: thân máy bay, 4 động cơ, IMU, GPS, khí áp kế. PX4 là phần mềm lái thật, chạy trên máy tính thay vì
trên flight controller. PX4 đọc cảm biến giả, ước lượng vị trí bằng EKF2 và tính lệnh động cơ. Micro XRCE-DDS Agent là
cầu nối: nó đưa các topic uORB bên trong PX4 ra thành topic ROS 2 (`/fmu/out/...`) và nhận lệnh từ ROS 2 (`/fmu/in/...`).
Node ROS 2 của bạn không điều khiển động cơ. Nó chỉ gửi điểm đặt (setpoint) vị trí; PX4 tự lo việc bay tới đó.

Hai khung tọa độ cần nhớ:
- PX4 dùng NED cục bộ: x = Bắc, y = Đông, z = hướng xuống. Gốc là điểm UAV xuất phát. Bay cao 5 m nghĩa là z = -5.
- Gazebo và ROS dùng ENU: x = Đông, y = Bắc, z = hướng lên. `PX4_GZ_MODEL_POSE="5,0"` nghĩa là đặt UAV cách gốc 5 m về phía Đông.

## 1. Mở Ubuntu

Từ PowerShell hoặc Windows Terminal:
```powershell
wsl -d Ubuntu-24.04
```
Bạn vào bằng user `highp`. Mỗi terminal mới đã tự nạp ROS 2, `px4_ros_ws`, cấu hình GPU, và biến `$J` trỏ tới
`/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal` (xem cuối `~/.bashrc`).

Cần nhiều terminal cùng lúc. Trong Windows Terminal, mỗi tab mới gõ lại `wsl -d Ubuntu-24.04`, hoặc chọn profile
"Ubuntu-24.04" trong menu mũi tên xuống. Có thể mở thư mục trong VS Code: `code $J` (cần extension WSL).

Kiểm tra nhanh:
```bash
printenv ROS_DISTRO            # jazzy
gz sim --versions              # 8.15.0
which MicroXRCEAgent
glxinfo -B | grep renderer     # D3D12 (NVIDIA GeForce RTX 3060 Laptop GPU)
```

## 2. Bài 1: một UAV, điều khiển bằng tay trong shell PX4

Terminal 1, cầu nối DDS:
```bash
MicroXRCEAgent udp4 -p 8888
```
Chưa thấy gì là bình thường. Khi PX4 chạy, agent sẽ in ra các dòng `create_topic`.

Terminal 2, PX4 + Gazebo có giao diện:
```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```
Cửa sổ Gazebo mở ra với một quadrotor X500 trên mặt đất. Terminal 2 thành shell PX4 với dấu nhắc `pxh>`.
Đợi tới dòng `Ready for takeoff!`.

Trong `pxh>` gõ:
```
param set NAV_DLL_ACT 0
commander takeoff
```
Lệnh `param set` cho phép arm khi không có trạm mặt đất (GCS). Nếu thiếu lệnh này sẽ gặp
`Arming denied: Resolve system health failures first`. Giá trị được lưu cho instance 0, lần sau không cần đặt lại.
Sau `commander takeoff`, UAV tự arm và bay lên khoảng 2,5 m rồi giữ vị trí.

Xem trạng thái ngay trong PX4 (không qua ROS):
```
listener vehicle_local_position     # x, y, z theo NED; z âm khi đang bay
listener vehicle_status             # arming_state, nav_state
commander land
```
Sau khi hạ cánh, PX4 tự disarm (`Disarmed by landing`).

Trong cửa sổ Gazebo: kéo chuột trái để xoay, chuột phải để zoom. Click phải vào x500 → Follow để camera đi theo UAV.

Thoát: gõ `shutdown` trong `pxh>` hoặc nhấn Ctrl+C. Gazebo đóng theo.

## 3. Bài 2: nhìn UAV qua ROS 2

Giữ Terminal 1 (agent) và Terminal 2 (PX4) đang chạy. Mở Terminal 3:
```bash
ros2 topic list | grep fmu                     # khoảng 65 topic; /fmu/out = PX4 gửi ra, /fmu/in = PX4 nhận vào
ros2 topic echo /fmu/out/vehicle_local_position_v1 --field z
ros2 topic hz /fmu/out/vehicle_odometry       # khoảng 100 Hz
ros2 node list
rqt_graph                                      # sơ đồ node và topic
```
Gõ `commander takeoff` ở Terminal 2 rồi nhìn giá trị `z` ở Terminal 3 giảm từ 0 xuống khoảng -2,5 (đo thử: -2,48).

Ba điểm cần biết:
- PX4 phát dữ liệu với QoS best-effort. Lệnh `ros2 topic echo/hz` của Jazzy tự khớp QoS. Trong code thì phải tự khai
  báo subscriber best-effort; nếu để mặc định (reliable) sẽ không nhận được gì (xem `qos` trong script demo).
- PX4 1.17 thêm hậu tố phiên bản vào một số topic: `vehicle_local_position_v1`, `vehicle_status_v1`.
- Với instance 0, topic là `/fmu/...`. Với `px4 -i N` (N ≥ 1), topic là `/px4_N/fmu/...`.

## 4. Bài 3: ROS 2 điều khiển UAV bay theo waypoint (Offboard)

Đây là cơ chế mà AnytimeSwarm sẽ dùng sau này. Giữ Terminal 1 và 2; UAV đang ở dưới đất và đã disarm. Terminal 3:
```bash
python3 $J/demo/offboard_waypoints.py
```
UAV cất cánh lên 5 m, bay hình vuông 15 × 15 m, dừng 3 s ở mỗi góc (giống thời gian phục vụ một task), quay về rồi hạ cánh.
Log mẫu (đã chạy thử):
```
[t=   1.0s] Offboard + arm requested
[t=   7.2s] reached waypoint 0 NED=(0.0,0.0,-5.0), holding 2s (service)
[t=  12.2s] reached waypoint 1 NED=(15.0,0.0,-5.0), holding 2s (service)
...
[t=  28.8s] route finished -> LAND
```
Đổi route: `--wps "bắc,đông,cao;..."` tính bằng mét, ví dụ
```bash
python3 $J/demo/offboard_waypoints.py --wps "0,0,8;30,0,8;30,30,12;0,0,8" --hold 5
```

Đọc code [demo/offboard_waypoints.py](../demo/offboard_waypoints.py) theo thứ tự sau:
1. `tick()` chạy 10 lần mỗi giây. Lần nào cũng gửi `OffboardControlMode` (nhịp tim) và `TrajectorySetpoint` (điểm đến).
   Nếu nhịp tim dưới khoảng 2 Hz, PX4 thoát chế độ Offboard và chuyển sang failsafe.
2. Sau 10 setpoint đầu tiên (1 s), gửi `VehicleCommand` để chuyển sang Offboard (`DO_SET_MODE 1, 6`) và arm.
   PX4 chỉ nhận Offboard khi đã có luồng setpoint từ trước.
3. `target_system` lấy từ `vehicle_status.system_id`. Instance N có MAVLink system id N+1; gửi sai id thì PX4 bỏ qua lệnh.
4. Khi vị trí thật (`vehicle_local_position`) cách điểm đến dưới 0,8 m thì xem như đã tới, giữ `--hold` giây rồi sang điểm kế tiếp.
   Hết route thì gửi `NAV_LAND`.

Liên hệ với AnytimeSwarm: route của một UAV trong planner (Depot → Task 3 → Task 8 → ...) chính là danh sách waypoint
này. `--hold` là service time. Thời điểm in ra `reached` là thời điểm task thực sự bắt đầu, dùng để kiểm tra deadline
theo thời gian thực thi thật thay vì thời gian planner dự đoán.

## 5. Bài 4: hai UAV cùng bay

Tắt hết phiên cũ (Ctrl+C / `shutdown`). Terminal 1: `MicroXRCEAgent udp4 -p 8888`.

Terminal 2, UAV thứ nhất. Instance 1 khởi động Gazebo có GUI:
```bash
cd ~/PX4-Autopilot
PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_MODEL_POSE="0,0" ./build/px4_sitl_default/bin/px4 -i 1
```
Terminal 3, UAV thứ hai, nhập vào Gazebo đang chạy (`PX4_GZ_STANDALONE=1`), đặt cách 5 m về phía Đông:
```bash
cd ~/PX4-Autopilot
PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_MODEL_POSE="5,0" ./build/px4_sitl_default/bin/px4 -i 2
```
Trong mỗi `pxh>` (Terminal 2 và 3) gõ `param set NAV_DLL_ACT 0`.

Terminal 4 và 5, mỗi UAV một route trong cùng hệ tọa độ thế giới (Bắc, Đông, Cao):
```bash
python3 $J/demo/offboard_waypoints.py --ns /px4_1 --spawn 0,0 --hold 2 --wps "0,0,6;20,0,6;20,-15,6;0,0,6"
python3 $J/demo/offboard_waypoints.py --ns /px4_2 --spawn 5,0 --hold 2 --wps "0,5,8;20,20,8;0,20,8;0,5,8"
```
`--spawn` phải trùng `PX4_GZ_MODEL_POSE`. Script tự trừ vị trí xuất phát để đổi tọa độ thế giới sang NED cục bộ của từng
UAV. Hai UAV bay ở hai độ cao khác nhau (6 m và 8 m) vì demo này chưa có tránh va chạm.

Kết quả chạy thử: cả hai UAV qua đủ 4 waypoint, hạ cánh và disarm trong khoảng 40 s.

## 6. QGroundControl (tùy chọn): xem UAV trên bản đồ

```bash
~/apps/QGroundControl-x86_64.AppImage
```
File đã tải về và cài thư viện cần thiết; tôi chưa mở thử, nên đây là lần chạy đầu tiên.
QGC tự kết nối với PX4 qua UDP 14550. Nó hiện bản đồ, đường bay, chế độ bay, pin giả lập và thông báo lỗi.
Khi QGC đã kết nối, không cần đặt `NAV_DLL_ACT 0` nữa. Ở cấu hình nhiều UAV, QGC thấy từng xe theo system id
(Vehicle 2, Vehicle 3).

## 7. Xem lại chuyến bay

PX4 tự ghi log `.ulg` cho mỗi lần arm:
`~/PX4-Autopilot/build/px4_sitl_default/rootfs/<instance>/log/<ngày>/*.ulg`
(instance 0 khi dùng `make px4_sitl`). Công cụ gợi ý (chưa cài): PlotJuggler
(`sudo apt install ros-jazzy-plotjuggler-ros`, chạy `ros2 run plotjuggler plotjuggler`). Nó vẽ topic ROS 2 trực tiếp
khi đang bay và có plugin đọc ULog.

Ghi rosbag để phân tích sau:
```bash
ros2 bag record -o ~/bags/thu_1 /fmu/out/vehicle_local_position_v1 /fmu/out/vehicle_status_v1
```

## 8. Tắt và dọn

- Ctrl+C ở từng terminal, hoặc `shutdown` trong `pxh>`.
- Nếu còn tiến trình sót (lần sau báo `gazebo already running`):
  `pkill -f "gz sim"; pkill -f MicroXRCEAgent; pkill -f px4_sitl_default/bin/px4`
- Giải phóng RAM của Ubuntu: chạy trong PowerShell `wsl --terminate Ubuntu-24.04`. Không dùng `wsl --shutdown` nếu
  docker-desktop đang chạy, vì lệnh này tắt cả docker.

## 9. Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Arming denied: Resolve system health failures first` | chưa có GCS, `NAV_DLL_ACT=2` | `param set NAV_DLL_ACT 0` hoặc mở QGC |
| `Preflight Fail: ekf2 missing data` vài giây đầu | EKF2 chưa hội tụ | chờ `Ready for takeoff!` |
| `gazebo already running`, không có cửa sổ | Gazebo của lần trước còn chạy | các lệnh `pkill` ở mục 8 |
| Cửa sổ Gazebo đen hoặc crash | driver d3d12 | `unset GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME` rồi chạy lại (dùng CPU, chậm hơn) |
| `ros2 topic echo` không ra gì | agent chưa chạy, hoặc sai tên topic (thiếu `_v1`, thiếu `/px4_N`) | kiểm tra Terminal 1; `ros2 topic list` |
| node Python không nhận dữ liệu | subscriber để QoS reliable | dùng QoS best-effort như script demo |
| UAV không vào Offboard | chưa có setpoint trước khi chuyển mode, hoặc sai `target_system` | dùng đúng script demo; kiểm tra `--ns` |
| Gazebo chậm, RTF < 1 | máy quá tải | chạy headless: thêm `HEADLESS=1` trước lệnh PX4 |

Xem RTF: `gz topic -e -t /stats -n 1 | grep real_time_factor`. RTF = 1 nghĩa là 1 giây mô phỏng ứng với 1 giây thật.

## 10. Chạy tự động (sau khi đã hiểu cách chạy tay)

```bash
bash $J/setup/05_smoke_test.sh 2       # 2 UAV headless, liệt kê topic, đo RTF
bash $J/setup/test_demo_1uav.sh 120    # 1 UAV headless bay route mặc định, log vào setup/logs/
bash $J/setup/test_demo_2uav.sh 120    # 2 UAV headless bay 2 route
```
