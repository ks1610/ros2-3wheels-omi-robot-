#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped
from rclpy.qos import qos_profile_sensor_data
import math

FORCE_TURN_SIGN = 1
# Điều chỉnh lại các thông số theo yêu cầu
LIDAR_BLIND   = 0.01   # Vùng mù giảm xuống 1cm để nhận diện được vật ở mốc 5cm
SAFE_DIST     = 0.05   # Khoảng cách an toàn là 5cm (0.05m)
CLEAR_DIST    = 0.20   # Khoảng cách phía trước > 20cm là đủ an toàn để thoát xoay
BACKUP_CYCLES = 30     
MIN_TURN_CYCLES = 20   # Giảm nhẹ số chu kỳ quay tối thiểu
FORWARD_SPEED = 0.30   
BACKUP_SPEED  = -0.12
TURN_SPEED    = 1.5    

class OtonomBir(Node):
    def __init__(self):
        super().__init__('otonom_bir')
        self.sub_lidar = self.create_subscription(LaserScan, '/scan', self.lidar_callback, qos_profile_sensor_data)
        self.pub = self.create_publisher(TwistStamped, '/omni_wheel_drive_controller/cmd_vel', 10)

        self.state       = 'EVALUATING'
        self.turn_sign   = FORCE_TURN_SIGN
        self.turn_dir    = 'RIGHT'
        self.turn_cycles = 0
        self.backup_cycles = 0

    def _min(self, rays, maxv=10.0):
        """Đã sửa: Xử lý đúng giá trị vô cực (inf) khi đường rất thoáng"""
        valid = []
        for x in rays:
            if math.isinf(x):
                valid.append(maxv) # Nếu không có vật cản, gán bằng maxv (10m)
            elif not math.isnan(x) and x > LIDAR_BLIND:
                valid.append(x)
        return min(valid) if valid else 0.0

    def lidar_callback(self, msg):
        r = list(msg.ranges)
        n = len(r)
        if n < 720:
            return
        
        s = n // 4 

        b_raw = {
            'R':  self._min(r[0 : s]),
            'FR': self._min(r[s : s + s//2]),
            'F':  self._min(r[s + s//2 : 2*s + s//2]), 
            'FL': self._min(r[2*s + s//2 : 3*s]), 
            'L':  self._min(r[3*s : n]),
        }

        self.get_logger().info(f"[{self.state}] F={b_raw['F']:.2f} FL={b_raw['FL']:.2f} FR={b_raw['FR']:.2f} L={b_raw['L']:.2f} R={b_raw['R']:.2f}")
        self.navigate(b_raw)

    def cmd(self, vx=0.0, wz=0.0):
        m = TwistStamped()
        m.header.stamp    = self.get_clock().now().to_msg()
        m.header.frame_id = 'base_footprint'
        m.twist.linear.x  = vx
        m.twist.angular.z = wz
        self.pub.publish(m)

    def stop_robot(self):
        """Hàm dừng robot an toàn khi thoát chương trình"""
        self.cmd(vx=0.0, wz=0.0)

    def _wz(self, direction):
        if direction == 'LEFT':
            return -self.turn_sign * TURN_SPEED
        else:
            return self.turn_sign * TURN_SPEED

    def navigate(self, b):
        # Tính toán gộp khoảng trống 3 hướng chính
        dist_front = b['F']
        dist_left  = min(b['L'], b['FL'])
        dist_right = min(b['R'], b['FR'])

        # 1. TRẠNG THÁI KIỂM TRA
        if self.state == 'EVALUATING':
            # Nếu tất cả các hướng đều > 5cm thì đi thẳng
            if dist_front > SAFE_DIST and dist_left > SAFE_DIST and dist_right > SAFE_DIST:
                self.cmd(vx=FORWARD_SPEED)
            else:
                # Nếu có mặt <= 5cm, so sánh ngay 2 bên trái/phải xem bên nào rộng hơn
                if dist_left > dist_right:
                    self.turn_dir = 'LEFT'
                else:
                    self.turn_dir = 'RIGHT'

                self.get_logger().info(f"Vật cản! (Front={dist_front:.2f}, Left={dist_left:.2f}, Right={dist_right:.2f}). Ưu tiên né về {self.turn_dir}")
                self.state = 'BACKING_UP'
                self.backup_cycles = 0
                self.cmd(vx=BACKUP_SPEED)

        # 2. TRẠNG THÁI LÙI LẠI
        elif self.state == 'BACKING_UP':
            self.backup_cycles += 1
            if self.backup_cycles >= BACKUP_CYCLES:
                self.get_logger().info(f"Đã lùi đủ, bắt đầu xoay {self.turn_dir}")
                self.state = f'TURNING_{self.turn_dir}'
                self.turn_cycles = 0
                self.cmd(wz=self._wz(self.turn_dir))
            else:
                self.cmd(vx=BACKUP_SPEED)

        # 3. TRẠNG THÁI XOAY
        elif self.state in ('TURNING_LEFT', 'TURNING_RIGHT'):
            self.turn_cycles += 1
            
            # ĐÃ SỬA: Chỉ cần hướng trước mặt thoáng (> 0.2m) là thoát trạng thái xoay.
            # Không bắt buộc phía trước phải là hướng rộng nhất nữa để tránh quay tròn.
            if self.turn_cycles >= MIN_TURN_CYCLES:
                if b['F'] > CLEAR_DIST:
                    self.get_logger().info("Đường đã thoáng, tiếp tục tiến lên.")
                    self.state = 'EVALUATING'
                    self.cmd(vx=FORWARD_SPEED)
                    return

            direction = 'LEFT' if self.state == 'TURNING_LEFT' else 'RIGHT'
            self.cmd(wz=self._wz(direction))

def main(args=None):
    rclpy.init(args=args)
    node = OtonomBir()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Đang dừng robot...")
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()