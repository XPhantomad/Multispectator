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


    def calculateSpeeds(self, repulsion, xTarget, yTarget, desiredHeading):
        ANGLE_TOLERANCE = 0.2
        MAX_SPEED = 0.5         # forward
        MAX_STRAFE = 0.5        # sideways - oft niedriger als forward beim Mecanum
        MAX_SPEED_ROT = 2.0
        MIN_SPEED_ROT = 0.8
        MIN_SPEED = 0.2         # Mindest-Gesamtgeschwindigkeit, sobald Bewegung nötig ist
        GAIN = 0.2
        ANGLE_GAIN = 2

        distanceToTarget = self.geDistanceToTarxet()
        if distanceToTarget <= 1e-3:
            self.speed = 0.0
            self.strafe = 0.0
            self.rotationSpeed = 0.0
            return

        dx = xTarget - self.xPos
        dy = yTarget - self.yPos
        attraction = np.array([dx / distanceToTarget, dy / distanceToTarget])
        print("attraction" + str(attraction))
        print("repulsion" + str(repulsion))

        x_final = attraction[0] + repulsion[0]
        y_final = attraction[1] + repulsion[1]

        body_x =  math.cos(self.theta) * x_final + math.sin(self.theta) * y_final
        body_y = -math.sin(self.theta) * x_final + math.cos(self.theta) * y_final

        # direkte Skalierung statt Normalisierung — Feldstärke bleibt pro Achse erhalten
        self.speed  = body_x * GAIN * self.state.speedFactor
        self.strafe = body_y * GAIN * self.state.speedFactor

        # getrennte Obergrenzen je Achse (Mecanum ist seitlich oft langsamer als vorwärts)
        self.speed  = max(-MAX_SPEED, min(MAX_SPEED, self.speed))
        self.strafe = max(-MAX_STRAFE, min(MAX_STRAFE, self.strafe))

        # Mindestgeschwindigkeit auf die GESAMTBEWEGUNG anwenden, nicht pro Achse einzeln —
        # sonst bekommt z.B. strafe eine künstliche Mindestbewegung, obwohl gerade
        # keine seitliche Ausweichung nötig ist
        totalMagnitude = math.hypot(self.speed, self.strafe)
        if 0 < totalMagnitude < MIN_SPEED:
            scale = MIN_SPEED / totalMagnitude
            self.speed  *= scale
            self.strafe *= scale

        self.rotationSpeed = 0.0

    # ("ge" and "tarxet" to prevent that the Model-to-JSON Part calls this function)
    def geDistanceToTarxet(self):
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
            #print("distance to small --> select other closest waypoint")
            closestWPIndex = sorted_indices[2]

        targetHeading1 = math.atan2(waypoints[closestWPIndex][1]-self.yPos, waypoints[closestWPIndex][0]-self.xPos)
        targetHeading2 = math.atan2(waypoints[secondClosestWPIndex][1]-self.yPos, waypoints[secondClosestWPIndex][0]-self.xPos)

        # return waypoint with smallest heading error
        if abs(self.geHeadingError(targetHeading1)) < abs(self.geHeadingError(targetHeading2)):
            return waypoints[closestWPIndex]
        else: 
            return waypoints[secondClosestWPIndex]


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
            #   print("Target setted " + str (xTarget) + " " + str(yTarget))

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