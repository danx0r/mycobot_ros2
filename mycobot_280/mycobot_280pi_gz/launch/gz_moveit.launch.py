"""
Launch mycobot_280_pi in Ignition Gazebo with MoveIt2.

Includes everything from gz.launch.py and adds:
  - move_group (MoveIt)
  - RViz with MoveIt plugin
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder
import xacro


def generate_launch_description():
    pkg_gz = get_package_share_directory('mycobot_280pi_gz')

    # --- Robot description (same xacro as gz.launch.py) ---
    xacro_file = os.path.join(pkg_gz, 'config', 'mycobot_280_pi.urdf.xacro')
    robot_description_content = xacro.process_file(xacro_file).toxml()

    # --- MoveIt config (reuse mycobot_280_moveit2's SRDF/kinematics/etc.) ---
    # We override robot_description so MoveIt uses our Gazebo-capable URDF.
    moveit_config = (
        MoveItConfigsBuilder('firefighter', package_name='mycobot_280_moveit2')
        .robot_description(file_path=xacro_file)
        .to_moveit_configs()
    )

    # --- Gazebo + controllers ---
    gz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('mycobot_280pi_gz'),
                'launch', 'gz.launch.py'
            ])
        ),
    )

    # --- move_group ---
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[moveit_config.to_dict()],
    )

    # --- RViz with MoveIt config ---
    rviz_config_file = os.path.join(
        get_package_share_directory('mycobot_280_moveit2'),
        'config', 'moveit.rviz'
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='log',
        arguments=['-d', rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
        ],
    )

    # Delay MoveIt startup to let Gazebo and controllers come up first
    delayed_moveit = TimerAction(
        period=8.0,
        actions=[move_group_node, rviz_node],
    )

    return LaunchDescription([
        gz_launch,
        delayed_moveit,
    ])
