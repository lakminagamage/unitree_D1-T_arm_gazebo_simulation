#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

ARM_JOINTS = ['Joint1', 'Joint2', 'Joint3', 'Joint4', 'Joint5', 'Joint6']
GRIPPER_JOINTS = ['Joint_L', 'Joint_R']

class SliderBridge(Node):
    def __init__(self):
        super().__init__('slider_bridge')
        self.arm_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(
            JointTrajectory, '/gripper_controller/joint_trajectory', 10)

        # Listen to /gui_joint_states — isolated from ros2_control's /joint_states
        self.sub = self.create_subscription(
            JointState, '/gui_joint_states', self.callback, 10)
        self.get_logger().info('Slider bridge ready on /gui_joint_states')

    def callback(self, msg: JointState):
        pos = dict(zip(msg.name, msg.position))

        if any(j in pos for j in ARM_JOINTS):
            traj = JointTrajectory()
            traj.joint_names = ARM_JOINTS
            pt = JointTrajectoryPoint()
            pt.positions = [pos.get(j, 0.0) for j in ARM_JOINTS]
            pt.time_from_start = Duration(sec=0, nanosec=200_000_000)  # 200ms
            traj.points = [pt]
            self.arm_pub.publish(traj)

        if any(j in pos for j in GRIPPER_JOINTS):
            traj = JointTrajectory()
            traj.joint_names = GRIPPER_JOINTS
            pt = JointTrajectoryPoint()
            pt.positions = [pos.get(j, 0.0) for j in GRIPPER_JOINTS]
            pt.time_from_start = Duration(sec=0, nanosec=200_000_000)
            traj.points = [pt]
            self.gripper_pub.publish(traj)

def main():
    rclpy.init()
    node = SliderBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
