#!/usr/bin/env python3
"""Set initial joint positions in Gazebo after spawn."""
import sys
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SetModelConfiguration


class SetJoints(Node):
    def __init__(self):
        super().__init__('set_initial_joints')
        self.client = self.create_client(
            SetModelConfiguration, '/gazebo/set_model_configuration'
        )
        self.get_logger().info('Waiting for /gazebo/set_model_configuration...')
        if not self.client.wait_for_service(timeout_sec=30.0):
            self.get_logger().error('Service not available')
            sys.exit(1)

        req = SetModelConfiguration.Request()
        req.model_name = 'mycobot_280'
        req.urdf_param_name = 'robot_description'
        req.joint_names = [
            'joint2_to_joint1',
            'joint3_to_joint2',
            'joint4_to_joint3',
            'joint5_to_joint4',
            'joint6_to_joint5',
            'joint6output_to_joint6',
        ]
        req.joint_positions = [0.0, -1.5708, 0.0, 0.0, 0.0, 0.0]

        future = self.client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        result = future.result()
        if result.success:
            self.get_logger().info('Joint positions set successfully')
        else:
            self.get_logger().error(f'Failed: {result.status_message}')


def main():
    rclpy.init()
    node = SetJoints()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
