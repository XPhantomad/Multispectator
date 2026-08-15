#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    laser_driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('yahboom_M3Pro_laser'),
                'launch', 'laser_driver.launch.py'
            )
        ])
    )

    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom_rf2o',
            'publish_tf': False,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 20.0,
        }],
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('orbbec_camera'),
                'launch', 'dabai_dcw2.launch.py'
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
        ],
        parameters=[{'size': 0.03}]
    )
    apriltag_node_delayed = TimerAction(period=5.0, actions=[apriltag_node])

    ekf_config = os.path.join(
        get_package_share_directory('m3pro_bringup'),
        'config', 'ekf.yaml'
    )
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config],
    )

    # IMU-Kovarianz-Fixer als reines Script starten (kein installiertes Executable noetig)
    imu_fixer_node = ExecuteProcess(
        cmd=['python3', '/root/M3Pro_ws/src/m3pro_bringup/scripts/imu_covariance_fixer.py'],
        output='screen',
    )

    smoother_config = os.path.join(
        get_package_share_directory('m3pro_bringup'),
        'config', 'velocity_smoother.yaml'
    )

    # Velocity Smoother: liest cmd_vel_raw (von deiner Fahrlogik),
    # publiziert cmd_vel (an den Antrieb).
    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[smoother_config],
        remappings=[
            ('cmd_vel', 'cmd_vel_raw'),        # Input von deiner Fahrlogik
            ('cmd_vel_smoothed', 'cmd_vel'),   # Output an den Antrieb
        ],
    )

    # Lifecycle-Manager: konfiguriert + aktiviert den Smoother automatisch.
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_smoother',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['velocity_smoother'],
        }],
    )

    return LaunchDescription([
        laser_driver_launch,
        rf2o_node,
        camera_launch,
        apriltag_node_delayed,
        ekf_node,
        imu_fixer_node,
        velocity_smoother,
        lifecycle_manager,
    ])

