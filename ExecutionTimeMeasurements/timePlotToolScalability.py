import re
from statistics import mean, median
import sys
import numpy as np
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
                    if val < 2.5:
                        times.append(val*1000)
                except ValueError:
                    print(f"could not parse: {m.group(1)}")
    #print(f"Read {len(times)} values from {filename}, sample: {times[:5]}")
    return times

three = read_times("timeMF4x1.txt")
six = read_times("timeMF4x2.txt")
ten = read_times("timeMF8x1.txt")
nineteen = read_times("timeMF6x2.txt")
thirty = read_times("timeMF12x1.txt")
thirty2 = read_times("timeMF4x3.txt")

print(max(three), max(six), max(ten), max(thirty), max(thirty2))
print(median(three), median(thirty))
print(mean(three), mean(thirty))
bp = plt.boxplot([three, six, ten, nineteen, thirty, thirty2], vert=False, labels=["4x1", "4x2", "8x1", "6x2", "12x1", "4x3"])
print(f'{"medians"}: {[item.get_xdata() for item in bp["medians"]]}n')

#plt.title("SEL Execution Times for X Robots (warm start)")
plt.xlabel("Milliseconds")
plt.xticks(np.arange(0, 600, 100))
plt.tight_layout()
plt.show()