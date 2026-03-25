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
    
    def setSUT(self, sut=None):
        self.sut = sut

    # calculates and sets the forward and roation speed of the robot
    def calculateSpeeds(self, repulsion):
        ANGLE_TOLERANCE = 0.2 # TODO spielen
        MAX_SPEED = 0.8 #Transport chain
        #MAX_SPEED = 0.3 # Flocking
        MAX_SPEED_ROT = 2.0
        MIN_SPEED_ROT = 0.8
        MIN_SPEED = 0.4  # Transport chain
        #MIN_SPEED = 0.1 # Flocking
        GAIN = 0.2
        ANGLE_GAIN = 2 #0.05           
        
        distanceToTarget = self.geDistanceToTarget()

        # Potential Field Implementation from: https://github.com/Tim-HW/ROS2-Path-Planning-Turtlebot3-Potential-Field/blob/main/src/potentialF.cpp
        #attraction
        dx= self.xTarget- self.xPos
        dy= self.yTarget- self.yPos
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

    # ("ge" to prevent that the Model-to-JSON Part calls this function)
    def geDistanceToTarget(self):
        return math.sqrt(pow(self.xTarget - self.xPos,2)+pow(self.yTarget-self.yPos,2))
         
    def geHeadingError(self, target):
        return (target - self.theta + math.pi) % (2 * math.pi) - math.pi

    def calculateNextWaypoint(self, radius, targetX, targetY):
        DIST_THRESHOLD = 0.1

        # Waypoint Array
        waypoints = []
        for i in range(8):
            x = targetX + math.cos((math.pi/4)*i)*radius
            y = targetY + math.sin((math.pi/4)*i)*radius
            waypoints.append([x,y])

        # get the two closest waypoints
        sorted_indices = sorted(range(len(waypoints)), key=lambda i: math.dist(waypoints[i], [self.xPos, self.yPos]))
        closestWPIndex = sorted_indices[0]
        secondClosestWPIndex = sorted_indices[1]

        # SPECIAL Condition: replace closest waypoint by the third closest, if robot is very close to actual target waypoint
        if (math.dist(waypoints[closestWPIndex], [self.xPos, self.yPos])) < DIST_THRESHOLD:
            print("distance to small --> select other closest waypoint")
            closestWPIndex = sorted_indices[2]

        targetHeading1 = math.atan2(waypoints[closestWPIndex][1]-self.yPos, waypoints[closestWPIndex][0]-self.xPos)
        targetHeading2 = math.atan2(waypoints[secondClosestWPIndex][1]-self.yPos, waypoints[secondClosestWPIndex][0]-self.xPos)

        # return waypoint with smallest heading error
        if abs(self.geHeadingError(targetHeading1)) < abs(self.geHeadingError(targetHeading2)):
            return waypoints[closestWPIndex]
        else: 
            return waypoints[secondClosestWPIndex]

class SUTImpl(SUT):
    
    def __init__(self, yPos=None, xPos=None):
        super().__init__(yPos, xPos)

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
    def implementation(self, xTarget, yTarget, SUTxPos, SUTyPos, stateName):
        robot = self.robots
        if(robot != None): 
            robot.xTarget = float(xTarget)
            robot.yTarget = float(yTarget)
            print("Target setted " + str (xTarget) + " " + str(yTarget))

            for state in self.states:
                if(state.getname() == stateName):
                    robot.state = state
                    print("State setted " + state.getname())
            
            sut = SUT(float(SUTxPos),float(SUTyPos))
            robot.setSUT(sut)
            print("SUT setted")
        return False

class StateImpl(State):
    def __init__(self, id=None, name="default", speedFactor=0.0, radius=0.0):
        super().__init__(id, name, speedFactor, radius)

class MsgImpl(Message):
    def __init__(self, id=None, name="default",ledColor="blue"):
        super().__init__(id, name, ledColor)