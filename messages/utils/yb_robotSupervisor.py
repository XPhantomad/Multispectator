#! /usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist, Vector3
from tf2_msgs.msg import TFMessage
from std_msgs.msg import Float32
from nav_msgs.msg import Odometry


DE2RA = math.pi / 180.0
JOINT1_CENTER = 90.0   # must match the CameraController

class RobotMessage(Node):
    def __init__(self, robotName): # add odom and cmd_vel name if needed for multiple Robots
        super().__init__(robotName+"MessageSubscriber")


        self.create_subscription(Odometry,'/odom_rf2o', self._odom_cb, 1)
        self.cameraYaw = 0.0

        self.create_subscription(TFMessage, '/tf', self._tf_cb, 10)
        self.create_subscription(Float32, '/camera_arm/joint1_angle', self._cam_angle_cb, 1)

        self.blobList = []

        self.xPos = 0.0
        self.yPos = 0.0
        self.theta = 0.0
        
    def _cam_angle_cb(self, msg):
        # joint1 in degrees -> deviation from "straight ahead" (90 deg) in radians.
        CAM_YAW_SIGN = -1.0  # calibrated: was inverted relative to the world heading convention
        self.cameraYaw = (msg.data - JOINT1_CENTER) * DE2RA * CAM_YAW_SIGN
        
    def _tf_cb(self, msg):
        # self.cameraYaw = deviation of joint1 from "straight ahead" (90 deg), in rad
        heading = self.theta + self.cameraYaw
        cos_t = math.cos(heading)
        sin_t = math.sin(heading)

        detected = []
        for tf in msg.transforms:
            if not tf.child_frame_id.startswith("tag"):
                continue

            tag_id = int(tf.child_frame_id.split(":")[1])   # "tag36h11:59" -> 59
            t = tf.transform.translation

            # Camera optical frame: x=right, y=down, z=forward
            fwd  = t.z
            left = -t.x

            # rotate into the global offset (by the robot's orientation theta)
            detected.append({
                "tag_id":   tag_id,
                "global_x": fwd * cos_t - left * sin_t,
                "global_y": fwd * sin_t + left * cos_t,
            })
        self.blobList = detected
    

    def _odom_cb(self, msg: Odometry):
        """Update robot pose from odometry."""
        self.xPos = msg.pose.pose.position.x
        self.yPos = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.theta = math.atan2(
            2.0 * (q.x * q.y + q.w * q.z),
            q.w * q.w + q.x * q.x - q.y * q.y - q.z * q.z
        )

    def getBlobs(self):
        return self.blobList
    
    def getxPos(self):
        return self.xPos
    
    def getyPos(self):
        return self.yPos
    
    def getTheta(self):
        return self.theta