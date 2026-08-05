#!/usr/bin/env python3
"""
Combined bringup launch file for the M3 Pro AprilTag/camera pipeline.

Starts, in order:
  1. yahboom_M3Pro_laser laser_driver.launch.py
     (robot_state_publisher, joint_state_publisher, laser merger/filter)
  2. rf2o_laser_odometry rf2o_laser_odometry.launch.py
     (publishes /odom_rf2o)
  3. orbbec_camera dabai_dcw2.launch.py
     (publishes /camera/color/image_raw, /camera/color/camera_info, etc.)
  4. apriltag_localization apriltag_node
     (publishes /detections, remapped onto the camera topics above)

Usage:
  ros2 launch <this_file>.launch.py
"""
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    laser_driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('yahboom_M3Pro_laser'),
                'launch',
                'laser_driver.launch.py'
            )
        ])
    )

    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py'
            )
        ])
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('orbbec_camera'),
                'launch',
                'dabai_dcw2.launch.py'
            )
        ])
    )

    apriltag_node = Node(
        package='apriltag_localization',
        executable='apriltag_node',
        name='apriltag_node',
        output='screen',
        remappings=[
            ('image_rect', '/camera/color/image_raw'),
            ('camera_info', '/camera/color/camera_info'),
        ]
    )

    # The AprilTag node needs the camera topics to already exist, so it is
    # started a few seconds after everything else to give the camera driver
    # time to come up. Adjust the delay if it still starts too early/late.
    apriltag_node_delayed = TimerAction(
        period=5.0,
        actions=[apriltag_node]
    )

    return LaunchDescription([
        laser_driver_launch,
        rf2o_launch,
        camera_launch,
        apriltag_node_delayed,
    ])