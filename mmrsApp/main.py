import json
import selectors
import threading
import time
import rclpy
import socket
from modelImpl.robotModelImpl import *
import re
import sys
from threading import Lock
import types


sel = selectors.DefaultSelector()

thread = None
thread_lock = Lock()

# global HOST, PORT, bufferSize 
HOST = "127.0.0.1"  
PORT = 3004
BUFFER_SIZE = 1024

global lsock
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse port immediately
lsock.bind((HOST,PORT))
lsock.listen()
print(f"Listening on {(HOST,PORT)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# Stop flag for background thread
stop_thread = False

# Code from: https://realpython.com/python-sockets/#frequently-asked-questions
def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

    # add new Robot to the model:
    print(f"Add Robot to Model {addr[1]}")
    newRobot=RobotImpl(0.0, 0.0, f"robot {addr[1]}" , addr[1])
    model.addRobot(newRobot)

    


# Code from: https://realpython.com/python-sockets/#frequently-asked-questions
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(BUFFER_SIZE)  # Should be ready to read
        if recv_data:
            # update received data immediately in the model
            port = data.addr[1]
            msg = json.loads(recv_data)
            # TODO: update only if necessary??
            #print(msg)
            model.update(port, msg)

        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    
    # if mask & selectors.EVENT_WRITE:
    #     if data.outb:
    #         print(f"Echoing {data.outb!r} to {data.addr}")
    #         sent = sock.send(data.outb)

"""
Background Thread
"""
#receive System status information from swarm-element-loop
def background_thread():
    while not stop_thread:
        # Code from: https://realpython.com/python-sockets/#frequently-asked-questions
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)


########################
#
#   Connection to the WebApp
#
###################################


# global addr, udpClientSocket, bufferSize
# addr = None
# start = False
# bufferSize = 1024
# HOST = "127.0.0.1"  
# PORT = 4444 # Port to listen on (non-privileged ports are > 1023)
# addrPort = (HOST,PORT)

# DIST_TOLERANCE = 0.15  # Distance tolerance for defining the goal as reached
# DIST_LOADING = 0.3  

# # receives Messages from WebApp
# def receiveMessages():
#     global start, addr, udpClientSocket    
#     while(True): 
#         msg = udpClientSocket.recv(bufferSize) # BLOCKS
#         if(msg.decode() == "start"):
#             start = True
#         else:
#             msg = json.loads(msg.decode())
#             #print(msg)
#             if(len(msg)>=2):
#                 model.implementation(msg["xTarget"],msg["yTarget"], msg["state"], msg["message"])

# # creates a Status message in JSON of the runtime model and sent it via Socket to the Swarm Element Loop
# # runs with 10Hz to meet the frequency of the initial checks of the SEL
# def publishMessages():
#     global start, udpClientSocket, addr
#     while True:
#         if(udpClientSocket and start):       # The sending of messages only starts when the start message has been received.
#             d = {}
#             robot = model.robots
#             # adds only attributes of robot to dict
#             d[model.robots.getname()] = {}
#             for a in [a for a in dir(robot) if not a.startswith('__') and callable(getattr(robot, a)) and "get" in a] :
#                 # must call getters, bacause otherwise Area would not return name but only reference               
#                 # appends attribute name from getter function name without get and attribute Value
#                 d[robot.getname()][(a[3:])] = getattr(robot, a)()
#             #print(robot.getload())
#             udpClientSocket.send(str.encode(json.dumps(d)+ "\n"))
            
#         time.sleep(0.1) # depends on the performance of your PC


def sendMessage(port, msg):
    events = sel.select(timeout=None)
    for robot in model.robot:
        for key, mask in events:
            if not key.data is None:
                if key.data.addr[1] == port:
                    sock = key.fileobj
                    print("test")
                    print(msg)
                    sent = sock.send(str.encode(msg))
                    #print(sent)

print("Staaaart")     



model = ModelImpl(None, None, None)
robot1=RobotImpl(0.0, 0.0, "robot1", 2000)
model.addRobot(robot1)


# Connection to SRL
threading.Thread(target=lambda: background_thread()).start()

##### MAPE-Loop
while(True): 
    goal = json.dumps({
        "xTarget": 0.0,
        "yTarget": 0.0,
        "state": "monitoring",
        "SUTxPos": 2,
        "SUTyPos": 2
    })
    if model.getRobot("fb_1") != None:
        sendMessage(model.getRobot("fb_1").getip(), goal)
    time.sleep(3)
