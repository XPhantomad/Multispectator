#! /usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist, Vector3
from tf2_msgs.msg import TFMessage
from std_msgs.msg import Float32
from tf2_msgs.msg import TFMessage


DE2RA = math.pi / 180.0
JOINT1_CENTER = 90.0   # must match the CameraController

class RobotMessage(Node):
    def __init__(self, robotName): # add odom and cmd_vel name if needed for multiple Robots
        super().__init__(robotName+"MessageSubscriber")

        self.create_subscription(TFMessage, '/tf', self._tf_cb, 10)

        self.create_subscription(Position, "/"+robotName+"/position", self.odom_sensor_callback, 1)

        self.cameraYaw = 0.0

        self.create_subscription(TFMessage, '/tf', self._tf_cb, 10)
        self.create_subscription(Float32, '/camera_arm/joint1_angle', self._cam_angle_cb, 1)

        self.blobList = []

        self.xPos = 0.0
        self.yPos = 0.0
        self.theta = 0.0
        
    def _cam_angle_cb(self, msg):
        # joint1 in degrees -> deviation from "straight ahead" (90 deg) in radians.
        # Flip CAM_YAW_SIGN if the computed positions end up mirrored
        # relative to the actual tag position.
        CAM_YAW_SIGN = 1.0
        self.cameraYaw = (msg.data - JOINT1_CENTER) * DE2RA * CAM_YAW_SIGN
        
    def _tf_cb(self, msg):
        # camera_yaw_rad = deviation of joint1 from "straight ahead" (90 deg), in rad
        heading = self.theta + camera_yaw_rad
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
    

    def odom_sensor_callback(self, message):
        self.xPos = message.position.x
        self.yPos = message.position.y
        qx = message.orientation.x
        qy = message.orientation.y
        qz = message.orientation.z
        qw = message.orientation.w
        self.theta = math.atan2(2.0*(qx*qy + qw*qz), qw*qw + qx*qx - qy*qy - qz*qz)

    # EXTRA Flocking
    def lightList_sensor_callback(self, message):
        lightList = message.lights
        max_value = 0
        for entry in lightList:
            if entry.value > max_value:
                self.globalLightAngle = entry.angle
                max_value = entry.value
        if max_value != 0 or max_value <= 0.63:
             # lightValue increases with decreasing distance (linreg with 3 value pairs returns these numbers)
            self.globalLightDist = (-7.242*max_value + 4.603)*100
        else:
            self.globalLightDist = 0.0

    # EXTRA Flocking
    def getGlobalLightAngle(self):
        return self.globalLightAngle
    def getGlobalLightDist(self):
        return self.globalLightDist

    def getBlobs(self):
        return self.blobList
    
    def getxPos(self):
        return self.xPos
    
    def getyPos(self):
        return self.yPos
    
    def getTheta(self):
        return self.theta