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
PORT = 2000+int(number[0])*2+1  # Port to listen on (non-privileged ports are > 1023)
addrPort = (HOST,PORT)

#Message Types
msg_Joiner = "Joiner"
msg_robotWithLoad = "Robot with Load"
msg_prey = "Prey"
msg_Chainmember_Join = "Chainmember(Join)"
msg_Joiner_Loading = "Joiner with Loading State"
msg_nothing = "nothing"

# EXTRA:Flocking
msg_Leader = "Leader"
msg_Deputy = "Deputy"
msg_Follower = "Follower"
msg_GlobalLight = "GlobalLight"
msg_Stopper = "Stopper"

# run robotSupervisor-Node
rclpy.init(args=None)
robotSupervisor = RobotMessage(name)
threading.Thread(target=lambda: rclpy.spin(robotSupervisor)).start()

# Socket for Connection to Webapp
udpClientSocket= socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
udpClientSocket.connect(addrPort)

def getAngleDif(a,b):
    return math.pi - abs(abs(a - b) - math.pi); 

def getGlobalCoordinates(blobAngle, blobDistance, decimalPlace):
    angle = blobAngle + robotSupervisor.getTheta()
    yPos = math.sin(angle) * (blobDistance / 100)
    xPos = math.cos(angle) * (blobDistance / 100)
    xAbs = round(robotSupervisor.getxPos() + xPos, decimalPlace)
    yAbs = round(robotSupervisor.getyPos() + yPos, decimalPlace)
    return xAbs, yAbs

blobs_old = []
# ##### MAPE-Loop
while(True):
    #start = time.time()
    blobs = robotSupervisor.getBlobs()
    if blobs_old != [] and blobs == []: #send a last nothing message, before stop sending
        print("last message")
        udpClientSocket.send(str.encode(json.dumps([[msg_nothing, 0, 0]])+ "\n"))
    
    messageList = []
    if blobs != []:
        filteredBlobs= {}  # dict: color -> blob mit kleinster Distanz

        for blob in blobs:
            # Filter out blobs behind the robot
            if -1.3 < blob.angle < 1.3:
                # take the blob, if the color is not in the dict or if it is closer than the former blob with this color
                if blob.color not in filteredBlobs or blob.distance < filteredBlobs[blob.color].distance:
                    filteredBlobs[blob.color] = blob

        # interpret the sorted blobs to messages
        for color, blob in filteredBlobs.items():
            xAbs, yAbs = getGlobalCoordinates(blob.angle, blob.distance, 2)

            if color == "red":
                messageList.append([msg_prey, xAbs, yAbs])
            elif color == "yellow" and not any(msg[0] == msg_robotWithLoad for msg in messageList):
                messageList.append([msg_robotWithLoad, xAbs, yAbs])
            elif color == "magenta" and not any(msg[0] == msg_Chainmember_Join for msg in messageList):
                messageList.append([msg_Chainmember_Join, xAbs, yAbs])
            elif color == "white":
                messageList.append([msg_Joiner_Loading, xAbs, yAbs])
            elif color == "green":
                messageList.append([msg_Joiner, xAbs, yAbs])
            
            # EXTRA:Flocking
            elif color == "purple" and not any(msg[0] == msg_Leader for msg in messageList):
                messageList.append([msg_Leader, xAbs, yAbs])
            elif color == "cyan" and not any(msg[0] == msg_Deputy for msg in messageList):
                messageList.append([msg_Deputy, xAbs, yAbs])
            elif color == "orange" and not any(msg[0] == msg_Follower for msg in messageList):
                messageList.append([msg_Follower, xAbs, yAbs])
            elif color == "brown" and not any(msg[0] == msg_Stopper for msg in messageList):
                messageList.append([msg_Stopper, xAbs, yAbs])

    if messageList == []:                           
        messageList.append([msg_nothing, 0, 0])

    # EXTRA Flocking
    angle = robotSupervisor.getGlobalLightAngle() 
    dist = robotSupervisor.getGlobalLightDist()
    if angle != 0.0 and dist != 0.0:
        xAbs, yAbs = getGlobalCoordinates(angle, dist, 0) 
        messageList.append([msg_GlobalLight, xAbs, yAbs])

    udpClientSocket.send(str.encode(json.dumps(messageList)+ "\n"))  

    blobs_old = blobs
    
    # end = time.time()
    # with open("timeMSG.txt", "a", encoding="utf-8") as f:
    #     f.write("time:"+ str(end-start)+"\n")
    
    time.sleep(0.1)

robotSupervisor.destroy_node()
rclpy.shutdown()

