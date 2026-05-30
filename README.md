# 3WD_OMNI_ROBOT

Original: https://github.com/Seda-cpu/3WD_OMNI_ROBOT

![project demo](mesh/image.png)

## Thư mục project 
```
cd ~/3WD_OMNI_ROBOT/diff/
```

## Build Package
```
colcon build --packages-select diff --symlink-install
```

## Về Project 
![project demo](worlds/map.png)
### khởi động Gazebo & Rviz:
```
source install/setup.bash
ros2 launch diff sim.launch.py
```

### Điều khiển với phím bấm
#### Chạy bộ chuyển đổi topic của controller sang topic của Robot:
```
source install/setup.bash
ros2 run diff converter.py
```
#### Chạy bảng điều khiển phím bấm:
```
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Chạy tự động

#### Khởi chạy node `auto.py` để robot tự động di chuyển khám phá và né vật cản:
```bash
source install/setup.bash
ros2 run diff auto.py
```

---

## 🗺️ Bản đồ & Định vị (SLAM & Nav2)

### 1. Tạo bản đồ với SLAM (Mapping)
Khởi động Gazebo, Robot State Publisher, SLAM Toolbox, và RViz:
* **Với bản đồ `maze2` (Mặc định)**:
  ```bash
  source install/setup.bash
  ros2 launch diff slam_gazebo_sim.launch.py
  ```
* **Với bản đồ `map1`**:
  ```bash
  source install/setup.bash
  ros2 launch diff slam_gazebo_sim.launch.py worlds:=$(ros2 pkg prefix diff)/share/diff/worlds/map1.sdf
  ```

#### Di chuyển robot để quét bản đồ:
1. Mở terminal mới, chạy bộ chuyển đổi topic:
   ```bash
   source install/setup.bash
   ros2 run diff converter.py
   ```
2. Chạy bảng điều khiển phím:
   ```bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```
   *Di chuyển robot đi khắp bản đồ cho đến khi RViz hiển thị đầy đủ các chướng ngại vật.*

#### Lưu bản đồ đã quét:
Sau khi quét xong, chạy lệnh sau ở terminal để lưu bản đồ trực tiếp vào thư mục nguồn của project:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/3WD_OMNI_ROBOT/diff/maps/maze2 --fmt pgm
```
*(Nếu quét bản đồ `map1`, đổi tên file lưu thành `map1`)*

**Hoặc dùng lệnh gọi service trực tiếp của SLAM Toolbox**:
```bash
ros2 service call /slam_toolbox/save_map slam_toolbox_msgs/srv/SaveMap "{map_name: '/home/khanhtrinh/trinh/3WD_OMNI_ROBOT/diff/maps/maze2'}"
```

**Lưu ý**: Nhớ chạy lại lệnh build sau khi lưu bản đồ mới để file được cập nhật vào thư mục share:
```bash
colcon build --packages-select diff --symlink-install
```

### 2. Định vị và dẫn đường với Nav2 (Navigation)
Khởi chạy hệ thống dẫn đường Nav2, định vị AMCL và tải bản đồ:
* **Chạy với bản đồ `maze2`**:
  ```bash
  source install/setup.bash
  ros2 launch diff navigation_gazebo_sim.launch.py world:=maze2
  ```
* **Chạy với bản đồ `map1`**:
  ```bash
  source install/setup.bash
  ros2 launch diff navigation_gazebo_sim.launch.py world:=map1
  ```

#### Hướng dẫn điều khiển trên RViz:
1. Nhấp nút **2D Pose Estimate** trên thanh công cụ của RViz, sau đó kéo chọn vị trí và hướng hiện tại của robot trên bản đồ để khởi tạo vị trí cho AMCL.
2. Nhấp nút **2D Goal Pose** (hoặc **Nav2 Goal**), kéo chọn điểm đích trên bản đồ. Robot sẽ tự động tính toán lộ trình và di chuyển đến đích.