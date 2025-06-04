import psutil
import os
import threading


# monitor
def monitor_resource_usage(interval=2):
    process = psutil.Process(os.getpid())
    while True:
        cpu_percent = process.cpu_percent(interval=interval)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 ** 2)
        print(f"📊 [Monitor] CPU: {cpu_percent:.2f}% | RAM: {mem_mb:.2f} MB")

def start_monitoring():
    t = threading.Thread(target=monitor_resource_usage, daemon=True)
    t.start()

