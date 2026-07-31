#!/usr/bin/env python3
"""
UGV-Adapter für den Waveshare UGV (Raspberry Pi, ROS2 Humble)
Ersetzt robotSupervisor.py – gleiche API, andere Topics/Msg-Typen.
"""
import math
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf_transformations import euler_from_quaternion


# ── Konfig ────────────────────────────────────────────────────────────────────
COLLISION_FOV_DEG  = 60      # Öffnungswinkel des Vorwärtssektors (±30°)
PROXIMITY_THRESH   = 0.55    # m – wie dein "i.value > 0.55" (Nähe für Load-Exchange)
PROXIMITY_FOV_RAD  = 1.4     # rad – wie dein "i.angle <= 1.4 and >= -1.4"
REPULSION_DIST     = 1.0     # m – alles näher erzeugt Repulsion


class UGVSupervisor(Node):
    """
    Gleiche öffentliche API wie RobotSupervisor:
      getxPos(), getyPos(), getzPos(), getTheta()
      getLoad(), getProximity(), getv_repulsion()
      publishVelocity(speed, angle)
      publishLight(ledColor)   → no-op (UGV hat keine LED-API hier)
      publishGripper(grip, release) → no-op (kein Greifer)
    """

    def __init__(self, robot_name: str):
        super().__init__(robot_name + '_ugv_supervisor')

        # ── State ─────────────────────────────────────────────────────────
        self.xPos        = 0.0
        self.yPos        = 0.0
        self.zPos        = 0.0
        self.theta       = 0.0
        self.load        = False          # UGV hat keinen Load-Sensor → immer False
        self.proximity   = False
        self.v_repulsion = np.array([0.00001, 0.0000001])  # Default wie Original

        self._cmd_pub = self.create_publisher(Twist, '/cmd_vel', 1)

        # ── Subscriptions ─────────────────────────────────────────────────
        # Odometry  →  /odom  (nav_msgs/Odometry)
        self.create_subscription(Odometry,  '/odom',  self._odom_cb,  1)

        # Laserscanner → /scan  (sensor_msgs/LaserScan)
        self.create_subscription(LaserScan, '/scan',  self._scan_cb,  1)

        self.get_logger().info(f'UGVSupervisor "{robot_name}" bereit.')

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry):
        """
        Entspricht odom_sensor_callback().
        Setzt xPos, yPos, theta (yaw).
        """
        self.xPos = msg.pose.pose.position.x
        self.yPos = msg.pose.pose.position.y
        self.zPos = msg.pose.pose.position.z  # (war im Original ein Tippfehler: position.x)

        q = msg.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.theta = yaw   # Original nutzt roll, UGV-Bewegung liegt in yaw

    def _scan_cb(self, msg: LaserScan):
        """
        Entspricht proximity_sensor_callback().
        Berechnet:
          - self.v_repulsion  (wie dein x_r/y_r-Vektor)
          - self.proximity    (Hindernis im Nahbereich frontal)

        Der LD19 liefert Winkel in [-π, +π] mit angle_min/angle_max.
        Wir iterieren über alle Strahlen und berechnen den Repulsionsvektor
        im gleichen Schema wie dein ARGoS-Code.
        """
        x_r, y_r    = 0.0, 0.0
        valid_points = 0
        self.proximity = False

        n     = len(msg.ranges)
        d_ang = (msg.angle_max - msg.angle_min) / max(n - 1, 1)

        for i, r in enumerate(msg.ranges):
            # Ungültige Messungen überspringen
            if not (msg.range_min < r < msg.range_max):
                continue

            angle = msg.angle_min + i * d_ang  # Winkel im Roboter-Frame

            # ── Repulsion (wie dein proximity_sensor_callback) ────────────
            if r < REPULSION_DIST:
                repulsion_force = 1.0 / max(r, 0.01)   # stärker je näher
                # Winkel in Weltkoordinaten (+ self.theta) wie im Original
                x_r -= repulsion_force * math.cos(angle + self.theta)
                y_r -= repulsion_force * math.sin(angle + self.theta)
                valid_points += 1

            # ── Proximity für Load-Exchange (frontaler Nahbereich) ────────
            if r > 0 and r < (1.0 / PROXIMITY_THRESH) and \
               -PROXIMITY_FOV_RAD <= angle <= PROXIMITY_FOV_RAD:
                self.proximity = True

        if valid_points == 0:
            self.v_repulsion = np.array([0.00001, 0.0000001])
        else:
            self.v_repulsion = np.array([x_r, y_r])

    # ── Getter-API (identisch zu RobotSupervisor) ─────────────────────────────

    def getxPos(self):       return self.xPos
    def getyPos(self):       return self.yPos
    def getzPos(self):       return self.zPos
    def getTheta(self):      return self.theta
    def getLoad(self):       return self.load        # immer False beim UGV
    def getProximity(self):  return self.proximity
    def getv_repulsion(self): return self.v_repulsion

    # ── Publisher-API (identisch zu RobotSupervisor) ──────────────────────────

    def publishVelocity(self, speed: float, angle: float):
        """Entspricht publishVelocity() – identische Signatur."""
        msg = Twist()
        msg.linear.x  = float(speed)
        msg.angular.z = float(angle)
        self._cmd_pub.publish(msg)

    def publishLight(self, led_color: str):
        """No-op: UGV-LED wird hier nicht angesteuert."""
        pass

    def publishGripper(self, grip: bool, release: bool):
        """No-op: Kein Greifer am UGV."""
        pass
