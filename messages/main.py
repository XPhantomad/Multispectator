import json
import threading
import time
import re
from utils.robotSupervisor import *
import rclpy
import socket
import sys


name = sys.argv[1]
number = re.findall(r'\d+', name)

global addr, udpClientSocket, bufferSize
start = False
addr = None
bufferSize = 1024
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 3005 # Port to listen on (non-privileged ports are > 1023)
addrPort = (HOST,PORT)

LIGHT_RANGE = 74 # range of the LED of the center of the robot (distance in which a robot is clearly identifiable (interesting/uninteresting))

# run robotSupervisor-Node
rclpy.init(args=None)
robotSupervisor = RobotMessage(name)
threading.Thread(target=lambda: rclpy.spin(robotSupervisor)).start()

# Socket for Connection to Webapp
udpClientSocket= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
udpClientSocket.connect(addrPort)
#udpClientSocket.send(str.encode("start"))

def getAngleDif(a,b):
    return math.pi - abs(abs(a - b) - math.pi); 

def getGlobalCoordinates(blobAngle, blobDistance):
    angle = blobAngle + robotSupervisor.getTheta()
    yPos = math.sin(angle) * (blobDistance / 100)
    xPos = math.cos(angle) * (blobDistance / 100)
    xAbs = round(robotSupervisor.getxPos() + xPos, 2)
    yAbs = round(robotSupervisor.getyPos() + yPos, 2)
    return xAbs, yAbs

blobs_old = []
messagesList_old = []

###### MAPE-Loop
while(True):
    #start = time.time()
    blobs = robotSupervisor.getBlobs()
    if blobs_old != [] and blobs == []: #send a last nothing message, before stop sending
        print("last message")
        #udpClientSocket.send(str.encode(json.dumps([[msg_nothing, 0, 0]])+ "\n"))
    
    messageList = []
    if blobs != []:
        filteredBlobs= {}  # dict: color -> blob mit kleinster Distanz
        for blob in blobs:
            # detect robots with more than 1 light on as INTERESTING robots
            if blob.color in filteredBlobs: 
                filteredBlobs[blob.color] = (blob, True)
            elif blob.distance <= LIGHT_RANGE:
                filteredBlobs[blob.color] = (blob, False)
         
        # interpret the sorted blobs to messages
        for color, blob in filteredBlobs.items():
            xAbs, yAbs = getGlobalCoordinates(blob[0].angle, blob[0].distance)
            messageList.append({"color":color, "xPos": xAbs, "yPos": yAbs, "interesting": blob[1]})

        if messageList and messageList != messagesList_old:                          
            msg = {"observation" : messageList}
            udpClientSocket.send(str.encode(json.dumps(msg)+ "\n")) 
    blobs_old = blobs
    messagesList_old = messageList
    
    # end = time.time()
    # with open("timeMSG.txt", "a", encoding="utf-8") as f:
    #     f.write("time:"+ str(end-start)+"\n")
    
    time.sleep(0.5)

robotSupervisor.destroy_node()
rclpy.shutdown()

