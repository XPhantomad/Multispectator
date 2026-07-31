## Systemtest - Plotting 

### Systemtest
This folder contains a ROS2-Node and a python Selenium application to measure the Model Fidelity of the MultiSpectator. The Model Fidelity is the time from starting an action in the web dashboard (e.g. setting a new monitoring target) till the robot starts its movement in the required direction. 

- ```testROSNode.py``` supervises the angle value of the cmd_vel topic (because robot has most likely to rotate before driving in the new tareget direction)
- ```testGoalAdaption.py``` starts the MultiSpectator Simulation
    - define number of monitoring robots (increase the number in the .argos file too!!!)
    - define number of Monitoring Teams and the team size
    - fixed-position inspection is used for the time measurement (Position are on the diagonal axis through the arena - see picture)

![a](frame_0000004406.png)
Systemtest with 80 robots, 10 Monitoring teams with 8 constituents in each.

### Plotting

- ```timePlotToolScalability.py``` provides a simple matplotlip implementation to:
    - visualize the measurements in a boxplot and
    - output the median and average Model Fidelity times in the shell