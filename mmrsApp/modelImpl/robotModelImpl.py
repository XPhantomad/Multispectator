import math

import numpy as np
from model.monMRSmodel import *

class RobotImpl(Robot):    
    def __init__(self, xPos=0.0, yPos=0.0, name="robo", ip=2000):
        super().__init__(xPos, yPos, name,None, ip)
    
    def setPos(self, x, y):
        self.xPos =x
        self.yPos =y

    def setName(self, name):
        self.name = name

    def setPort(self, port):
        self.port = port


class PerceivedRobotImpl(Robot):    
    def __init__(self, xPos=0.0, yPos=0.0, name="perc", objectGripped=None):
        super().__init__(xPos, yPos, name, objectGripped)
    
    def setPos(self, x, y):
        self.xPos =x
        self.yPos =y

class ModelImpl(Model):

    def __init__(self, robot=None, object=None, perceivedrobot=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))
        super().__init__(robot, object, perceivedrobot)

    def addRobot(self, robot):
        self.robot.append(robot)

    def removeRobot(self, robot):
        self.robot.remove(robot)

    def getRobot(self, name):
        for r in self.robot:
            if r.name == name:
                return r
        return None

    
    # takes data from goal-message and implement them to a specific goal for the runtimemodel
    def implementation(self, xTarget, yTarget, stateName, messageName):
        robot = self.robot
        if(robot != None): 
            robot.xTarget = float(xTarget)
            robot.yTarget = float(yTarget)
            print("Target setted " + str (xTarget) + " " + str(yTarget))
            for state in self.states:
                if(state.getname() == stateName):
                    robot.state = state
                    print("State setted " + state.getname())
            for message in self.messages:
                if (message.getname() == messageName):
                    robot.message = message
                    print("LED setted " + message.getledColor())
        return False

    def update(self, port, receivedData):
        # if receivedData.prefix == "observation":
        #     # handle input from observation 
        #     for entry in receivedData:
        #         self.addPerceivedRobot(entry.name, entry.x , entry.y)

        # handle inputs from monitoring robots 
        msg_type, msg = next(iter(receivedData.items()))
        #print(msg_type)
        #print(msg)
        if (msg_type == "robot"):
            robot = self.getRobot(msg["name"])
            # robot already modelled --> update
            if (robot != None):
                robot.setPos(msg["xPos"], msg["yPos"])
                robot.setPort(port)
            # robot not found in the model --> create
            else:
                self.addRobot(RobotImpl(msg["xPos"], msg["yPos"], msg["name"], port))

        if (msg_type == "observation"):
            # TODO: process message list and add/update perceived SUTs/Objects
            pass

        # for name, params in receivedData.items():
        #     for robot in self.robot:
        #         if robot.getip() == port:
        #             robot.setName(params.get("name", robot.getName()))
        #             robot.setPos(params.get("xPos", robot.getxPos()), params.get("yPos", robot.getyPos()))
        #             return
                   
    
class ObjectImpl(Object):
    def __init__(self, xPos=0.0, yPos=0.0, name="obj"):
        super().__init__(xPos, yPos, name)
