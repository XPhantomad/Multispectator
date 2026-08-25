import math

import numpy as np
from model.robotModel import *

class RobotImpl(Robot):    
    def __init__(self, xPos=0.0, yPos=0.0, zPos = 0.0, xTarget=0.0, yTarget=0.0, name = "newRobot", id=12, goalReached = True, theta = 0.0, sut=None):
        super().__init__(xPos, yPos, zPos, id, name,xTarget,yTarget, goalReached, theta, None, 0.0, 0.0)
    
    def setPos(self, x, y,z, theta):
        self.xPos =x
        self.yPos = y
        self.zPos = z
        self.theta = theta

    def setstate(self, state=None):
        self.state = state
    
    def setmessage(self, message=None):
        self.message = message

    # calculates and sets the forward and roation speed of the robot
    def calculateSpeeds(self, repulsion, xTarget, yTarget):
        ANGLE_TOLERANCE = 0.3 # TODO spielen
        MAX_SPEED = 0.6 #Transport chain
        #MAX_SPEED = 0.3 # Flocking
        MAX_SPEED_ROT = 0.4
        MIN_SPEED_ROT = 0.1
        MIN_SPEED = 0.2  # Transport chain
        #MIN_SPEED = 0.1 # Flocking
        GAIN = 0.3
        ANGLE_GAIN = 0.5 #0.05           
        
        distanceToTarget = self.geDistanceToTarxet()
        if(distanceToTarget <= 0):
            return

        # Potential Field Implementation from: https://github.com/Tim-HW/ROS2-Path-Planning-Turtlebot3-Potential-Field/blob/main/src/potentialF.cpp
        #attraction
        dx= xTarget- self.xPos
        dy= yTarget- self.yPos
        attraction = np.array([dx/distanceToTarget, dy/distanceToTarget])
        #print("attraction" + str(attraction))
        #print("repulsion" + str(repulsion))

        x_final = attraction[0] + repulsion[0]
        y_final = attraction[1] + repulsion[1]

        targetHeading = math.atan2(y_final, x_final)
        headingError = self.geHeadingError(targetHeading)

        if(abs(headingError) > ANGLE_TOLERANCE):
            self.speed = 0.0
            self.rotationSpeed = ANGLE_GAIN * headingError * self.state.speedFactor
            if abs(self.rotationSpeed) > MAX_SPEED_ROT:
                self.rotationSpeed = (MAX_SPEED_ROT * -1.0) if self.rotationSpeed < 0 else MAX_SPEED_ROT
            if abs(self.rotationSpeed) < MIN_SPEED_ROT:
                self.rotationSpeed = MIN_SPEED_ROT * -1.0 if self.rotationSpeed < 0 else MIN_SPEED_ROT

        else:
            self.rotationSpeed = 0.0 
            self.speed = GAIN * distanceToTarget * self.state.speedFactor
            self.speed = self.speed if self.speed<MAX_SPEED else MAX_SPEED 
            self.speed = self.speed * self.state.speedFactor # speed factor has a value between 0 and 1
            self.speed = self.speed if self.speed>MIN_SPEED else MIN_SPEED

    # ("ge" and "tarxet" to prevent that the Model-to-JSON Part calls this function)
    def geDistanceToTarxet(self):
        return math.dist([self.xTarget, self.yTarget], [self.xPos, self.yPos])
         
    def geHeadingError(self, target, base=None):
        if base is None:
            base = self.theta
        return (target - base + math.pi) % (2 * math.pi) - math.pi

    # def calculateNextWaypoint(self, radius, targetX, targetY):
    #     NUM_CORNERS = 6                  # Hexagon
    #     ADVANCE_THRESHOLD = 0.1         # m: wie nah an einer Ecke, bevor zur nächsten gewechselt wird
    #     ORBIT_DIR = 1                    # +1 = CCW, -1 = CW

    #     step = 2 * math.pi / NUM_CORNERS  # 60°

    #     # aktueller Winkel des Roboters um das Zentrum
    #     currentAngle = math.atan2(self.yPos - targetY, self.xPos - targetX)

    #     # nächste Ecke in Umlaufrichtung als Vielfaches von 'step'
    #     # (auf das Raster runden, dann einen Schritt weiter)
    #     k = round(currentAngle / step)
    #     nextAngle = (k + ORBIT_DIR) * step

    #     nextX = targetX + math.cos(nextAngle) * radius
    #     nextY = targetY + math.sin(nextAngle) * radius

    #     # Ist der Roboter schon nah genug an der aktuellen Ziel-Ecke?
    #     # Dann überspringe eine weitere Ecke, damit er nicht "klebt".
    #     currentCornerX = targetX + math.cos(k * step) * radius
    #     currentCornerY = targetY + math.sin(k * step) * radius
    #     if math.dist([currentCornerX, currentCornerY], [self.xPos, self.yPos]) < ADVANCE_THRESHOLD:
    #         nextAngle = (k + 2 * ORBIT_DIR) * step
    #         nextX = targetX + math.cos(nextAngle) * radius
    #         nextY = targetY + math.sin(nextAngle) * radius

    #     return [nextX, nextY]

    # def get_waypoint(self, radius, target_x, target_y):
    #     phi = math.atan2(robot_y - target_y, robot_x - target_x)
    #     idx = round(phi / self.step)

    #     # Distanz zur aktuell "eingerasteten" Ecke
    #     cur_angle = idx * self.step
    #     cx = target_x + radius * math.cos(cur_angle)
    #     cy = target_y + radius * math.sin(cur_angle)
    #     dist = math.hypot(cx - robot_x, cy - robot_y)

    #     # Erst weiterschalten, wenn aktuelle Ecke erreicht UND (optional) langsam
    #     if dist < 0.15:
    #         idx += self.direction

    #     next_angle = idx * self.step
    #     nx = target_x + self.radius * math.cos(next_angle)
    #     ny = target_y + self.radius * math.sin(next_angle)
    #     return [nx, ny]

    def geMovementDirection(self):
        """
        Computes the actual world-frame direction the robot is translating in,
        combining forward and strafe speed in the robot's body frame and
        rotating it by the current heading (which is always pointed at the center).
        """
        # body-frame velocity: x = forward, y = strafe (positive = left, ROS convention)
        vx_body = self.speed
        vy_body = self.strafe

        # if robot isn't moving, fall back to heading itself
        if abs(vx_body) < 1e-6 and abs(vy_body) < 1e-6:
            return self.theta

        # rotate body-frame velocity into world frame using current heading
        vx_world = vx_body * math.cos(self.theta) - vy_body * math.sin(self.theta)
        vy_world = vx_body * math.sin(self.theta) + vy_body * math.cos(self.theta)

        return math.atan2(vy_world, vx_world)

    def calculateNextWaypoint(self, radius, targetX, targetY):
        DIST_THRESHOLD = 0.2

        # Waypoint Array
        waypoints = []
        for i in range(6):
            x = targetX + math.cos((math.pi/4)*i)*radius
            y = targetY + math.sin((math.pi/4)*i)*radius
            waypoints.append([x,y])

        # get the two closest waypoints
        sorted_indices = sorted(range(len(waypoints)), key=lambda i: math.dist(waypoints[i], [self.xPos, self.yPos]))
        closestWPIndex = sorted_indices[0]
        secondClosestWPIndex = sorted_indices[1]

        # SPECIAL Condition: replace closest waypoint by the third closest, if robot is very close to actual target waypoint
        if (math.dist(waypoints[closestWPIndex], [self.xPos, self.yPos])) < DIST_THRESHOLD:
            #print("distance to small --> select other closest waypoint")
            closestWPIndex = sorted_indices[2]

        targetHeading1 = math.atan2(waypoints[closestWPIndex][1]-self.yPos, waypoints[closestWPIndex][0]-self.xPos)
        targetHeading2 = math.atan2(waypoints[secondClosestWPIndex][1]-self.yPos, waypoints[secondClosestWPIndex][0]-self.xPos)

        # return waypoint with smallest heading error
        if abs(self.geHeadingError(targetHeading1)) < abs(self.geHeadingError(targetHeading2)):
            return waypoints[closestWPIndex]
        else: 
            return waypoints[secondClosestWPIndex]

    # def get_waypoint(self, target_x, target_y):
    #     dx = self.xPos - target_x
    #     dy = self.yPos - target_y
    #     dist = math.hypot(dx, dy)

    #     # Zentrums-Guard: im Mittelpunkt ist der Winkel bedeutungslos
    #     # -> feste Startecke, kein Kreiseln
    #     if dist < 0.05:
    #         return [target_x + self.radius, target_y]   # Ecke 0

    #     # aktuelle Winkelposition um das Target -> einrasten
    #     phi = math.atan2(dy, dx)
    #     idx = round(phi / self.step)

    #     # immer EINE Ecke VORAUS im festen Umlaufsinn
    #     next_idx = idx + self.direction
    #     angle = next_idx * self.step

    #     return [target_x + self.radius * math.cos(angle),
    #             target_y + self.radius * math.sin(angle)]

class ModelImpl(Model):

    def __init__(self, robot=None, states=None, messages=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))
        super().__init__(robot, states, messages)

    def addRobot(self, robot):
        self.robots = robot

    def removeRobot(self):
        self.robots= None
    
    # takes data from goal-message and implement them to a specific goal for the runtimemodel
    def implementation(self, xTarget, yTarget, stateName):
        robot = self.robots
        if(robot != None): 
            robot.xTarget = float(xTarget)
            robot.yTarget = float(yTarget)
            print("Target setted " + str (xTarget) + " " + str(yTarget))

            for state in self.states:
                if(state.getname() == stateName):
                    robot.state = state
                    print("State setted " + state.getname())
        return False

class StateImpl(State):
    def __init__(self, id=None, name="default", speedFactor=0.0, radius=0.0):
        super().__init__(id, name, speedFactor, radius)

class MsgImpl(Message):
    def __init__(self, id=None, name="default",ledColor="blue"):
        super().__init__(id, name, ledColor)