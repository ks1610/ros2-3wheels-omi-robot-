#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped
from rclpy.qos import qos_profile_sensor_data
import math
import random

FORCE_TURN_SIGN = 1
LIDAR_BLIND   = 0.05   # Tăng nhẹ điểm mù để lọc nhiễu sát sườn
SAFE_DIST     = 0.25   # Khoảng cách an toàn để quyết định lùi (5cm là quá sát thực tế, nâng lên 25cm)
CLEAR_DIST    = 0.40   # Khoảng cách để coi là đường cực kì thoáng
BACKUP_CYCLES = 25    
MIN_TURN_CYCLES = 15   
FORWARD_SPEED = 0.30   
BACKUP_SPEED  = -0.15
TURN_SPEED    = 1.0    

class OtonomBir(Node):
    def __init__(self):
        super().__init__('otonom_bir')
        self.sub_lidar = self.create_subscription(LaserScan, '/scan', self.lidar_callback, qos_profile_sensor_data)
        self.pub = self.create_publisher(TwistStamped, '/omni_wheel_drive_controller/cmd_vel', 10)

        self.state       = 'EXPLORING'
        self.turn_sign   = FORCE_TURN_SIGN
        self.turn_dir    = 'RIGHT'
        self.turn_cycles = 0
        self.backup_cycles = 0

    def _min(self, rays, maxv=10.0):
        valid = []
        for x in rays:
            if math.isinf(x):
                valid.append(maxv)
            elif not math.isnan(x) and x > LIDAR_BLIND:
                valid.append(x)
        return min(valid) if valid else 0.0

    def lidar_callback(self, msg):
        r = list(msg.ranges)
        n = len(r)
        
        # Bỏ cái 720 đi, chỉ cần có dữ liệu là chạy
        if n < 720: 
            return
        
        s = n // 8  # 1/8 số tia (vd: 360/8 = 45 tia)
        
        # Nếu r[0] là phía trước, vùng F sẽ là một nửa bên trái 0 và một nửa bên phải (tức là cuối mảng)
        front_rays = r[-s:] + r[:s]     # Trước mặt
        fl_rays    = r[s : 3*s]         # Trước Trái
        l_rays     = r[3*s : 5*s]       # Trái
        fr_rays    = r[-3*s : -s]       # Trước Phải
        r_rays     = r[-5*s : -3*s]     # Phải

        b_raw = {
            'F':  self._min(front_rays),
            'FL': self._min(fl_rays), 
            'L':  self._min(l_rays),
            'FR': self._min(fr_rays),
            'R':  self._min(r_rays),
        }

        # In ra để bạn debug trực tiếp
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
        self.cmd(vx=0.0, wz=0.0)

    def _wz(self, direction, speed_multiplier=1.0):
        if direction == 'LEFT':
            return -self.turn_sign * TURN_SPEED * speed_multiplier
        else:
            return self.turn_sign * TURN_SPEED * speed_multiplier

    def navigate(self, b):
        dist_front = b['F']
        dist_left_diag = b['FL']
        dist_right_diag = b['FR']
        dist_left = b['L']
        dist_right = b['R']

        # 1. TRẠNG THÁI KHÁM PHÁ (Chủ động tìm khoảng trống)
        if self.state == 'EXPLORING':
            # Nếu phía trước quá gần tường -> Đổi trạng thái sang chống kẹt
            if dist_front < SAFE_DIST or dist_left_diag < SAFE_DIST or dist_right_diag < SAFE_DIST:
                self.turn_dir = 'LEFT' if (dist_left + dist_left_diag) > (dist_right + dist_right_diag) else 'RIGHT'
                self.get_logger().info(f"Vật cản sát! Đang lùi và chuẩn bị né về {self.turn_dir}")
                self.state = 'BACKING_UP'
                self.backup_cycles = 0
                self.cmd(vx=BACKUP_SPEED)
            else:
                # Thuật toán Wander: Vừa đi thẳng vừa điều chỉnh hướng về bên thoáng hơn
                steer_z = 0.0
                
                # Nếu hai bên không đều nhau, hơi bẻ lái nhẹ về bên rộng hơn
                if dist_left_diag > CLEAR_DIST and dist_right_diag < CLEAR_DIST:
                    steer_z = self._wz('LEFT', 0.4) # Bẻ trái nhẹ
                elif dist_right_diag > CLEAR_DIST and dist_left_diag < CLEAR_DIST:
                    steer_z = self._wz('RIGHT', 0.4) # Bẻ phải nhẹ
                
                # Để tránh việc chạy thành 1 vòng tròn nếu vào bãi đất trống lớn, 
                # thỉnh thoảng thêm nhiễu ngẫu nhiên nhỏ vào góc xoay
                if dist_front > CLEAR_DIST * 2:
                    steer_z += random.uniform(-0.2, 0.2)

                self.cmd(vx=FORWARD_SPEED, wz=steer_z)

        # 2. TRẠNG THÁI LÙI LẠI (Chống kẹt)
        elif self.state == 'BACKING_UP':
            self.backup_cycles += 1
            if self.backup_cycles >= BACKUP_CYCLES:
                self.state = f'TURNING_{self.turn_dir}'
                self.turn_cycles = 0
                self.cmd(wz=self._wz(self.turn_dir))
            else:
                self.cmd(vx=BACKUP_SPEED)

        # 3. TRẠNG THÁI XOAY (Tìm đường thoát)
        elif self.state in ('TURNING_LEFT', 'TURNING_RIGHT'):
            self.turn_cycles += 1
            
            # Chỉ thoát vòng xoay khi hướng trước mặt ĐỦ RỘNG và vượt qua số vòng xoay tối thiểu
            if self.turn_cycles >= MIN_TURN_CYCLES:
                if dist_front > CLEAR_DIST and dist_left_diag > SAFE_DIST and dist_right_diag > SAFE_DIST:
                    self.get_logger().info("Đã tìm thấy hướng mở mới, tiếp tục khám phá.")
                    self.state = 'EXPLORING'
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