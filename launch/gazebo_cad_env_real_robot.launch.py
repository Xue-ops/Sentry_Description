from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def make_robot_description(
    robot_xacro,
    base_frame,
    robot_base_frame,
    cmd_topic,
    odom_topic,
    odom_frame,
    odin1_frame,
    livox_frame,
    odin1_cloud_topic,
    odin1_cloud_frame,
    livox_cloud_topic,
    wheel_prefix,
):
    return {
        'robot_description': Command([
            'xacro ',
            robot_xacro,
            ' base_frame:=', base_frame,
            ' robot_base_frame:=', robot_base_frame,
            ' cmd_topic:=', cmd_topic,
            ' odom_topic:=', odom_topic,
            ' odom_frame:=', odom_frame,
            ' odin1_frame:=', odin1_frame,
            ' livox_frame:=', livox_frame,
            ' odin1_cloud_topic:=', odin1_cloud_topic,
            ' odin1_cloud_frame:=', odin1_cloud_frame,
            ' livox_cloud_topic:=', livox_cloud_topic,
            ' wheel_prefix:=', wheel_prefix,
        ])
    }


def generate_launch_description():
    pkg_share = FindPackageShare('sentry_description')

    world_file = PathJoinSubstitution([
        pkg_share,
        'worlds',
        'cad_env.world'
    ])

    robot_xacro = PathJoinSubstitution([
        pkg_share,
        'urdf',
        'real_robot.urdf.xacro'
    ])

    odin1_description = make_robot_description(
        robot_xacro,
        'odom',
        'robot_base',
        '/cmd_vel',
        '/odin1/odom',
        'odom',
        'odin1_base_link',
        'livox_frame',
        '/odin1/cloud_slam',
        'odin1_base_link',
        'livox/lidar',
        '',
    )

    odin2_description = make_robot_description(
        robot_xacro,
        'odin2_odom',
        'odin2_robot_base',
        '/odin2/cmd_vel',
        '/odin2/odom',
        'odin2_odom',
        'odin2_odin1_base_link',
        'odin2_livox_frame',
        '/odin2/cloud_slam',
        'odin2_odin1_base_link',
        '/odin2/livox/lidar',
        'odin2_',
    )

    model_path = PathJoinSubstitution([
        pkg_share,
        'models'
    ])

    gazebo_launch = PathJoinSubstitution([
        FindPackageShare('gazebo_ros'),
        'launch',
        'gazebo.launch.py'
    ])

    return LaunchDescription([

        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=model_path
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={
                'world': world_file,
                'verbose': 'true'
            }.items()
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace='odin1',
            parameters=[odin1_description],
            output='screen'
        ),

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-topic', '/odin1/robot_description',
                '-entity', 'odin1',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.1'
            ],
            output='screen'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace='odin2',
            parameters=[odin2_description],
            output='screen'
        ),

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-topic', '/odin2/robot_description',
                '-entity', 'odin2',
                '-x', '0.0',
                '-y', '0.8',
                '-z', '0.1'
            ],
            output='screen'
        ),

        Node(
            package='sentry_description',
            executable='oscillate_cmd_vel.py',
            name='odin2_oscillate_cmd_vel',
            parameters=[{
                'cmd_vel_topic': '/odin2/cmd_vel',
                'speed': 1.0,
                'period': 4.0,
            }],
            output='screen'
        ),
    ])
