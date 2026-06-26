#!/usr/bin/env python3
"""
apriltag_tracker.py
Controls the UGV pan-tilt to keep a detected AprilTag centered in the frame.
"""
import rclpy
from rclpy.node import Node
from apriltag_msgs.msg import AprilTagDetectionArray
from sensor_msgs.msg import JointState


class AprilTagTracker(Node):

    #  Tuning parameters 
    KP_PAN   = 0.5    # proportional gain for horizontal tracking
    KP_TILT  = 0.5    # proportional gain for vertical tracking
    MAX_PAN  = 1.57   # rad (~90), from URDF pt_link1 limit
    MAX_TILT = 0.52   # rad (~30), from URDF pt_link2 limit
    MIN_TILT = -0.52  # rad
    TARGET_ID = None  # track any tag if None, or set to specific ID e.g. 0
    # 

    def __init__(self):
        super().__init__('apriltag_tracker')

        # Current pan tilt angles initialize from current joint state
        self.pan  = 0.0
        self.tilt = 0.0

        # Subscribe to AprilTag detections
        self.create_subscription(
            AprilTagDetectionArray,
            '/apriltag_detections',
            self._detection_cb,
            1
        )

        # Subscribe to current joint states to initialize pan/tilt
        self.create_subscription(
            JointState,
            '/ugv/joint_states',
            self._joint_state_cb,
            1
        )

        # Publish pan-tilt commands to joint states
        self.cmd_pub = self.create_publisher(
            JointState,
            '/ugv/joint_states',   # adjust if topic name differs
            1
        )

        self.get_logger().info('AprilTag tracker ready.')

    def _joint_state_cb(self, msg: JointState):
        """Initialize pan/tilt from current joint positions."""
        try:
            pan_idx  = msg.name.index('pt_base_link_to_pt_link1')
            tilt_idx = msg.name.index('pt_link1_to_pt_link2')
            self.pan  = msg.position[pan_idx]
            self.tilt = msg.position[tilt_idx]
        except ValueError:
            pass  # joints not in this message

    def _detection_cb(self, msg: AprilTagDetectionArray):
        """Track the first detected tag (or TARGET_ID if set)."""
        if not msg.detections:
            return

        # Select target detection
        detection = None
        if self.TARGET_ID is None:
            detection = msg.detections[0]
        else:
            for d in msg.detections:
                if d.id == self.TARGET_ID:
                    detection = d
                    break

        if detection is None:
            return

        # Tag position in camera frame
        # tx: left/right offset positive = tag is to the right
        # ty: up/down offset   positive = tag is below center
        tx = detection.pose.pose.pose.position.x
        ty = detection.pose.pose.pose.position.y

        # P-controller: reduce offset by adjusting pan/tilt
        self.pan  -= self.KP_PAN  * tx
        self.tilt += self.KP_TILT * ty

        # Clamp to joint limits from URDF
        self.pan  = max(-self.MAX_PAN,  min(self.MAX_PAN,  self.pan))
        self.tilt = max( self.MIN_TILT, min(self.MAX_TILT, self.tilt))

        self._publish_cmd()

    def _publish_cmd(self):
        cmd = JointState()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.name     = ['pt_base_link_to_pt_link1', 'pt_link1_to_pt_link2']
        cmd.position = [self.pan, self.tilt]
        cmd.velocity = []
        cmd.effort   = []
        self.cmd_pub.publish(cmd)
        self.get_logger().debug(
            f'Pan: {self.pan:.3f} rad, Tilt: {self.tilt:.3f} rad'
        )


def main():
    rclpy.init()
    rclpy.spin(AprilTagTracker())
    rclpy.shutdown()


if __name__ == '__main__':
    main()