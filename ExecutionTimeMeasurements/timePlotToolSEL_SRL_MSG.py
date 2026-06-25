import re
import statistics
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

SELtime = read_times("timeSEL7000.txt")
SRLtime = read_times("timeSRL.txt")
MSGtime = read_times("timeMSG.txt")
print(max(SELtime), max(SRLtime), max(MSGtime))
print(statistics.median(SRLtime))
print(statistics.median(SELtime))
print(statistics.median(MSGtime))
plt.boxplot([SELtime, SRLtime, MSGtime], vert=False, labels=["Swarm Element Loop", "Single Robot Loop", "Messages Component"])
plt.title("Execution Times of Each Component")
plt.xlabel("Seconds")
plt.tight_layout()
plt.show()