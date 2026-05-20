import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, ExecuteProcess, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
import xacro

def generate_launch_description():
    pkg_name = 'diff'
    pkg_share = get_package_share_directory(pkg_name)
    
    # 1. Ép đường dẫn Resource cho Gazebo tìm file STL
    install_dir = get_package_prefix(pkg_name)
    gazebo_model_path = os.path.join(install_dir, 'share')
    set_gazebo_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', gazebo_model_path)

    # 2. Xử lý file URDF/Xacro
    xacro_file = os.path.join(pkg_share, 'urdf', 'main.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {'robot_description': robot_description_config.toxml(),
                         'use_sim_time': True} # Kích hoạt Clock giả lập

    # 3. Khởi chạy Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # Tạo môi trường Gazebo với bản đồ đã thiết kế
    world_file = os.path.join(pkg_share, 'worlds', 'map1.sdf')
    # 4. Khởi chạy Gazebo Harmonic
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        # Thay đổi gz_args để load world_file
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    # 5. Spawn Robot vào Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                   '-name', 'diff_bot',
                   '-z', '0.1'], 
        output='screen'
    )

    # 6. Bridge: Nối Clock và LiDAR từ Gazebo sang ROS 2
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    # 7. Khởi chạy RViz2
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # 8. Kích hoạt Joint State Broadcaster (Để vẽ các link trên RViz)
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    # 9. Kích hoạt Omni Drive Controller (Để sinh ra odom và điều khiển cmd_vel)
    load_omni_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["omni_wheel_drive_controller"],
    )

    return LaunchDescription([
        set_gazebo_resource_path,
        node_robot_state_publisher,
        gazebo,
        spawn_entity,
        bridge,
        rviz2,
        load_joint_state_broadcaster,
        load_omni_controller
    ])