import json
import threading
import time
import re
from utils.ugv_robot_message import *
import rclpy
import socket
import sys


name = sys.argv[1]
number = re.findall(r'\d+', name)

global addr, udpClientSocket, bufferSize
start = False
addr = None
bufferSize = 1024
HOST = "192.168.137.201"  # Standard loopback interface address (localhost)
PORT = 3005 # Port to listen on (non-privileged ports are > 1023)
addrPort = (HOST,PORT)

LIGHT_RANGE = 74 # range of the LED of the center of the robot (distance in which a robot is clearly identifiable (interesting/uninteresting))

TAG_COLOR_MAP = {
    10:  "red",
    2:  "blue",
    3:  "green",
    46:  "yellow",
    4:  "magenta",
    5:  "cyan",
    6:  "orange",
    7:  "white",
    8:  "purple",
    9:  "pink",
}

DEFAULT_COLOR = "pink"  # fallback if tag ID is not in map



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
       for blob in blobs:
          xAbs = round(robotSupervisor.getxPos() + blob["x"], 2)
          yAbs = round(robotSupervisor.getyPos() + blob["z"], 2)
          # translate tag_ids to colors by hand
          messageList.append({"color":TAG_COLOR_MAP.get(int(blob["tag_id"]), DEFAULT_COLOR), "xPos": xAbs, "yPos": yAbs, "interesting": False})

       if messageList and messageList != messagesList_old:                          
          msg = {"observation" : messageList}
          print(msg)
          print(json.dumps(msg)+ "\n")
          udpClientSocket.send(str.encode(json.dumps(msg)+ "\n")) 
    blobs_old = blobs
    messagesList_old = messageList
    
    # end = time.time()
    # with open("timeMSG.txt", "a", encoding="utf-8") as f:
    #     f.write("time:"+ str(end-start)+"\n")
    
    time.sleep(0.5)

robotSupervisor.destroy_node()
rclpy.shutdown()

