import re
import sys
import pandas as pd
import matplotlib.pyplot as plt

import re
import matplotlib.pyplot as plt

pattern = re.compile(r'time:([0-9]+\.?[0-9]*(?:[eE][+-]?[0-9]+)?)')

def read_times(filename):
    times = []
    with open(filename) as f:
        for line in f:
            m = pattern.search(line)
            if m:
                try:
                    val = float(m.group(1))
                    if val < 3.0:
                        times.append(val)
                except ValueError:
                    print(f"could not parse: {m.group(1)}")
    print(f"Read {len(times)} values from {filename}, sample: {times[:5]}")
    return times

preyDetected = read_times("time_PreyDetected.txt")
robotWithLoadDetected = read_times("time_RobotWithLoadDetected.txt")
robotLoadingDetected = read_times("time_RobotLoadingDetected.txt")
joinerDetected = read_times("time_JoinerDetected.txt")
print(max(preyDetected), max(robotWithLoadDetected), max(robotLoadingDetected, joinerDetected))
plt.boxplot([preyDetected, robotWithLoadDetected, robotLoadingDetected, joinerDetected], vert=False, labels=["Prey detected", "Robot with Load detected", "Robot in Loading State detected", "Joiner detected"])
plt.title("Full System Execution Times for specific Actions")
plt.xlabel("Seconds")
plt.tight_layout()
plt.show()