#!/usr/bin/env python3
"""
SUT Robot Teleop Tool

Usage:
    ros2 run <your_pkg> sut_teleop.py 3
    or
    python3 sut_teleop.py 3

Controls:
    w / s : forward / backward
    a / d : turn left / turn right
    space : stop
    l     : toggle LED on/off
    q     : quit
"""



import sys
import termios
import tty
import select
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from argos3_ros2_bridge.msg import Position, Led, Load, Grip, ProximityList
import time

# ---- Tunable parameters ----
LINEAR_SPEED = 0.2      # m/s
ANGULAR_SPEED = 1.0     # rad/s
PUBLISH_RATE = 10.0     # Hz (steady stream needed for continuous motion)
SINGLE = "SINGLE"
ALL = "ALL"

HELP = """
Control Your SUT Robot
----------------------
   w
a  s  d        w/s : move forward/back
               a/d : turn left/right
space : stop
l     : toggle LED
q     : quit
"""

colors = ["red", "yellow", "orange", "green", "white", "blue", "magenta", "brown"]

class SutTeleop(Node):
    def __init__(self, sut_number: int):
        super().__init__(f'sut_teleop_{sut_number}')

        self.sut_number = sut_number

        # Adjust these patterns to match your actual topic names
        cmd_vel_topic = f'/SUT{sut_number}/cmd_vel'
        cmd_led_topic = f'/SUT{sut_number}/cmd_led'

        self.vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.led_pub = self.create_publisher(Led, cmd_led_topic, 10)

        self.twist = Twist()
        self.led_mode = SINGLE

        self.get_logger().info(f'Publishing velocity to: {cmd_vel_topic}')
        self.get_logger().info(f'Publishing LED to:      {cmd_led_topic}')

        # Steady stream publisher
        self.timer = self.create_timer(1.0 / PUBLISH_RATE, self.publish_velocity)

    def publish_velocity(self):
        self.vel_pub.publish(self.twist)

    def set_velocity(self, linear=0.0, angular=0.0):
        self.twist.linear.x = linear
        self.twist.angular.z = angular
        self.publish_velocity()

    def toggle_led(self):
        msg = Led()
        # Switch between SINGLE and ALL
        if self.led_mode == ALL:
            self.led_mode = SINGLE
            # 1. set all leds to black
            msg.color = 'black' #colors[self.sut_number]
            msg.mode = ALL
            msg.index = 12
            self.led_pub.publish(msg) 
            #print(msg)
            time.sleep(1)
            # 2. set one to the desired color again
            msg = Led()
            msg.color = colors[self.sut_number]
            msg.mode = SINGLE
            msg.index = 12
            self.led_pub.publish(msg)
            #print(msg)

        else:
            self.led_mode = ALL
            msg.color = colors[self.sut_number]
            msg.mode = ALL
            msg.index = 12
            self.led_pub.publish(msg)
            #print(msg)

        #mode_name = 'ALL' if self.led_mode == Led.ALL else 'SINGLE'
        #self.get_logger().info(f'LED mode set to {mode_name}')


def get_key(settings, timeout=0.1):
    """Read a single keypress (non-blocking)."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    key = sys.stdin.read(1) if rlist else ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def main():
    if len(sys.argv) < 2:
        print('Usage: sut_teleop.py <SUT_NUMBER>')
        sys.exit(1)

    try:
        sut_number = int(sys.argv[1])
    except ValueError:
        print('SUT number must be an integer.')
        sys.exit(1)

    rclpy.init()
    node = SutTeleop(sut_number)

    settings = termios.tcgetattr(sys.stdin)
    print(HELP)

    try:
        while rclpy.ok():
            # Process ROS callbacks (keeps the steady-stream timer firing)
            rclpy.spin_once(node, timeout_sec=0.0)

            key = get_key(settings)

            if key == 'w':
                node.set_velocity(linear=LINEAR_SPEED)
            elif key == 's':
                node.set_velocity(linear=-LINEAR_SPEED)
            elif key == 'a':
                node.set_velocity(angular=ANGULAR_SPEED)
            elif key == 'd':
                node.set_velocity(angular=-ANGULAR_SPEED)
            elif key == ' ':
                node.set_velocity(0.0, 0.0)
            elif key == 'l':
                node.toggle_led()
            elif key == 'q':
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot before exiting
        node.set_velocity(0.0, 0.0)
        node.vel_pub.publish(Twist())
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print('\nStopped and exited.')


if __name__ == '__main__':
    main()
