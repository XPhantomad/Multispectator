#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import Float32
from cv_bridge import CvBridge
from apriltag_localization.msg import AprilTagDetectionArray


# Camera mounting offset relative to the robot base (in meters), measured
# in the robot frame at joint1 = 90 deg (camera facing straight forward).
# PLACEHOLDER - measure/calibrate on the real robot if you need higher
# positional accuracy. Currently assumed to sit on the rotation axis.
CAMERA_OFFSET_X = 0.0
CAMERA_OFFSET_Y = 0.0

JOINT1_CENTER_DEG = 90.0  # joint1 angle at which the camera faces straight forward


class RobotMessage(Node):

    def __init__(self, robot_name: str):
        super().__init__(robot_name + '_message_subscriber')

        # Own robot position
        self.xPos  = 0.0
        self.yPos  = 0.0
        self.theta = 0.0

        # Current arm joint1 angle (deg) - needed because the camera
        # rotates with the arm, not with the robot base itself.
        self._joint1_deg = JOINT1_CENTER_DEG

        # Camera intrinsics - populated from /camera/color/camera_info,
        # needed to convert pixel coordinates + depth into a 3D point.
        self._fx = None
        self._fy = None
        self._cx = None
        self._cy = None

        self._depth_bridge = CvBridge()
        self._latest_depth_image = None  # most recent depth frame, meters

        # AprilTag detections in blob format
        # Each entry: {"tag_id": str, "angle": float, "pixel_x": float,
        #              "pixel_y": float, "global_x": float or None,
        #              "global_y": float or None}
        # global_x/global_y are None if no valid depth was available.
        self._blobList = []

        self.create_subscription(
            Odometry,
            '/odom_rf2o',
            self._odom_cb,
            1
        )

        self.create_subscription(
            CameraInfo,
            '/camera/color/camera_info',
            self._camera_info_cb,
            1
        )

        self.create_subscription(
            Image,
            '/camera/depth/image_raw',
            self._depth_cb,
            1
        )

        # Current joint1 angle, published by camera_arm_controller.py itself -
        # needed because the camera rotates with the arm, not the robot base.
        self.create_subscription(
            Float32,
            '/camera_arm/joint1_angle',
            self._curjoints_cb,
            1
        )

        self.create_subscription(
            AprilTagDetectionArray,
            '/detections',
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

    def _camera_info_cb(self, msg: CameraInfo):
        """Cache camera intrinsics needed for pixel -> 3D conversion."""
        self._fx = msg.k[0]
        self._fy = msg.k[4]
        self._cx = msg.k[2]
        self._cy = msg.k[5]

    def _depth_cb(self, msg: Image):
        """Cache the latest depth frame (assumed aligned to the color frame,
        same as the pattern used in Yahboom's own grasp node)."""
        depth_image = self._depth_bridge.imgmsg_to_cv2(msg, '32FC1')
        self._latest_depth_image = depth_image

    def _curjoints_cb(self, msg: Float32):
        """Track the current joint1 angle, since the camera rotates with it."""
        self._joint1_deg = msg.data

    def _apriltag_cb(self, msg: AprilTagDetectionArray):
        if self._fx is None or self._cx is None:
            return  # camera_info not received yet - skip this frame

        blobs = []
        for detection in msg.detections:
            tag_id = str(detection.id)

            px = detection.centre.x
            py = detection.centre.y

            angle_cam = math.atan2(-(px - self._cx), self._fx)

            global_x, global_y = self._compute_global_position(px, py)

            blobs.append({
                "tag_id":   tag_id,
                "angle":    angle_cam,
                "global_x": global_x,
                "global_y": global_y,
            })

        self._blobList = blobs

    # -- Geometry helpers ----------------------------------------------------

    def _compute_global_position(self, px: float, py: float):
        """
        Converts a detected tag's pixel position into a global (x, y)
        position using the depth image, the camera intrinsics, the
        current arm rotation (joint1), and the robot's own pose.

        Returns (None, None) if no valid depth is available at that pixel.
        """
        if self._latest_depth_image is None:
            return None, None

        ix, iy = int(py), int(px)
        h, w = self._latest_depth_image.shape[:2]
        if not (0 <= iy < h and 0 <= ix < w):
            return None, None

        depth_m = float(self._latest_depth_image[iy, ix])
        if depth_m <= 0.0 or math.isnan(depth_m):
            return None, None  # invalid depth reading at this pixel

        # Pixel + depth -> 3D point in the camera frame (camera looking
        # along its own z-axis, x = right, y = down - standard pinhole model)
        x_cam = (px - self._cx) * depth_m / self._fx
        z_cam = depth_m  # "forward" distance from the camera

        # Combine robot heading with the camera's own rotation from joint1
        # (joint1 = JOINT1_CENTER_DEG means camera faces straight forward,
        # i.e. contributes zero additional rotation)
        joint1_offset_rad = math.radians(self._joint1_deg - JOINT1_CENTER_DEG)
        combined_heading = self.theta + joint1_offset_rad

        # Camera-relative forward/right offsets, rotated into the world frame
        forward = z_cam
        right   = x_cam

        dx = forward * math.cos(combined_heading) - right * math.sin(combined_heading)
        dy = forward * math.sin(combined_heading) + right * math.cos(combined_heading)

        # Camera mount offset relative to the robot base, also rotated
        # into the world frame
        mount_dx = CAMERA_OFFSET_X * math.cos(self.theta) - CAMERA_OFFSET_Y * math.sin(self.theta)
        mount_dy = CAMERA_OFFSET_X * math.sin(self.theta) + CAMERA_OFFSET_Y * math.cos(self.theta)

        global_x = self.xPos + mount_dx + dx
        global_y = self.yPos + mount_dy + dy

        return global_x, global_y

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