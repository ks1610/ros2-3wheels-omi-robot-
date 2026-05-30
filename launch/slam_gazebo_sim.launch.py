import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

PACKAGE_NAME = "diff"

def generate_launch_description():
    # Lấy đường dẫn đến thư mục share của package
    pkg_share = get_package_share_directory(PACKAGE_NAME)

    default_world_path = os.path.join(pkg_share, 'worlds', 'maze2.sdf')

    declare_world_cmd = DeclareLaunchArgument(
        'worlds', 
        default_value=default_world_path,
        description='Đường dẫn tuyệt đối đến file Gazebo World'
    )

    # Include file launch gazebo_sim và truyền biến worlds đã chứa đường dẫn đầy đủ
    gazebo_sim_path = PathJoinSubstitution([
                pkg_share, 'launch', 'gazebo_sim.launch.py'
            ])
    
    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gazebo_sim_path]),
        launch_arguments={'worlds': LaunchConfiguration('worlds')}.items()
    )

    slam_toolbox_launch_path = PathJoinSubstitution([
                get_package_share_directory("slam_toolbox"), 'launch', 'online_async_launch.py'
            ])
    
    slam_params_file = os.path.join(pkg_share, 'config', 'mapper_params_online_async.yaml')

    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([slam_toolbox_launch_path]),
        launch_arguments={
            "use_sim_time": "true",
            "slam_params_file": slam_params_file
        }.items()
    )

    rviz_config_path = PathJoinSubstitution([
                pkg_share, 'rviz', 'slam.rviz'
            ])
            
    rviz2 = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_path],
            parameters=[{'use_sim_time': True}]
        )
    
    # Tạo LaunchDescription và thêm các action
    ld = LaunchDescription()
    ld.add_action(declare_world_cmd)
    ld.add_action(gazebo_sim)
    ld.add_action(slam_toolbox_launch)
    ld.add_action(rviz2)
    
    return ld