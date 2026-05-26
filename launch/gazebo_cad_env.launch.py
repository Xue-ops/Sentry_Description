from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def make_robot_description(
    robot_xacro,
    robot_name,
    frame_prefix,
    cmd_topic,
    odom_topic,
    odom_frame,
    cloud_topic,
    base_r,
    base_g,
    base_b,
    base_a,
    gazebo_material
):
    return {
        'robot_description': Command([
            'xacro ',
            robot_xacro,
            ' robot_name:=', robot_name,
            ' frame_prefix:=', frame_prefix,
            ' cmd_topic:=', cmd_topic,
            ' odom_topic:=', odom_topic,
            ' odom_frame:=', odom_frame,
            ' cloud_topic:=', cloud_topic,
            ' base_r:=', base_r,
            ' base_g:=', base_g,
            ' base_b:=', base_b,
            ' base_a:=', base_a,
            ' gazebo_material:=', gazebo_material,
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
        'simple_robot.urdf.xacro'
    ])

    odin1_description = make_robot_description(
        robot_xacro,
        'odin1',
        '',
        '/cmd_vel',
        '/odom',
        'odom',
        '/odin1/cloud_slam',
        '1.0',
        '0.0',
        '0.0',
        '1.0',
        'Gazebo/Red'
    )

    odin2_description = make_robot_description(
        robot_xacro,
        'odin2',
        'odin2_',
        '/odin2/cmd_vel',
        '/odin2/odom',
        'odin2_odom',
        '/odin2/cloud_slam',
        '0.0',
        '0.1',
        '1.0',
        '1.0',
        'Gazebo/Blue'
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
