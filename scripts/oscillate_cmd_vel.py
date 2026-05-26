#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class OscillateCmdVel(Node):
    def __init__(self):
        super().__init__('oscillate_cmd_vel')

        self.declare_parameter('cmd_vel_topic', '/odin2/cmd_vel')
        self.declare_parameter('speed', 0.8)
        self.declare_parameter('period', 4.0)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.speed = float(self.get_parameter('speed').value)
        self.period = max(float(self.get_parameter('period').value), 0.2)
        self.direction = 1.0
        self.last_switch_time = self.get_clock().now()

        self.publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.timer = self.create_timer(0.05, self.publish_twist)

    def publish_twist(self):
        now = self.get_clock().now()
        elapsed = (now - self.last_switch_time).nanoseconds / 1e9
        if elapsed >= self.period:
            self.direction *= -1.0
            self.last_switch_time = now

        twist = Twist()
        twist.linear.x = self.speed * self.direction
        self.publisher.publish(twist)


def main():
    rclpy.init()
    node = OscillateCmdVel()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
