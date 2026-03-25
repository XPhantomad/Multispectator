#! /usr/bin/env python3
import math

import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist, Vector3
from argos3_ros2_bridge.msg import Position, Led, Load, Grip, ProximityList



class RobotSupervisor(Node):
    def __init__(self, robotName): # add odom and cmd_vel name if needed for multiple Robots
        super().__init__(robotName+"PositionSubscriber")
        
        self.xPos = 0.0
        self.yPos = 0.0
        self.zPos = 0.0
        self.theta = 0.0
        self.load = False
        self.proximity = False
        self.v_repulsion = np.array([0.0, 0.0])

        self.message_vel = Twist()
        self.message_led = Led()
        self.message_grip = Grip()

        self.create_subscription(Position, "/"+robotName+"/position", self.odom_sensor_callback, 1)
        self.create_subscription(Load, "/"+robotName+"/load", self.load_sensor_callback, 1)
        self.create_subscription(ProximityList, "/"+robotName+"/proximityList", self.proximity_sensor_callback, 1)

        self.publisher_vel =self.create_publisher(Twist, "/"+robotName+"/cmd_vel",1)
        self.publisher_grip = self.create_publisher(Grip, "/"+robotName+"/cmd_grip", 1)
        self.publisher_light = self.create_publisher(Led, "/"+robotName+"/cmd_led", 1)

    def load_sensor_callback(self, message):
        self.load = message.load

    def proximity_sensor_callback(self, message):
        proximities = message.proximities
        self.proximity = False
        x_r = 0
        y_r = 0
        valid_points=0
        for i in proximities:
            # get if an obstacle is near for collission avoidance
            if (i.value > 0.0):
                repulsion_force = i.value # 50 / (4 * math.pi * i.value * i.value)
                x_r -= repulsion_force * math.cos(i.angle+self.theta)
                y_r -= repulsion_force * math.sin(i.angle+self.theta)
                valid_points+=1 
            # get required proximity for load exchange
            if (i.value > 0.55 and i.angle <= 1.4 and i.angle >= -1.4):
                self.proximity = True
                #break
        if(valid_points == 0):
            self.v_repulsion = np.array([0.00001, 0.0000001])
        else:
            self.v_repulsion = np.array([x_r, y_r])
            

    def odom_sensor_callback(self, message):
        self.xPos = message.position.x
        self.yPos = message.position.y
        self.zPos = message.position.x
        qx = message.orientation.x
        qy = message.orientation.y
        qz = message.orientation.z
        qw = message.orientation.w
        roll = math.atan2(2.0*(qx*qy + qw*qz), qw*qw + qx*qx - qy*qy - qz*qz)
        #print(f'position: ({self.xPos:.4f},{self.yPos:.4f},{self.zPos:.4f}) orientation: ({qx:.4f},{qy:.4f},{qz:.4f},{qw:.4f}) yaw/pitch/roll: ({yaw:.4f},{pitch:.4f},{roll:.4f})')

        self.theta = roll
        #print(self.theta)
    
        
    def publishVelocity(self, speed, angle):
        self.message_vel.linear.x = speed
        self.message_vel.angular.z = angle
        self.publisher_vel.publish(self.message_vel)
    
    def publishLight(self, ledColor):
        self.message_led.color = ledColor
        self.message_led.mode = "SINGLE"
        self.message_led.index = 12
        self.publisher_light.publish(self.message_led)

    def publishGripper(self, grip, release):
        self.message_grip.grip = grip
        self.message_grip.release = release
        self.publisher_grip.publish(self.message_grip)

    def getxPos(self):
        return self.xPos
    
    def getyPos(self):
        return self.yPos
    
    def getzPos(self):
        return self.zPos
    
    def getTheta(self):
        return self.theta

    def getLoad(self):
        return self.load
    
    def getProximity(self):
        return self.proximity

    def getv_repulsion(self):
        return self.v_repulsion

