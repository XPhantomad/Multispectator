import os
import subprocess
import sys
import threading
import time


colors = ["red", "yellow", "orange", "green", "white", "blue", "magenta", "brown"]

print(os.getcwd())

# Inititalize SUTs
for i in range(4):
    print(colors[i])
    if i%2 == 0:
        threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "SUT"+ str(i), colors[i]])).start()
    else:
        threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializerInteresting.sh", "SUT"+ str(i), colors[i]])).start()
    time.sleep(0.1)


# start webapp 
threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/webapp/swarmDisplay.py"])).start()

# start Multispectator App 
time.sleep(4)
threading.Thread(target=lambda: subprocess.run(["julia", os.getcwd() + "/Contexts/MultiSpectator/multispectator.jl"])).start()
time.sleep(7)

# start Robots
for i in range(4):
    robotName = "fb_"+str(i)
    print("start " + robotName)
    
    # start Single Robot Loop 
    threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/runtimemodel/main.py", robotName])).start()
    time.sleep(1)
    # start Messages Component
    threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/messages/main.py", robotName])).start()
    time.sleep(1)
        