#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class LidarVeri(Node):
    def __init__(self):
        super().__init__('lidar_verileri')
        # Đăng ký nhận dữ liệu từ topic /scan
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        self.get_logger().info(f'Nhận được dữ liệu LiDAR: {len(msg.ranges)} điểm')
        # Bỏ print toàn bộ msg vì terminal sẽ bị spam liên tục

def main(args=None):
    rclpy.init(args=args)
    node = LidarVeri()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Sonlandirildi (Đã dừng node).')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()