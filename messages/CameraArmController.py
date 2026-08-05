#!/usr/bin/env python3
"""
Camera arm controller for the Yahboom M3 Pro.

Idle mode:   joint1 slowly sweeps back and forth (triangle wave) between
             JOINT1_MIN and JOINT1_MAX to widen the effective camera FOV.
Track mode:  as soon as an AprilTag is detected, joint1 follows the tag's
             horizontal angle so the camera keeps it centered while the
             robot drives past. Falls back to idle scanning if the tag
             is lost for longer than TAG_LOST_TIMEOUT_S.

Uses the existing M3Pro_Demo interface: publishes to /arm6_joints
(arm_msgs/msg/ArmJoints) and subscribes to /apriltag_detections
(apriltag_msgs/msg/AprilTagDetectionArray), the same topic used by
RobotMessage.

IMPORTANT - VERIFY BEFORE RUNNING ON THE REAL ROBOT:
  1. HOME_JOINT2..HOME_JOINT6 below are placeholders. Confirm these are
     a safe resting pose for your actual arm geometry before running -
     wrong values here can make the arm collide with the chassis.
  2. CAMERA_ANGLE_TO_SERVO_SIGN is unverified. Test at low speed first
     (e.g. temporarily lower TRACK_MAX_SPEED_DEG_S) and confirm the arm
     turns towards the tag, not away from it. Flip the sign if it's
     backwards.
  3. JOINT1_MIN/JOINT1_MAX are taken from your reported safe range
     (20-160 deg). Do not loosen these without re-verifying physically
     on the robot.
"""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo
from apriltag_localization.msg import AprilTagDetectionArray
from arm_msgs.msg import ArmJoints
from std_msgs.msg import Float32


# ── Safety limits (verified safe range for joint1) ─────────────────────────
JOINT1_MIN    = 20   # deg - hard lower limit, do not exceed
JOINT1_MAX    = 160  # deg - hard upper limit, do not exceed
JOINT1_CENTER = 90   # deg - assumed "camera points straight forward"

# Home position for the other joints while in camera-scanning/tracking mode.
# PLACEHOLDER VALUES - verify these are safe for your arm before running.
HOME_JOINT2 = 135
HOME_JOINT3 = 45
HOME_JOINT4 = 0
HOME_JOINT5 = 90
HOME_JOINT6 = 45 # gripper should not be fully open (90°) --> leads to crunching noises

# ── Idle scanning behaviour ─────────────────────────────────────────────────
SCAN_SPEED_DEG_S = 20.0   # sweep speed while idle (deg/s)
CONTROL_HZ       = 1.0   # control loop / publish rate

# ── Tracking behaviour ───────────────────────────────────────────────────────
TRACK_MAX_SPEED_DEG_S      = 60.0  # max angular speed while actively tracking
TAG_LOST_TIMEOUT_S         = 2.0   # revert to idle scan after this long without a tag
CAMERA_ANGLE_TO_SERVO_SIGN = -1.0   # flip to -1.0 if tracking moves the wrong way - CALIBRATE ON ROBOT

MOVE_TIME_MS = int(1000.0 / CONTROL_HZ)  # servo move duration matches the control loop period

# ── Tracking gain ──
TRACK_KP = 2  # proportional gain (deg of servo per deg of camera error)
TRACK_DEADBAND_DEG = 2.3   # to ignore minimal changes

