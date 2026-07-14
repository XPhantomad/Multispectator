import os
import subprocess
import sys
import threading
import time
import unittest
import rclpy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager



from testROSNode import TestROSSupervisor

colors = ["red", "yellow", "orange", "green", "white", "blue", "magenta", "brown"]
robotCount = 12
teams = 4
monitoringTeamSize = 3

class testGoalAdaption(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print(os.getcwd())

        # setup is done in automated startup
        # threading.Thread(target=lambda: subprocess.run(["ros2", "launch", "webots_ros2_turtlebot", "robot_launch.py"])).start()
        # time.sleep(5)
        # threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/runtimemodel/main.py"])).start()
        # threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/webapp/mobileRTM.py"])).start()
        # time.sleep(3) 

        
        # Inititalize SUTs
        for i in range(8):
            print(colors[i])
            threading.Thread(target=lambda: subprocess.run([os.getcwd() + "/SUT-initializer.sh", "SUT"+ str(i), colors[i]])).start()
            time.sleep(0.1)


        # start webapp 
        threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/webapp/swarmDisplay.py"])).start()

        # start Multispectator App 
        time.sleep(4)
        threading.Thread(target=lambda: subprocess.run(["julia", os.getcwd() + "/Contexts/MultiSpectator/multispectator.jl"])).start()
        time.sleep(7)

        # start Robots
        for i in range(robotCount):
            robotName = "fb_"+str(i)
            print("start " + robotName)
            
            # start Single Robot Loop 
            threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/runtimemodel/main.py", robotName])).start()
            time.sleep(1)
            # start Messages Component
            threading.Thread(target=lambda: subprocess.run(["python3", os.getcwd() + "/messages/main.py", robotName])).start()
            time.sleep(1)


        rclpy.init(args=None)
        self.rosNode = TestROSSupervisor(robotCount)
        threading.Thread(target=lambda: rclpy.spin(self.rosNode)).start()
        
        options = Options()
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        time.sleep(2)
        self.driver.get("http://127.0.0.1:5000/")

    def testWebapp(self):
        title = self.driver.title
        self.assertEqual(title,"Flexible Model Display")
    
  
    # def testSUTOneWay(self):
    #     for i in range(0, teams):
    #         xPos = self.driver.find_element(by=By.ID, value="target-x")
    #         xPos.clear()
    #         xPos.send_keys("1")
    #         yPos = self.driver.find_element(by=By.ID, value="target-y")
    #         yPos.clear()
    #         yPos.send_keys(i)
            
    #         number = self.driver.find_element(by=By.ID, value="numberOfObservers")
    #         number.clear()
    #         monitoringTeamSize = 2
    #         number.send_keys(monitoringTeamSize)
            
    #         submit_button = self.driver.find_element(by=By.ID, value="start")
    #         submit_button.click()
            
    #         # Measures Model Fidelity
    #         start = time.time()
    #         while(self.rosNode.angleNotNullCount < (i*monitoringTeamSize)):
    #             continue
    #         end = time.time()
    #         with open("timeMF"+str(teams)+"x"+str(monitoringTeamSize)+".txt", "a", encoding="utf-8") as f:
    #             f.write("time:"+ str(end-start)+"\n")

    #         self.assertEqual(self.rosNode.angleNotNullCount, (i*monitoringTeamSize))
    #         print("MF " + str(end-start))
    #         time.sleep(2)
    
    def testDestinationOneWay(self):
        for i in range(0, teams):
            xPos = self.driver.find_element(by=By.ID, value="target-x")
            xPos.clear()
            xPos.send_keys("1")
            yPos = self.driver.find_element(by=By.ID, value="target-y")
            yPos.clear()
            yPos.send_keys(i)
            
            number = self.driver.find_element(by=By.ID, value="numberOfObservers")
            number.clear()

            number.send_keys(monitoringTeamSize)
            
            submit_button = self.driver.find_element(by=By.ID, value="start")
            submit_button.click()
            
            # Measures Model Fidelity
            start = time.time()
            while(self.rosNode.angleNotNullCount < (i*monitoringTeamSize)):
                continue
            end = time.time()
            self.assertEqual(self.rosNode.angleNotNullCount, (i*monitoringTeamSize))
            with open("timeMF"+str(teams)+"x"+str(monitoringTeamSize)+".txt", "a", encoding="utf-8") as f:
                f.write("time:"+ str(end-start)+"\n")


            print("MF " + str(end-start))
            time.sleep(2)

    # def testDestinationBothWays(self):
    #     areaInput = self.driver.find_element(by=By.NAME, value="area")
    #     areaInput.send_keys("B")
        
    #     stateInput = self.driver.find_element(by=By.ID, value="state")
    #     stateInput.send_keys("driving")

    #     submit_button = self.driver.find_element(by=By.ID, value="goalAdaption")
    #     submit_button.click()
    #     self.driver.find_element(by=By.ID, value="robo1goalReached").text
        
    #     # Measures Model Fidelity Both Ways
    #     start = time.time()
    #     while(self.driver.find_element(by=By.ID, value="robo1goalReached").text != "false"):
    #         continue
    #     end = time.time()
    #     print("MF x2 " + str(end-start))

    #     self.assertEqual(self.driver.find_element(by=By.ID, value="robo1goalReached").text, "false")          
        
    #     recentxPos= self.driver.find_element(by=By.ID, value="robo1theta").text
    #     for i in range(10):
    #         time.sleep(2) #webapp updates every 1s 
    #         print("hello")
    #         print(self.driver.find_element(by=By.ID, value="robo1theta").text)
    #         self.assertNotEqual(self.driver.find_element(by=By.ID, value="robo1theta").text, str(recentxPos))
    #         recentxPos= self.driver.find_element(by=By.ID, value="robo1theta").text
            
       
        
if __name__ == '__main__':
    unittest.main()
    