from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


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

    robot_description = {
        'robot_description': Command(['xacro ', robot_xacro])
    }

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
            parameters=[robot_description],
            output='screen'
        ),

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-topic', 'robot_description',
                '-entity', 'simple_robot',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.1'
            ],
            output='screen'
        ),
    ])