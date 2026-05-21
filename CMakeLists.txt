cmake_minimum_required(VERSION 3.8)
project(diff)

# Khai báo sử dụng chuẩn C++17 (yêu cầu cơ bản của ROS2)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Tìm kiếm các build tools và thư viện của ROS2
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

# 2. Cài đặt các thư mục chứa resource (Launch, URDF, Mesh, Config)
# Trong ROS2, bắt buộc phải install các file này vào thư mục share
install(DIRECTORY
  launch
  urdf
  mesh
  config
  worlds
  DESTINATION share/${PROJECT_NAME}
)

# 3. Cài đặt các file Python Scripts
# Giúp ROS2 có thể chạy node bằng lệnh: ros2 run diff <tên_file.py>
install(PROGRAMS
  scripts/lidar_veri_anl.py
  scripts/lidar_veri.py
  scripts/otonom1.py
  DESTINATION lib/${PROJECT_NAME}
)

# 4. (Tùy chọn) Nếu sau này bạn có viết thêm các file C++ trong thư mục src/
# add_executable(my_cpp_node src/my_cpp_node.cpp)
# ament_target_dependencies(my_cpp_node rclcpp std_msgs)
# install(TARGETS my_cpp_node
#   DESTINATION lib/${PROJECT_NAME}
# )

# Đánh dấu đây là một ament package
ament_package()

install(PROGRAMS
  scripts/converter.py
  DESTINATION lib/${PROJECT_NAME}
)