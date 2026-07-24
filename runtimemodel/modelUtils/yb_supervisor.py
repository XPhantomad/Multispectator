#!/usr/bin/env python3
"""
UGV adapter for the Yahboom M3 Pro (Raspberry Pi, ROS2 Humble)
Pure direct control without Nav2 - reactive swarm behavior via
publishVelocity() based on odometry and laser scan data.
"""
import math
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan


# ── Config ────────────────────────────────────────────────────────────────────
COLLISION_FOV_DEG  = 60      # opening angle of the forward sector (±30°)
PROXIMITY_THRESH   = 0.55    # m - proximity for load exchange
PROXIMITY_FOV_RAD  = 1.4     # rad - opening angle for proximity check
REPULSION_DIST     = 0.3     # m - anything closer generates repulsion

# Lidar mount offset: adjusts the scan angles to the actual lidar
# mounting on the M3 Pro. If the odometry rotation looks twisted/
# inverted in RViz, adjust here (e.g. -math.pi/2, math.pi, etc.)
MOUNT_OFFSET = 0.0


class YBSupervisor(Node):
    """
    Public API:
      getxPos(), getyPos(), getzPos(), getTheta()
      getLoad(), getProximity(), getv_repulsion()
      publishVelocity(speed, angle, strafe=0.0)
      publishLight(ledColor)   -> no-op
      publishGripper(grip, release) -> no-op
    """

    def __init__(self, robot_name: str):
        super().__init__(robot_name + '_yb_supervisor')

        # ── State ─────────────────────────────────────────────────────────
        self.xPos        = 0.0
        self.yPos        = 0.0
        self.zPos        = 0.0
        self.theta       = 0.0
        self.load        = False          # no load sensor -> always False
        self.proximity   = False
        self.v_repulsion = np.array([0.00001, 0.0000001])  # default

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 1)

        # ── Subscriptions ─────────────────────────────────────────────────
        self.create_subscription(Odometry,  '/odom_rf2o', self._odom_cb, 1)
        self.create_subscription(LaserScan, '/scan',       self._scan_cb, 1)

        self.get_logger().info(f'UGVSupervisor "{robot_name}" ready.')

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry):
        """Sets xPos, yPos, theta (yaw) from the laser odometry."""
        self.xPos = msg.pose.pose.position.x
        self.yPos = msg.pose.pose.position.y
        self.zPos = msg.pose.pose.position.z

        q = msg.pose.pose.orientation
        self.theta = math.atan2(
            2.0 * (q.x * q.y + q.w * q.z),
            q.w * q.w + q.x * q.x - q.y * q.y - q.z * q.z
        )

    def _scan_cb(self, msg: LaserScan):
        """
        Computes:
          - self.v_repulsion  (repulsion vector)
          - self.proximity    (obstacle in the frontal near range)
        """
        x_r, y_r = 0.0, 0.0
        valid_points = 0
        self.proximity = False

        for i, r in enumerate(msg.ranges):
            if not (msg.range_min < r < msg.range_max):
                continue

            angle = msg.angle_min + i * msg.angle_increment + MOUNT_OFFSET

            # ── Repulsion ──────────────────────────────────────────────
            if r < REPULSION_DIST:
                repulsion_force = 1.0 / max(r, 0.01)
                x_r -= repulsion_force * math.cos(angle + self.theta)
                y_r -= repulsion_force * math.sin(angle + self.theta)
                valid_points += 1

        if valid_points == 0:
            self.v_repulsion = np.array([0.00001, 0.0000001])
        else:
            self.v_repulsion = np.array([x_r, y_r])

    # ── Getter API ─────────────────────────────────────────────────────

    def getxPos(self):        return self.xPos
    def getyPos(self):        return self.yPos
    def getzPos(self):        return self.zPos
    def getTheta(self):       return self.theta
    def getLoad(self):        return self.load
    def getProximity(self):   return self.proximity
    def getv_repulsion(self): return self.v_repulsion

    # ── Publisher API ──────────────────────────────────────────────────

    def publishVelocity(self, speed: float, angle: float, strafe: float = 0.0):
        """
        speed:  linear.x [m/s]    - forward/backward
        angle:  angular.z [rad/s] - rotation
        strafe: linear.y [m/s]    - sideways (mecanum omnidrive), positive = left
        """
        msg = Twist()
        msg.linear.x  = float(speed)
        msg.linear.y  = float(strafe)
        msg.angular.z = float(angle)
        self._cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = UGVSupervisor('robot1')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()