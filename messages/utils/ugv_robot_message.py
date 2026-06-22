#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from apriltag_msgs.msg import AprilTagDetectionArray


class RobotMessage(Node):

    def __init__(self, robot_name: str):
        super().__init__(robot_name + '_message_subscriber')

        # Own robot position
        self.xPos  = 0.0
        self.yPos  = 0.0
        self.theta = 0.0

        # AprilTag detections in blob format
        # Each entry: {"color": str(tag_id), "angle": float, "distance": float}
        self._blobList = []

        # Subscribe to odometry
        self.create_subscription(
            Odometry,
            '/odom_rf2o',
            self._odom_cb,
            1
        )

        # Subscribe to AprilTag detections
        self.create_subscription(
            AprilTagDetectionArray,
            '/apriltag_detections',
            self._apriltag_cb,
            1
        )

        self.get_logger().info(f'RobotMessage "{robot_name}" ready.')

    # -- Callbacks ---------------------------------------------------------

    def _odom_cb(self, msg: Odometry):
        """Update robot pose from odometry."""
        self.xPos = msg.pose.pose.position.x
        self.yPos = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.theta = math.atan2(
            2.0 * (q.x * q.y + q.w * q.z),
            q.w * q.w + q.x * q.x - q.y * q.y - q.z * q.z
        )

    def _apriltag_cb(self, msg: AprilTagDetectionArray):
       
        blobs = []
        for detection in msg.detections:
            tag_id = str(detection.id)

            # Camera frame: x = right, z = forward
            tx = detection.pose.pose.pose.position.x
            tz = detection.pose.pose.pose.position.z

            # Distance in cm (matches ARGoS blob.distance unit)
            distance_m  = math.sqrt(tx * tx + tz * tz)
            distance_cm = distance_m * 100.0

            # Angle in camera frame (positive = left)
            angle_cam = math.atan2(-tx, tz)

            # Camera points forward = robot forward direction
            # Add camera mount offset here if needed: angle_cam += CAMERA_MOUNT_OFFSET
            angle_robot = angle_cam

            blobs.append({
                "tag_id":    tag_id,       # tag ID used as color identifier
                "x": tx,
                "z": tz
            })

        self._blobList = blobs

    # -- Getter API (identical to ARGoS RobotMessage) ----------------------

    def getBlobs(self):
        return self._blobList

    def getxPos(self):
        return self.xPos

    def getyPos(self):
        return self.yPos

    def getTheta(self):
        return self.theta

    def getGlobalLightAngle(self):
        return 0.0  # no light sensor on UGV

    def getGlobalLightDist(self):
        return 0.0