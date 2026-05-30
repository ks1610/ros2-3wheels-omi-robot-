import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_name = 'diff'
    pkg_share = get_package_share_directory(pkg_name)
    
    # Declare arguments
    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value='map1',
        description='Name of the world (e.g. map1, maze2) to load the corresponding map'
    )
    
    declare_slam_cmd = DeclareLaunchArgument(
        'slam',
        default_value='False',
        description='Whether to run SLAM (True) or static map navigation (False)'
    )
    
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation clock if True'
    )
    
    # Map file path using standard ROS 2 list-based concatenation
    world_conf = LaunchConfiguration('world')
    map_file_path = [pkg_share, '/maps/', world_conf, '.yaml']
    
    # Find nav2_bringup launch file
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'slam': LaunchConfiguration('slam'),
            'map': map_file_path,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': os.path.join(pkg_nav2_bringup, 'params', 'nav2_params.yaml')
        }.items()
    )
    
    return LaunchDescription([
        declare_world_cmd,
        declare_slam_cmd,
        declare_use_sim_time_cmd,
        nav2_bringup_launch
    ])
