#!/bin/bash

source ~/ros_ws/install/setup.bash
ros2 topic pub --once /$1/cmd_led argos3_ros2_bridge/msg/Led "{color: "$2", mode: "ALL", index: 0}"
