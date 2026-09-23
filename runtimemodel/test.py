import math

# required for the strafe behavior --> noraml theta cannot be used anymore
def geMovementDirection():

    # body-frame velocity: x = forward, y = strafe (positive = left, ROS convention)
    vx_body = 1.5
    vy_body = -1

    # if robot isn't moving, fall back to heading itself
    if abs(vx_body) < 1e-6 and abs(vy_body) < 1e-6:
        return 0

    # rotate body-frame velocity into world frame using current heading
    vx_world = vx_body * math.cos(0) - vy_body * math.sin(0)
    vy_world = vx_body * math.sin(0) + vy_body * math.cos(0)

    return math.atan2(vy_world, vx_world)


print(geMovementDirection())