class CameraArmController(Node):

    def __init__(self):
        super().__init__('camera_arm_controller')

        self._current_angle = JOINT1_CENTER
        self._scan_direction = 1.0
        self._last_tag_time = None
        self._last_tag_angle_rad = None

        # Camera intrinsics - populated from /camera/color/camera_info,
        # needed to convert the tag's pixel position into an angle
        self._fx = None
        self._cx = None

        self._arm_pub = self.create_publisher(ArmJoints, '/arm6_joints', 1)
        self._joint1_angle_pub = self.create_publisher(Float32, '/camera_arm/joint1_angle', 1)

        self.create_subscription(
            CameraInfo,
            '/camera/color/camera_info',
            self._camera_info_cb,
            1
        )

        self.create_subscription(
            AprilTagDetectionArray,
            '/detections',
            self._apriltag_cb,
            1
        )

        self._timer = self.create_timer(1.0 / CONTROL_HZ, self._control_loop)

        self.get_logger().info(
            f'CameraArmController ready. joint1 limits: '
            f'[{JOINT1_MIN}, {JOINT1_MAX}] deg.'
        )

    # ── Callbacks ────────────────────────────────────────────────────────

    def _camera_info_cb(self, msg: CameraInfo):
        """Cache camera intrinsics (fx, cx) needed for angle computation."""
        self._fx = msg.k[0]
        self._cx = msg.k[2]

    def _apriltag_cb(self, msg: AprilTagDetectionArray):
        if not msg.detections:
            return  # no tag right now - let the control loop time out on its own

        if self._fx is None or self._cx is None:
            print("frame skipped, because of no camera info")
            return  # camera_info not received yet - skip this frame

        # Tracks the first detection in the list. If you want to prefer
        # a specific tag instead, filter/sort msg.detections here.
        detection = msg.detections[0]
        px = detection.centre.x

        # Same convention as RobotMessage: positive = left.
        # No depth/3D pose in this message - angle is derived purely from
        # the pixel offset from the image center and the focal length
        self._last_tag_angle_rad = math.atan2(-(px - self._cx), self._fx)
        self._last_tag_time = self.get_clock().now()

    # ── Control loop ─────────────────────────────────────────────────────

    def _control_loop(self):

        tag_visible = self._is_tag_currently_visible()
        max_step_deg = (TRACK_MAX_SPEED_DEG_S if tag_visible else SCAN_SPEED_DEG_S) / CONTROL_HZ

        if tag_visible:
            # Proportional correction relative to CURRENT position, not center.
            error_deg = math.degrees(self._last_tag_angle_rad) * CAMERA_ANGLE_TO_SERVO_SIGN
            # Dead band: Ignore minor errors so that the arm doesn't wobble around the center
            if abs(error_deg) < TRACK_DEADBAND_DEG:
                desired_angle = self._current_angle   # halten
            else:
                desired_angle = self._current_angle + TRACK_KP * error_deg

        else:
            desired_angle = self._next_scan_angle()

        desired_angle = self._clamp(desired_angle)

        delta = desired_angle - self._current_angle
        step = max(-max_step_deg, min(max_step_deg, delta))
        self._current_angle = self._clamp(self._current_angle + step)
        self._publish_arm(self._current_angle)

    def _is_tag_currently_visible(self) -> bool:
        if self._last_tag_time is None:
            return False
        elapsed_s = (self.get_clock().now() - self._last_tag_time).nanoseconds / 1e9
        return elapsed_s < TAG_LOST_TIMEOUT_S


    def _next_scan_angle(self) -> float:
        """Triangle-wave sweep between JOINT1_MIN and JOINT1_MAX."""
        step = (SCAN_SPEED_DEG_S / CONTROL_HZ) * self._scan_direction
        next_angle = self._current_angle + step

        if next_angle >= JOINT1_MAX:
            next_angle = JOINT1_MAX
            self._scan_direction = -1.0
        elif next_angle <= JOINT1_MIN:
            next_angle = JOINT1_MIN
            self._scan_direction = 1.0

        return next_angle

    @staticmethod
    def _clamp(angle: float) -> float:
        return max(JOINT1_MIN, min(JOINT1_MAX, angle))

    def _publish_arm(self, joint1_angle: float):
        msg = ArmJoints()
        msg.joint1 = int(joint1_angle)
        msg.joint2 = HOME_JOINT2
        msg.joint3 = HOME_JOINT3
        msg.joint4 = HOME_JOINT4
        msg.joint5 = HOME_JOINT5
        msg.joint6 = HOME_JOINT6
        msg.time = MOVE_TIME_MS
        self._arm_pub.publish(msg)

        angle_msg = Float32()
        angle_msg.data = float(joint1_angle)
        self._joint1_angle_pub.publish(angle_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraArmController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()