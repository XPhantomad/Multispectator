#!/bin/bash

cd ros_ws && source install/setup.bash && argos3 -c monitoringEnvironment.argos & export PATH=/home/repo/julia-1.10.10/bin:$PATH && cd Multispectator && source ../ros_ws/install/setup.bash && source startup/bin/activate && python3 startup/automatedStartupMultiSpectator.py
