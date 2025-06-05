import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv("graphs/monitor_log.csv", parse_dates=["timestamp"])
# df = pd.read_csv("monitor_log.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)
df[["cpu_percent", "ram_mb"]].plot(figsize=(12, 6))
plt.title("CPU and RAM usage over time")
plt.ylabel("Usage")
plt.grid()
plt.show()
