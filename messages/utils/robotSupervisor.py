#! /usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist, Vector3
from argos3_ros2_bridge.msg import BlobList, Position, LightList



class RobotMessage(Node):
    def __init__(self, robotName): # add odom and cmd_vel name if needed for multiple Robots
        super().__init__(robotName+"MessageSubscriber")

        self.create_subscription(Position, "/"+robotName+"/position", self.odom_sensor_callback, 1)
        self.create_subscription(BlobList, "/"+robotName+"/blobList", self.blobList_sensor_callback, 1)
        #EXTRA: Flocking
        self.create_subscription(LightList, "/"+robotName+"/lightList", self.lightList_sensor_callback, 1)

        self.blobList = []

        self.xPos = 0.0
        self.yPos = 0.0
        self.theta = 0.0
        
        # EXTRA Flocking
        # the second light sensor returns only an angle, where it perceives the bright light in the environment
        self.globalLightAngle = 0.0
        self.globalLightDist = 0.0


    def blobList_sensor_callback(self, message):
        blobs = message.blobs
        self.blobList = blobs

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