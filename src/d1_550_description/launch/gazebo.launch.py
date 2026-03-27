import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    pkg_path = get_package_share_directory('d1_550_description')
    urdf_path = os.path.join(pkg_path, 'urdf', 'd1_550_description.urdf')
    controllers_yaml = os.path.join(pkg_path, 'config', 'controllers.yaml')
    meshes_path = os.path.join(pkg_path, 'meshes')

    with open(urdf_path, 'r') as f:
        robot_description = f.read()

    robot_description = robot_description.replace(
        'package://d1_550_description/meshes/',
        'file://' + meshes_path + '/'
    )
    robot_description = robot_description.replace(
        'CONTROLLERS_YAML_PLACEHOLDER',
        controllers_yaml
    )

    return LaunchDescription([

        # Gazebo server
        ExecuteProcess(
            cmd=['gzserver', '--verbose', '-s', 'libgazebo_ros_factory.so'],
            output='screen'
        ),

        # Gazebo client
        TimerAction(period=3.0, actions=[
            ExecuteProcess(cmd=['gzclient'], output='screen')
        ]),

        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),

        # Spawn robot
        TimerAction(period=6.0, actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=[
                    '-entity', 'd1_arm',
                    '-topic', '/robot_description',
                    '-x', '0.0', '-y', '0.0', '-z', '0.05'
                ],
                output='screen'
            )
        ]),

        # ros2_control manager — runs standalone, connects to Gazebo via plugin
        TimerAction(period=8.0, actions=[
            Node(
                package='controller_manager',
                executable='ros2_control_node',
                parameters=[
                    {'robot_description': robot_description},
                    controllers_yaml
                ],
                output='screen'
            )
        ]),

        # Load controllers after manager is up
        TimerAction(period=12.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller',
                     '--set-state', 'start', 'joint_state_broadcaster'],
                output='screen'
            ),
        ]),
        TimerAction(period=13.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller',
                     '--set-state', 'start', 'arm_controller'],
                output='screen'
            ),
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller',
                     '--set-state', 'start', 'gripper_controller'],
                output='screen'
            ),
        ]),

        # GUI on isolated topic
        TimerAction(period=14.0, actions=[
            Node(
                package='joint_state_publisher_gui',
                executable='joint_state_publisher_gui',
                output='screen',
                remappings=[('joint_states', '/gui_joint_states')],
            )
        ]),
    ])
