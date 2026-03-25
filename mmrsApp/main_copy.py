import json
import threading
import time
from modelUtils.robotSupervisor import *
import rclpy
import socket
from modelImpl.robotModelImpl import *

global addr, udpServerSocket, bufferSize
addr = None
start = False
bufferSize = 1024
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65431  # Port to listen on (non-privileged ports are > 1023)
addrPort = (HOST,PORT)
DIST_TOLERANCE = 0.1
DIST_LOADING = 0.3

# receives Messages from the Webapp, 
# if hello-Message is received the Initialisation Message is created and sent to the Webapp
# otherwise Goal is set
def receiveMessages():
    global start, addr, udpServerSocket    
    while(True): 
        msg, addr = udpServerSocket.recvfrom(bufferSize) # BLOCKS

        if(msg.decode() == "hello"):
            # send INIT
            # List for all Modellelements, that are not Model --> State, Area, Robot
            e = {}
            for a in [a for a in dir(model) if not a.startswith('__') and callable(getattr(model, a)) and "get" in a] :
                e[(a[3:])] = getattr(model, a)()
            #print(json.dumps(e)) # {"areas": ["A", "B", "C", "D", "E", "F"], "robots": ["robo1", "roboter2"], "states": ["waiting", "driving"]}
            udpServerSocket.sendto(str.encode(json.dumps(e)),addr)

        else:
            msg = json.loads(msg.decode())
            #print(msg)
            if(len(msg)>=2):
                model.implementation(msg["robot"],msg["xTarget"],msg["yTarget"], msg["state"], msg["led"])

# creates a Statusmessage in JSON from the Runtimemodel and sends it via Socket to the Webapp
# Message contains each Robot with its attributes
def publishMessages():
    global start, udpServerSocket, addr
    while True:
        if(addr != None):       
            # robot --> JSON  TODO: make this easier --> Outsource
            d = {}

            for robot in model.robots :
                # adds only attributes of robot to dict
                d[robot.getname()] = {}
                for a in [a for a in dir(robot) if not a.startswith('__') and callable(getattr(robot, a)) and "get" in a] :
                    # must call getters, bacause otherwise Area would not return name but only reference               
                    # appends attribute name from getter function name without get and attribute Value
                    d[robot.getname()][(a[3:])] = getattr(robot, a)()
            #print(json.dumps(d))
            udpServerSocket.sendto(str.encode(json.dumps(d)+ "\n"), addr)
            
        time.sleep(1) # depends on the performance of your PC

print("Staaaart")     


waiting = StateImpl(1, "waiting", 0.0, True)
driving = StateImpl(2, "driving", 1.0, False)
load = StateImpl(5, "load", 0.0, True, True, False)
unload = StateImpl(6, "unload", 0.0, True, False, True)

model = ModelImpl(None, [waiting, driving, load, unload])
robot1=RobotImpl(0.0, 0.0, 0.0,0.0, 0.0, "fb_0", 1,)
robot1.setstate(waiting)
model.addRobot(robot1)



# run robotSupervisor-Node
rclpy.init(args=None)

robotSupervisor = RobotSupervisor(robot1.getname())
threading.Thread(target=lambda: rclpy.spin(robotSupervisor)).start()

# Socket for Connection to Webapp
udpServerSocket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
udpServerSocket.bind(addrPort)

# Reveice from Webapp
threading.Thread(target=lambda: receiveMessages()).start()

#Publish to Webapp
threading.Thread(target=lambda: publishMessages()).start()


##### MAPE-Loop
while(True): 
    #Monitor
    robot1.setPos(robotSupervisor.getxPos(), robotSupervisor.getyPos(),robotSupervisor.getzPos(), robotSupervisor.getTheta())
    robot1.setLoad(robotSupervisor.getLoad())
    proximity = robotSupervisor.getProximity()

    #Analyse - makes the abstraction and checks if goal was Reached
    #model.abstraction(robot1.getid()) 
    if(robot1.geDistanceToTarge()>DIST_TOLERANCE):
        robot1.goalReached = False
    else:
        robot1.goalReached = True
    
    # trigger load/release, when other robot is very near and goal is nearly reached or state is waiting
    # TODO: Move to model.abstraction
    if((robot1.geDistanceToTarge()<= DIST_LOADING or robot1.state == waiting) and proximity == True and robot1.state != load and robot1.state!=unload):
        if(robot1.load):
            robot1.setstate(unload)
        else:
            robot1.setstate(load)
        print("-----------------something changed--------------")
    
    # Plan - calculates and sets speeds for the robot
    if(not robot1.getgoalReached()):
        robot1.calculateSpeeds(robotSupervisor.getv_repulsion())
    
    # if goal reached
    elif(robot1.speed != 0.0 or robot1.rotationSpeed != 0.0):
        robot1.speed = robot1.rotationSpeed = 0.0
        robot1.goalReached = False #required to send last velocity command with 0 and 0 to stop the robot    

    grip = robot1.state.getgrip()
    release = robot1.state.getrelease()

    #Execute - send speeds to robotSupervisor to publish them to ROS
    if(not robot1.getgoalReached()):
        #print(f'goal: {robot1.getgoalReached()} publish velocity({robot1.speed},{robot1.rotationSpeed})')
        robotSupervisor.publishVelocity(robot1.speed,robot1.rotationSpeed)
    robotSupervisor.publishLight(robot1.ledColor) # TODO: with condition, publish only when changed
    robotSupervisor.publishGripper(grip, release)

robotSupervisor.destroy_node()
rclpy.shutdown()

