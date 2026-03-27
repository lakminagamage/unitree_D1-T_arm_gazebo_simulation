#!/usr/bin/env python3
"""
Slider bridge with deadband filtering and rate limiting.
Only sends trajectory commands when joints actually move,
preventing vibration from constant re-commanding.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time

ARM_JOINTS     = ['Joint1', 'Joint2', 'Joint3', 'Joint4', 'Joint5', 'Joint6']
GRIPPER_JOINTS = ['Joint_L', 'Joint_R']

# Only send a new command if a joint moved more than this (radians / meters)
DEADBAND = 0.005

# Minimum seconds between commands (rate limiter)
MIN_SEND_INTERVAL = 0.05  # 20Hz max

# How long the controller has to reach the target (longer = smoother)
EXECUTION_TIME_SEC = 0.5


class SliderBridge(Node):
    def __init__(self):
        super().__init__('slider_bridge')

        self.arm_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(
            JointTrajectory, '/gripper_controller/joint_trajectory', 10)

        self.sub = self.create_subscription(
            JointState, '/gui_joint_states', self.callback, 10)

        self.last_arm_positions     = None
        self.last_gripper_positions = None
        self.last_arm_send_time     = 0.0
        self.last_gripper_send_time = 0.0

        self.get_logger().info(
            f'Slider bridge ready | deadband={DEADBAND} rad | '
            f'max rate={1.0/MIN_SEND_INTERVAL:.0f}Hz | '
            f'execution time={EXECUTION_TIME_SEC}s'
        )

    def positions_changed(self, new_pos, last_pos):
        if last_pos is None:
            return True
        return any(abs(n - l) > DEADBAND for n, l in zip(new_pos, last_pos))

    def make_trajectory(self, joint_names, positions):
        traj = JointTrajectory()
        traj.joint_names = joint_names
        pt = JointTrajectoryPoint()
        pt.positions = list(positions)
        pt.velocities = [0.0] * len(joint_names)
        pt.time_from_start = Duration(
            sec=int(EXECUTION_TIME_SEC),
            nanosec=int((EXECUTION_TIME_SEC % 1) * 1e9)
        )
        traj.points = [pt]
        return traj

    def callback(self, msg: JointState):
        now = time.time()
        pos = dict(zip(msg.name, msg.position))

        arm_pos = [pos.get(j, 0.0) for j in ARM_JOINTS]
        if (now - self.last_arm_send_time >= MIN_SEND_INTERVAL and
                self.positions_changed(arm_pos, self.last_arm_positions)):
            self.arm_pub.publish(self.make_trajectory(ARM_JOINTS, arm_pos))
            self.last_arm_positions = arm_pos
            self.last_arm_send_time = now

        gripper_pos = [pos.get(j, 0.0) for j in GRIPPER_JOINTS]
        if (now - self.last_gripper_send_time >= MIN_SEND_INTERVAL and
                self.positions_changed(gripper_pos, self.last_gripper_positions)):
            self.gripper_pub.publish(self.make_trajectory(GRIPPER_JOINTS, gripper_pos))
            self.last_gripper_positions = gripper_pos
            self.last_gripper_send_time = now


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