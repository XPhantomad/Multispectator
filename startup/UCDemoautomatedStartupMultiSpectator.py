import os
import subprocess
import sys
import threading
import time


colors = ["red", "yellow", "orange", "green", "white", "blue", "magenta", "brown"]

print(os.getcwd())

# Inititalize SUTs
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT1", colors[1]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT2", colors[2]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT3", colors[3]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT4", colors[0]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT5a", colors[6]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT5b", colors[6]])).start()
threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "R_SUT5c", colors[6]])).start()


#threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializerInteresting.sh", "SUT"+ str(i), colors[i]])).start()
time.sleep(0.1)


# start webapp 
threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/webapp/swarmDisplay.py"])).start()

# start Multispectator App 
time.sleep(4)
threading.Thread(target=lambda: subprocess.run(["julia", os.getcwd() + "/Contexts/MultiSpectator/multispectator.jl"])).start()
time.sleep(7)

# start Robots
for i in range(8):
    robotName = "R"+str(i)
    print("start " + robotName)
    
    # start Single Robot Loop 
    threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/runtimemodel/main.py", robotName])).start()
    time.sleep(1)
    # start Messages Component
    threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/messages/main.py", robotName])).start()
    time.sleep(1)
        