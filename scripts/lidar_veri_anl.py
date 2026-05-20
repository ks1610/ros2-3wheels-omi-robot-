#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math

class LidarVeriAnl(Node):
    def __init__(self):
        super().__init__('lidar_veri_anl')
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.callback, 10)

    def safe_min(self, slice_arr, max_val):
        # Lọc bỏ giá trị inf (vô cực) và nan trước khi tìm min
        valid_vals = [x for x in slice_arr if not math.isinf(x) and not math.isnan(x)]
        if not valid_vals:
            return float(max_val)
        return min(min(valid_vals), float(max_val))

    def callback(self, msg):
        ranges = msg.ranges
        # Đảm bảo mảng đủ 720 tia (thường gặp với rplidar)
        if len(ranges) < 720:
            return

        bolgeler = {
            'sag': self.safe_min(ranges[0:143], 30.0),
            'on_sag': self.safe_min(ranges[144:287], 30.0),
            'on': self.safe_min(ranges[288:431], 30.0),
            'on_sol': self.safe_min(ranges[432:575], 30.0),
            'sol': self.safe_min(ranges[576:719], 30.0),
        }
        self.get_logger().info(f'Khoảng cách các vùng: {bolgeler}')

def main(args=None):
    rclpy.init(args=args)
    node = LidarVeriAnl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Sonlandirildi (Đã dừng node).')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()