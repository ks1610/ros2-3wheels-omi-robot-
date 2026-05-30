import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, RegisterEventHandler, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
import xacro

def launch_setup(context, *args, **kwargs):
    pkg_name = 'diff'
    pkg_share = get_package_share_directory(pkg_name)
    
    # Retrieve launch argument values
    world_name = context.launch_configurations.get('world', 'map1')
    worlds_path = context.launch_configurations.get('worlds', '')
    
    # Resolve the world file path
    if worlds_path:
        world_file = worlds_path
    else:
        # Check if the name already contains extension
        if not world_name.endswith('.sdf') and not world_name.endswith('.world'):
            world_file = os.path.join(pkg_share, 'worlds', f'{world_name}.sdf')
        else:
            world_file = os.path.join(pkg_share, 'worlds', world_name)
            
    # Fallback to make sure the file exists; if not, look for .sdf instead of .world
    if not os.path.exists(world_file):
        alternative = world_file.replace('.world', '.sdf')
        if os.path.exists(alternative):
            world_file = alternative
            
    # 1. Force Resource Path for Gazebo to find STL meshes
    install_dir = get_package_prefix(pkg_name)
    gazebo_model_path = os.path.join(install_dir, 'share')
    set_gazebo_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', gazebo_model_path)

    # 2. Process URDF/Xacro
    xacro_file = os.path.join(pkg_share, 'urdf', 'main.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {'robot_description': robot_description_config.toxml(),
                         'use_sim_time': True}

    # 3. Launch Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # 4. Launch Gazebo Sim with resolved world file
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    # 5. Spawn Robot into Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                   '-name', 'diff_bot',
                   '-allow_renaming', 'true',
                   '-z', '0.1'],
        output='screen'
    )

    # 6. Bridge: Connect Clock and LiDAR from Gazebo to ROS 2
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    # 7. Joint State Broadcaster Spawner
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    # 8. Omni Drive Controller Spawner
    load_omni_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["omni_wheel_drive_controller"],
    )

    # 9. Register event handlers to load controllers in sequence
    controllers_spawners = [
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_broadcaster],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_broadcaster,
                on_exit=[load_omni_controller],
            )
        ),
    ]

    return [
        set_gazebo_resource_path,
        node_robot_state_publisher,
        gazebo,
        spawn_entity,
        bridge,
        *controllers_spawners
    ]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='map1',
            description='Name of the Gazebo world (e.g. map1, maze2)'
        ),
        DeclareLaunchArgument(
            'worlds',
            default_value='',
            description='Full path to the world SDF/world file'
        ),
        OpaqueFunction(function=launch_setup)
    ])