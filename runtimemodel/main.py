import json
import threading
import time
from modelUtils.ugv_supervisor import *
import rclpy
import socket
from modelImpl.robotModelImpl import *
import re
import sys

# cli arguments for robot name
name = sys.argv[1]
number = re.findall(r'\d+', name)   

global addr, udpClientSocket, bufferSize
addr = None
start = False
bufferSize = 1024
HOST = "192.168.137.201"  
PORT = 3004 
addrPort = (HOST,PORT)
DIST_TOLERANCE = 0.2  # Distance tolerance for defining the goal as reached 

# receives Messages from the Swarm Element Loop
def receiveMessages():
    global start, addr, udpClientSocket    
    while(True): 
        msg = udpClientSocket.recv(bufferSize) # BLOCKS
        if(msg.decode() == "start"):
            start = True
        else:
            #print(msg)
            msg = json.loads(msg.decode().splitlines()[0])
            if(len(msg)>=2):
                model.implementation(msg["xTarget"],msg["yTarget"], msg["state"])

# creates a Status message in JSON of the runtime model and sent it via Socket to the Swarm Element Loop
# runs with 10Hz to meet the frequency of the initial checks of the SEL
def publishMessages():
    global start, udpClientSocket, addr
    while True:
        if(udpClientSocket):       # The sending of messages only starts when the start message has been received.
            d = {}
            robot = model.robots
            # adds only attributes of robot to dict
            d["robot"] = {}
            for a in [a for a in dir(robot) if not a.startswith('__') and callable(getattr(robot, a)) and "get" in a] :
                # must call getters, bacause otherwise Area would not return name but only reference               
                # appends attribute name from getter function name without get and attribute Value
                d["robot"][(a[3:])] = getattr(robot, a)()
            #print(robot.getload())
            udpClientSocket.send(str.encode(json.dumps(d)+ "\n"))
            
        time.sleep(0.5) # depends on the performance of your PC

print("Staaaart")     

exploration = StateImpl(1, "exploration", 1.0)
driving = StateImpl(2, "driving", 1.0)
waiting = StateImpl(3, "waiting", 0.0)
monitoring = StateImpl(3, "monitoring", 1.0, 0.8)  

model = ModelImpl(None, [waiting, driving, waiting, monitoring], [])
robot1=RobotImpl(0.0, 0.0, 0.0,0.0, 0.0, name, 1)
robot1.setstate(driving)
model.addRobot(robot1)


# run robotSupervisor-Node
rclpy.init(args=None)

robotSupervisor = UGVSupervisor(robot1.getname())
threading.Thread(target=lambda: rclpy.spin(robotSupervisor)).start()

# Socket for Connection to SEL
udpClientSocket= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
udpClientSocket.connect(addrPort)

# Reveice from SEL
threading.Thread(target=lambda: receiveMessages()).start()

#Publish to SEL
threading.Thread(target=lambda: publishMessages()).start()

counter = 0
##### MAPE-Loop
while(True): 

    #Monitor
    robot1.setPos(robotSupervisor.getxPos(), robotSupervisor.getyPos(),robotSupervisor.getzPos(), robotSupervisor.getTheta())
    repulsion = robotSupervisor.getv_repulsion()
    #if (counter % 10000 == 0):
    #  print(repulsion)
    
    #counter+=1

    #Analyse - makes the abstraction and checks if goal is reached
    # GoalReached is only interesting if robot makes target approximation
    if robot1.geDistanceToTarxet()>DIST_TOLERANCE:
        robot1.goalReached = False
    elif robot1.state != monitoring:
        robot1.goalReached = True


    # initially set target position to robots attribute
    xTarget = robot1.getxTarget()
    yTarget = robot1.getyTarget()

    # MONITORING: if state is monitoring, set target position to individually calculated position
    if robot1.state == monitoring:
        nextWaypoint = robot1.calculateNextWaypoint(robot1.state.getradius(),robot1.getxTarget(), robot1.getyTarget())
        #print("moinitoring")
        xTarget = nextWaypoint[0]
        yTarget = nextWaypoint[1]

    # Plan - calculates and sets speeds for the robot
    if(not robot1.getgoalReached() and (robot1.state == driving or robot1.state == monitoring)):
        robot1.calculateSpeeds(repulsion, xTarget, yTarget)

    # if goal reached or state != driving
    elif(robot1.speed != 0.0 or robot1.rotationSpeed != 0.0):
        robot1.speed = robot1.rotationSpeed = 0.0
        robot1.goalReached = False #required to send last velocity command with 0 and 0 to stop the robot    

    #if (counter % 10000 == 0):
     # print(f"Pos: ({robot1.xPos:.2f}, {robot1.yPos:.2f}) "
      #  f"Ziel: ({robot1.xTarget:.2f}, {robot1.yTarget:.2f}) "
       # f"Dist: {robot1.geDistanceToTarxet():.3f} "
        #f"Theta: {robotSupervisor.getTheta():.3f}")
    
    #counter+=1
    
    #Execute - send speeds to robotSupervisor to publish them to ROS
    if(not robot1.getgoalReached()):
        robotSupervisor.publishVelocity(robot1.speed,robot1.rotationSpeed)
    time.sleep(0.1)

robotSupervisor.destroy_node()
rclpy.shutdown()

