Yahboom Rosmaster m3pro Setup
============
Official documentation: https://www.yahboom.net/study/ROSMASTER-M3PRO

**Hardware Info:**
- pi@raspberrypi:~ $ cat /etc/os-release
```
    PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
    NAME="Debian GNU/Linux"
    VERSION_ID="12"
    VERSION="12 (bookworm)"
    VERSION_CODENAME=bookworm
    ID=debian
    HOME_URL="https://www.debian.org/"
    SUPPORT_URL="https://www.debian.org/support"
    BUG_REPORT_URL="https://bugs.debian.org/"
```
- pi@raspberrypi:~ $ cat /sys/firmware/devicetree/base/model
  
    ```Raspberry Pi 5 Model B Rev 1.1```

## 0. Quickstart Xbox handel control: 
- Plug in the Controller receiver in the USB-Hub board (underneath the RPI)
- start the robot, power on the controller
- wait until everything has been started up on the screen
- Press "start" on the Controller, press "R2" to unlock the controller (press R1 to close the gripper, otherwise it is getting hot) 
- start driving the robot:

![](https://md.inf.tu-dresden.de/notes/uploads/e7004db8-33df-46f0-bf02-797bf97b27e0.png)

## 1. Configure Network to connect to a new Hotspot:
- connect to the ROSMASTER Accespoint: PW = 12345678
- SSH to the RPI-board:
    - default IP = 192.168.8.88
    - username = pi
    - password = yahboom
- https://www.raspberrypi.com/documentation/computers/configuration.html
- ```nmcli dev wifi list```
- ```sudo nmcli --ask dev wifi connect <example_ssid> ```
- connect the robot to your own hotspot for simple integration
  
## 2. Initial tasks:
- ```sudo apt update``` (requries usually additional steps)
- ```sudo apt upgrade```
- ```sudo apt autoremove```
- ```docker container prune``` (removes unused docker containers to free space)
- delete unused docker images:
  - e.g. ```sudo docker image rm 192.168.2.51:5000/rosmaster-m3pro:1.0.X```

## Container Structure on the Yahboom
1. 
## 3.1 Enter Docker container: 
- (```sh start_agent.sh```) (usually already done by the AutoStart of the yahboom)
- ```bringup_m3pro``` (always composes a new docker container, with ```docker start rosmaster...``` you can go around that but sometimes rviz2 does not work anymore)
- ```exec_m3pro``` (sshs into the docker container)
- to hook persistent storage in the container: add new volumes in the docker compose file (~/M3Pro_ws/docker-compose.yml) 

## 3.2 Connect to Docker Container via VS-Code basically (not only via exec on the rpi)
- https://www.yahboom.net/study/ROSMASTER-M3PRO
- VS-Code
- '>'remote: Add remote connection (later, if host already exists: Connect to host)
- ``` ssh pi@<ip-address>```
- add address to user config
- press connect in the bottom right
- enter continue, enter password (yahboom)
- left corner must show the ip-address of the rpi
- install docker in this VS-Code instance
- open Docker tab in VS-code
- right click on the running docker container: "Attach VS-Code"
- enter the password for the container (yahboom)

## 3.3 Check whether ROS-topics exist:
- ```ros2 topic list``` should show around 10 topics including /cmd_vel, ...
- if not, restart the 

## 4. Connect to the Robots Display via VNC 

- https://uvnc.com/downloads/ultravnc/167-ultravnc-1-8-2-4.html
- Set new screen size: 
    - open: pi/.config/wayfire.ini (activate "show hidden" for that) set:
    -  [output:HDMI-A-1]
       mode = 1920x1080@60
- reconnect via VNC
- at each startup the VNC requires exactly two tries to connect because of the changed resolution

## 4. Change ROS-Domain ID
- modify ~/start_agent.sh by adding ``` -e ROS_DOMAIN_ID=42 ``` after ```--privileged```
- modify the ``` export ROS_DOMAIN_ID=30 ``` line in the rosmaster_m3Pro contianers ~/.bashrc


## 5. Control the robot driving (/cmd_vel)
- ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.1, y: -0.1, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 10

## 6. ROS Workspace Preparations for MultiSpectator
- add this line to "volumes" in ~/M3Pro_ws/docker-compose.yml :
     ``` /home/pi/Multispectator:/root/MultiSpectator``` 
    to have the repo persistent in the container
- rf2o_laser_odometry package must be installed from git:
    ```
    cd ~/yahboomcar_ws/src
    git clone -b ros2 https://github.com/MAPIRlab/rf2o_laser_odometry.git
    cd ~/yahboomcar_ws
    colcon build --packages-select rf2o_laser_odometry
    source install/setup.bash
    ```
- clone MultiSpectator Repository from Github and checkout branch "yahboom"
- create a python3 venv in the runtimemodel directory 
    - it uses python 3.10 and venv is not installed by default
    - before installing venv, run: ``` sudo apt-get update``` (takes a while)
    - then: ``` sudo apt install python3.10-venv ```
    - ``` python3 -m venv .```
    - ```source bin/activate```
    - ```pip install -r requirements.txt ```

## 7. Start MultiSpectator - SingleRobotController
- start combined laser pkg 
```ros2 launch yahboom_M3Pro_laser laser_driver.launch.py ```
- start rf2o 
```ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py ``` 
- in "/MultiSpectator/runtimemmodel" run ``` python3 main.py <robot_name> ```
- run mini-SEL.py on the Host PC for Target approach control 

## 8. Use Camera and Arm for AprilTag detection and following
- Predefined package works okay (Desktop tracking and gripping machine code):
    - run each command in a new terminal
    - ``` ros2 launch M3Pro_demo camera_arm_kin.launch.py ```
    - ``` ros2 run M3Pro_demo grasp_desktop ``` 
    - ``` ros2 run M3Pro_demo apriltag_track_desktop ``` 
    - robot follows Apriltag object - if it stays still, it beeps - afterwards, grasp mode can be triggered with "space" - to enter follow mode again press "m"
    - works also withouth the grasp_desktop node
    - If multiple Tags are visible, system tracks the one with the lowest ID
- Issues: 
    - Robot rotates sometimes more than 90 degrees and may crashs into the display !!!! very dangerous  !!!
    - Package must be improved in this direction 
- Robot should use arm rotation and chassis rotation together to enable very fast following
    - First Step: enable the following with limited arm by a seperate ROS-package
- Robot arm should osziallate if no April-Tag is there to increase the FOV (field of view) 
- Messages Component only wants to know the position of a perceived April-Tag (or multiple)
- Get Detection Topic filled with April-Tag data:
    - ros2 launch orbbec_camera dabai_dcw2.launch.py
    - ros2 launch m3pro_bringup record_tag.launch.py 
    - but Record_tag has to much thing in it

- Run April-Tag detection clean without additional stuff:
    - ```ros2 run apriltag_localization apriltag_node --ros-args \
  -r image_rect:=/camera/color/image_raw \
  -r camera_info:=/camera/color/camera_info ```
- Set all joints to a testable level (IMPORTANT: do not set all to 0!!!!)
    - ros2 topic pub /arm6_joints arm_msgs/msg/ArmJoints "{joint1: 90, joint2: 90, joint3: 90, joint4: 90, joint5: 90, joint6: 45, time: 3000}" --once
    - ATTENTION: joint 6 crunches with 90° !!!!!
    - time: 3000 for slwo movement to preserve
    - close to initial pose: 
``` ros2 topic pub /arm6_joints arm_msgs/msg/ArmJoints "{joint1: 90, joint2: 135, joint3: 45, joint4: 0, joint5: 90, joint6: 45, time: 3000}" --once ```

## Camera Controller startup:
- ```ros2 launch orbbec_camera dabai_dcw2.launch.py```
- ``` ros2 run apriltag_localization apriltag_node --ros-args -r image_rect:=/camera/color/image_raw -r camera_info:=/camera/color/camera_info ```
- 
- in /Multispectator/messages/ run ```python3 /utils/CameraArmController``` 

## Setup with Launch Script 
- multispectator.launch.py located in M3Pro_ws/src/m3pro_bringup/launch
- locate required config file in the config folder beside it

## Get SLAM running:
- load custom slam_params.yaml:
    - ros2 launch slam_toolbox online_async_launch.py \
      use_sim_time:=false \
      slam_params_file:=/root/M3Pro_ws/slam_params.yaml


## Idea with ARM/Camera Control:
- switch for User-mode controlled from the Dashboard and auto-mode 
- user mode --> specifiy goal or joystick input (has to consider camera limits and shoudl rotate the robot in this case!!!!)
- **seperate component for the camera control**
- auto mode: 
    - performs oscillating behavior, if no code is received
    - fixes and follows the code, if one is received
    - in Monitoring case: Robots theta must be set to SUT direction to ensure good view on the SUT 
    - ISSUE: fixed position monitoring: theta rotation as before; How to retain robot from focusing other tags instead of the fixed position, that has obviously no tag?
        - switch to manual user mode for that automatically  

## Problem:
- Camera stops rotating when the robot moves (Issue with the Message DDS??)
- solved: let the mape-k loop running slower

## Improve Positioning:
- use extended kalman filter (EKF) node and config in the launch file
- and imu-covariance fixer script --> uses the imu_raw_data from the robot
- use odom_raw, because it is more acurate on "teppich" than odom_rf2o (although frequencies were fixed) 
- Resart the micro-ros container everytime the robot restarts at its initial position --> clean odom values 
- drift after some circles too but it can perform some :+1: 

## Improve driving by velocity smoother
- **IMPORTANT: robot drives unsmooth only if the controller handle is active, otherwise it drives way faster and smooth!!!**
- use existing nav2_velocity_smoother
- adapt the publish and subscribe topics

## Todo: 
- try with rotation also from odom_raw 
- add "strafe" attribute to the metamodel for sideward movement
- uniform attraction and repulsion forces
- Idea: use depth camera for Obstacle avoidance as well

## Adjustemnts to Runtimemodel SRL for Paper Docu:
- add strafe attriute to metamodel and runtimemodel
- adapt calculate speeds function so that it no longer rotates but considers the sideward movement with the strafe
- adapt robot supervisor


## How to change the ROS_DOMAIN_ID?
- open ~/robot_config.py scroll to the end, uncomment lines with set ROS_DOMAIN_ID and insert new ID
- stop and remove all containers
- change the ID also in ~/M3Pro_ws/.bashrc
- reboot the robot
- ATTENTION: If you wanna change the namespace, the joystick willnot work anymore
- In the second rosmaster contianer version 1.0.3 you cannot change something and its unclear where the directory are that it mounts
- **Summary: you can change the namespace and the ID but lose the joystick control completely**
- The joystick teleop node can be found in yahboomcar_ws/src/yahboomcar_ctrl/yahboom_joy_M3Pro.py --> it has no option to generally change the namespace


## Smarobix Intructions:
- install VS code Remote explorer extension
- attach VS code to the container and simply drag the smarobix probe in the file editor
- execute it
- open vs code with the smarobix extension
    - export diagram as screenshot
    - export logs for them
    - upload .smaro file for them (C:\Users\adsc644c\AppData\Roaming\Code\User\globalStorage\smarobix.smarobix-insights\models)

## Troubleshooting
- if ros2 topic list returns not the initial topics: restart the two containers, micro-ros and rosmaster 1.0.3 
- if the SD-Card runs full: delete unused docker images:
    - sudo docker image rm 192.168.2.51:5000/rosmaster-m3pro:1.0.1
