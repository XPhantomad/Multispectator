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
        ANGLE_TOLERANCE = 0.1
        MAX_SPEED = 0.8         # forward
        MAX_STRAFE = 0.8        # sideways - oft niedriger als forward beim Mecanum
        MAX_SPEED_ROT = 2.0
        MIN_SPEED_ROT = 0.0
        MIN_SPEED = 0.0         # Mindest-Gesamtgeschwindigkeit, sobald Bewegung nötig ist
        GAIN = 1
        ANGLE_GAIN = 0.8

        distanceToTarget = self.geDistanceToTarxet()
        if distanceToTarget <= 1e-3:
            self.speed = 0.0
            self.strafe = 0.0
            self.rotationSpeed = 0.0
            return

        dx = xTarget - self.xPos
        dy = yTarget - self.yPos
        attraction = np.array([dx / distanceToTarget, dy / distanceToTarget])
        #print("attraction" + str(attraction))
        #print("repulsion" + str(repulsion))

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

        # ── Continuous heading control (decoupled from translation) ──
        # Rotation is commanded independently of speed/strafe; the Mecanum
        # base mixes them at the wheel level, so orienting toward the target
        # does not disturb the orbit motion.
        if desiredHeading is not None:
            headingError = self.geHeadingError(desiredHeading)   # normalized [-pi, pi]

            if abs(headingError) < ANGLE_TOLERANCE:
                self.rotationSpeed = 0.0                          # deadband: on target
            else:
                rot = ANGLE_GAIN * headingError
                # clamp magnitude and enforce a minimum so it actually turns
                sign = 1.0 if rot >= 0 else -1.0
                rot = sign * max(MIN_SPEED_ROT, min(MAX_SPEED_ROT, abs(rot)))
                self.rotationSpeed = rot
        else:
            self.rotationSpeed = 0.0

    # ("ge" and "tarxet" to prevent that the Model-to-JSON Part calls this function)
    def geDistanceToTarxet(self):
        return math.dist([self.xTarget, self.yTarget], [self.xPos, self.yPos])
         
    def geHeadingError(self, target):
        return (target - self.theta + math.pi) % (2 * math.pi) - math.pi

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

    def getMovementDirection(self):
        """
        Computes the actual world-frame direction the robot is translating in,
        combining forward and strafe speed in the robot's body frame and
        rotating it by the current heading (which is always pointed at the center).
        """
        # body-frame velocity: x = forward, y = strafe (positive = left, ROS convention)
        vx_body = self.forwardSpeed
        vy_body = self.strafeSpeed

        # if robot isn't moving, fall back to heading itself
        if abs(vx_body) < 1e-6 and abs(vy_body) < 1e-6:
            return self.heading

        # rotate body-frame velocity into world frame using current heading
        vx_world = vx_body * math.cos(self.heading) - vy_body * math.sin(self.heading)
        vy_world = vx_body * math.sin(self.heading) + vy_body * math.cos(self.heading)

        return math.atan2(vy_world, vx_world)

    def calculateNextWaypoint(self, radius, targetX, targetY):
        DIST_THRESHOLD = 0.1

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

        # --- NEW: actual movement direction from forward + strafe speed ---
        movementDirection = self.getMovementDirection()
        
        # return waypoint with smallest heading error compared with the actual movement direction 
        if abs(self.geHeadingError(targetHeading1, base=movementDirection)) < abs(self.geHeadingError(targetHeading2, base=movementDirection)):
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