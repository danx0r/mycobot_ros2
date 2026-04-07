"""
Launch mycobot_280_pi in Ignition Gazebo (Fortress) with ros2_control.

Starts:
  - Ignition Gazebo with empty world
  - robot_state_publisher (URDF via xacro)
  - spawn_entity (ros_gz_sim)
  - joint_state_broadcaster
  - arm_group_controller (JointTrajectoryController)
  - ros_gz_bridge for /clock
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import xacro


def generate_launch_description():
    pkg_gz = get_package_share_directory('mycobot_280pi_gz')

    # --- Arguments ---
    gz_paused_arg = DeclareLaunchArgument(
        'gz_paused', default_value='false',
        description='Start Gazebo paused')
    gz_gui_arg = DeclareLaunchArgument(
        'gz_gui', default_value='true',
        description='Start Gazebo GUI')

    # --- Robot description (xacro -> URDF string) ---
    xacro_file = os.path.join(pkg_gz, 'config', 'mycobot_280_pi.urdf.xacro')
    robot_description_content = xacro.process_file(xacro_file).toxml()
    robot_description = {'robot_description': robot_description_content}

    # --- robot_state_publisher ---
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    # --- Ignition Gazebo ---
    world_file = os.path.join(pkg_gz, 'worlds', 'empty.sdf')
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': [world_file, ' -r --physics-engine ignition-physics-dartsim-plugin'],
        }.items(),
    )

    # --- Spawn robot from robot_description topic ---
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'mycobot_280_pi',
            '-topic', 'robot_description',
            '-z', '0.03',
        ],
        output='screen',
    )

    # --- Clock bridge (Ignition -> ROS2) ---
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
        output='screen',
    )

    # --- Spawn controllers after robot is created ---
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_group_controller', '--controller-manager', '/controller_manager'],
    )

    # Start arm controller after joint_state_broadcaster is active
    start_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )

    # Delay controller spawning to give Gazebo time to load the plugin
    delayed_jsb = TimerAction(period=5.0, actions=[joint_state_broadcaster_spawner])

    return LaunchDescription([
        gz_paused_arg,
        gz_gui_arg,
        rsp_node,
        gz_sim,
        spawn_robot,
        clock_bridge,
        delayed_jsb,
        start_arm_controller,
    ])
