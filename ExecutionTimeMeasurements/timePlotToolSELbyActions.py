import re
import sys
import pandas as pd
import matplotlib.pyplot as plt

file = sys.argv[1]

# parse log 
pattern = re.compile(r"^(.*?)\s*time:(\d+\.?\d*(?:e-?\d+)?)")
data = []
with open(file) as f:
    for line in f:
        m = pattern.search(line.strip())
        if m:
            action = m.group(1).strip()
            time = float(m.group(2))
            data.append((action, time))
df = pd.DataFrame(data, columns=["action","time"])

# gewünschte Reihenfolge (z.B. nach Median)
order = df.groupby("action")["time"].median().sort_values().index.tolist()
print("Plot order:", order)   # zur Kontrolle

# Gruppiert anschauen
print(df.groupby("action")["time"].describe())

# Liste von arrays in exakt dieser Reihenfolge
groups = [df.loc[df["action"]==a, "time"].values for a in order]

plt.figure(figsize=(14,7))
plt.boxplot(groups, labels=order, showfliers=False, widths=0.6)
plt.xticks(rotation=45, ha="right")
plt.xlabel("Action")
plt.ylabel("Time (s)")
plt.title("Execution times per action (ordered by median)")
plt.tight_layout()
plt.show()