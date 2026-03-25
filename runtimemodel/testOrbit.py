import math
import numpy as np



def geHeadingError(current, target):
    return (target - current + math.pi) % (2 * math.pi) - math.pi

DIST_TH = 0.2

xTarget = 2
yTarget = 0
radius = 1

xPos = 1.8
yPos = 0.9
theta = 2.5

# Waypoint Array
waypoints = []
for i in range(8):
    x = xTarget + math.cos((math.pi/4)*i)*radius
    y = yTarget + math.sin((math.pi/4)*i)*radius
    waypoints.append([x,y])

print(waypoints)


# get the two closest waypoints
sorted_indices = sorted(range(len(waypoints)), key=lambda i: math.dist(waypoints[i], [xPos, yPos]))
closestWPIndex = sorted_indices[0]
secondClosestWPIndex = sorted_indices[1]

# if robot is too close, choose the next waypoints --> avoids, that the robot stucks at one waypoint
if (math.dist(waypoints[closestWPIndex], [xPos,yPos])) < DIST_TH:
    closestWPIndex = sorted_indices[2]

print(closestWPIndex)
print(secondClosestWPIndex)

targetHeading1 = math.atan2(waypoints[closestWPIndex][0]-xPos, waypoints[closestWPIndex][1]-yPos)
targetHeading2 = math.atan2(waypoints[secondClosestWPIndex][0]-xPos, waypoints[secondClosestWPIndex][1]-yPos)

# take waypoint with smallest heading error
if abs(geHeadingError(theta,targetHeading1)) < abs(geHeadingError(theta,targetHeading2)):
    print(closestWPIndex)
else:
    print(secondClosestWPIndex)

print("works?")


# check robots direction: if diff(theta, targetHeading) > 90° then choose next waypoint


robotVector = np.array([1, 1])
targetVector = np.array([2, 2])

distanceVector = targetVector-robotVector
print(distanceVector)
targetHeading = math.atan2(distanceVector[0], distanceVector[1])
print(targetHeading)
targetHeading = targetHeading+(math.pi/2)
print(targetHeading)


