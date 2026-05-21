#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistConverter(Node):
    def __init__(self):
        super().__init__('twist_converter')
        self.subscription = self.create_subscription(Twist, '/cmd_vel', self.listener_callback, 10)
        self.publisher = self.create_publisher(TwistStamped, '/omni_wheel_drive_controller/cmd_vel', 10)

    def listener_callback(self, msg):
        stamped_msg = TwistStamped()
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = 'base_footprint'
        stamped_msg.twist = msg
        self.publisher.publish(stamped_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TwistConverter()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()