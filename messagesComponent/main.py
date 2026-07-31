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

def getDistance(x1,x2, y1,y2):
        return math.sqrt(pow(x2 - x1,2)+pow(y2-y1,2))
     
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
    
    messageList = []
    if blobs != []:
        filteredBlobs= {}  # dict: color -> blob mit kleinster Distanz
        for blob in blobs:
            # see, if light was already there and if 
            xAbs, yAbs = getGlobalCoordinates(blob.angle, blob.distance)
            if blob.color in filteredBlobs: 
                xPrev = filteredBlobs[blob.color][1]
                yPrev = filteredBlobs[blob.color][2]
                # check additionally that distance between the blobs is small enough to safely assign it all to one robot 
                #print(getDistance(xAbs, xPrev, yAbs, yPrev))
                if getDistance(xAbs, xPrev, yAbs, yPrev) <= 0.3:  # 10 is roughly the radius of the robot in arogos units
                    #print("intersting perceived")
                    filteredBlobs[blob.color] = (blob, xAbs, yAbs, True)
                # if light blobs are to far from each other, a MRSUT is detected and only the closest robot has to be taken into consideration
                elif blob.distance <= filteredBlobs[blob.color][0].distance:
                    #print("set new MRS member")
                    filteredBlobs[blob.color] = (blob, xAbs, yAbs, False)

            elif blob.distance <= LIGHT_RANGE:
                filteredBlobs[blob.color] = (blob, xAbs, yAbs, False)
         
        # interpret the sorted blobs to messages
        for color, blob in filteredBlobs.items():
            messageList.append({"color":color, "xPos": blob[1], "yPos": blob[2], "interesting": blob[3]})

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

