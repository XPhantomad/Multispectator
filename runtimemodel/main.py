import json
import threading
import time
from modelUtils.ugv_supervisor import *
import rclpy
import socket
from modelImpl.robotModelImpl import *
import re
import sys
import signal

# cli arguments for robot name
name = sys.argv[1]
number = re.findall(r'\d+', name)   

global addr, udpClientSocket, bufferSize
addr = None
start = False
bufferSize = 1024
HOST = "192.168.137.201"  
PORT = 3004
HOST_TRACKER = "192.168.0.100"  
PORT_TRACKER = 5006 
addrPort = (HOST, PORT)
addrPort_tracker = (HOST_TRACKER, PORT_TRACKER)
DIST_TOLERANCE = 0.2

# Shutdown event – shared across all threads
shutdown_event = threading.Event()

def receiveMessages():
    global start, udpClientSocket    
    while not shutdown_event.is_set(): 
        try:
            msg = udpClientSocket.recv(bufferSize)
            if not msg:
                break
            if msg.decode() == "start":
                start = True
            else:
                msg = json.loads(msg.decode().splitlines()[0])
                if len(msg) >= 2:
                    model.implementation(msg["xTarget"], msg["yTarget"], msg["state"])
        except Exception:
            break  # socket closed or error – exit thread cleanly

def publishMessages():
    global udpClientSocket
    while not shutdown_event.is_set():
        if udpClientSocket:
            try:
                d = {"robot": {}}
                robot = model.robots
                for a in [a for a in dir(robot) if not a.startswith('__') and callable(getattr(robot, a)) and "get" in a]:
                    d["robot"][(a[3:])] = getattr(robot, a)()
                udpClientSocket.send(str.encode(json.dumps(d) + "\n"))
            except Exception:
                break
        time.sleep(0.5)

def publishMessages_toTracker():
    global udpClientSocket_tracker
    while not shutdown_event.is_set():
        if udpClientSocket_tracker:
            try:
                d = {"robot": {}}
                robot = model.robots
                for a in [a for a in dir(robot) if not a.startswith('__') and callable(getattr(robot, a)) and "get" in a]:
                    d["robot"][(a[3:])] = getattr(robot, a)()
                print(d)
                udpClientSocket_tracker.send(str.encode(json.dumps(d) + "\n"))
            except Exception:
                break
        time.sleep(0.5)


print("Staaaart")     

exploration = StateImpl(1, "exploration", 1.0)
driving     = StateImpl(2, "driving",     1.0)
waiting     = StateImpl(3, "waiting",     0.0)
monitoring  = StateImpl(3, "monitoring",  1.0, 0.8)  

model = ModelImpl(None, [waiting, driving, waiting, monitoring], [])
robot1 = RobotImpl(0.0, 0.0, 0.0, 0.0, 0.0, name, 1)
robot1.setstate(driving)
model.addRobot(robot1)

# Initialize ROS2
rclpy.init(args=None)
robotSupervisor = UGVSupervisor(robot1.getname())
threading.Thread(target=lambda: rclpy.spin(robotSupervisor), daemon=True).start()

# Sockets
udpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
udpClientSocket.connect(addrPort)

udpClientSocket_tracker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
udpClientSocket_tracker.connect(addrPort_tracker)

# Start threads as daemon=True so they die automatically when main thread exits
threading.Thread(target=receiveMessages,          daemon=True).start()
threading.Thread(target=publishMessages,          daemon=True).start()
threading.Thread(target=publishMessages_toTracker, daemon=True).start()




def shutdown(signum=None, frame=None):
    global robotSupervisor 
    """Called on SIGINT (Ctrl+C) or SIGTERM – always runs in main thread."""
    print("Shutting down...")
    shutdown_event.set()
    robotSupervisor.publishVelocity(0.0, 0.0) 

# Register signal handlers in main thread – reliable across all platforms
signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)



# ── MAPE loop ─────────────────────────────────────────────────────────────────
while not shutdown_event.is_set():
    # Monitor
    robot1.setPos(robotSupervisor.getxPos(), robotSupervisor.getyPos(),
                  robotSupervisor.getzPos(), robotSupervisor.getTheta())
    repulsion = robotSupervisor.getv_repulsion()

    # Analyse
    if robot1.geDistanceToTarxet() > DIST_TOLERANCE:
        robot1.goalReached = False
    elif robot1.state != monitoring:
        robot1.goalReached = True

    xTarget = robot1.getxTarget()
    yTarget = robot1.getyTarget()

    if robot1.state == monitoring:
        nextWaypoint = robot1.calculateNextWaypoint(
            robot1.state.getradius(), robot1.getxTarget(), robot1.getyTarget()
        )
        xTarget = nextWaypoint[0]
        yTarget = nextWaypoint[1]

    # Plan
    if not robot1.getgoalReached() and (robot1.state == driving or robot1.state == monitoring):
        robot1.calculateSpeeds(repulsion, xTarget, yTarget)
    elif robot1.speed != 0.0 or robot1.rotationSpeed != 0.0:
        robot1.speed = robot1.rotationSpeed = 0.0
        robot1.goalReached = False

    # Execute
    if not robot1.getgoalReached():
        robotSupervisor.publishVelocity(robot1.speed, robot1.rotationSpeed)

    time.sleep(0.1)

# ── Cleanup – always reached when shutdown_event is set ───────────────────────
robotSupervisor.publishVelocity(0.0, 0.0)  # stop motors
time.sleep(0.2)
robotSupervisor.destroy_node()
rclpy.shutdown()
udpClientSocket.close()
udpClientSocket_tracker.close()
print("Shutdown complete.")