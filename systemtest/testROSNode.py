import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class TestROSSupervisor(Node):
    def __init__(self, robot_count=4):
        super().__init__("testnode")

        self.xPos = 0.0

        # store all robot data here
        self.robots = {
            i: {
                "angle": 0.0,
                "first_time": True
            } for i in range(robot_count)
        }

        self.angleNotNullCount = 0

        # odom (global)
        self.create_subscription(Odometry, "/odom", self.odom_callback, 10)

        # create subscriptions dynamically
        for i in range(robot_count):
            topic = f"/fb_{i}/cmd_vel"

            self.create_subscription(
                Twist,
                topic,
                self.create_cmdvel_callback(i),
                10
            )

    def odom_callback(self, msg):
        self.xPos = msg.pose.pose.position.x

    def create_cmdvel_callback(self, robot_id):
        def callback(msg):
            robot = self.robots[robot_id]

            if msg.angular.z != 0.0 and robot["first_time"]:
                robot["first_time"] = False
                self.angleNotNullCount += 1

            robot["angle"] = msg.angular.z

        return callback