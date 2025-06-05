import psutil
import os
import threading
import time
import csv
from datetime import datetime


# monitor
def monitor_resource_usage_v1(interval=2):
    process = psutil.Process(os.getpid())
    while True:
        cpu_percent = process.cpu_percent(interval=interval)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 ** 2)
        print(f"📊 [Monitor] CPU: {cpu_percent:.2f}% | RAM: {mem_mb:.2f} MB")

def start_monitoring_v1():
    t = threading.Thread(target=monitor_resource_usage_v1, daemon=True)
    t.start()

# monitor version 2
def monitor_resource_usage_v2(interval=2):
    process = psutil.Process(os.getpid())

    while True:
        # CPU usage of the process (measured twice for accuracy)
        process.cpu_percent(interval=None)
        time.sleep(interval)
        cpu_percent = process.cpu_percent(interval=None)

        # Memory usage of the process (RSS = resident set size)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 ** 2)

        # Additional stats
        num_threads = process.num_threads()
        total_mem = psutil.virtual_memory()
        total_used_mb = total_mem.used / (1024 ** 2)
        total_mem_percent = total_mem.percent

        print(f"📊 [Monitor] CPU: {cpu_percent:.2f}% | RAM: {mem_mb:.2f} MB | "
              f"Threads: {num_threads} | SysRAM: {total_used_mb:.2f} MB ({total_mem_percent:.1f}%)")

def start_monitoring_v2():
    t = threading.Thread(target=monitor_resource_usage_v2, daemon=True)
    t.start()




# save to file to exc graf
def monitor_resource_usage_v3(interval=2, log_file=None):
    if log_file is None:
        log_file = os.path.join("graphs", "monitor_log.csv")
    
    process = psutil.Process(os.getpid())
    
   
    if not os.path.exists(log_file):
        with open(log_file, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "cpu_percent", "ram_mb", "threads",
                "sys_ram_used_mb", "sys_ram_percent"
            ])

    while True:

        process.cpu_percent(interval=None)
        time.sleep(interval)
        cpu_percent = process.cpu_percent(interval=None)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024 ** 2)
        num_threads = process.num_threads()

        total_mem = psutil.virtual_memory()
        total_used_mb = total_mem.used / (1024 ** 2)
        total_mem_percent = total_mem.percent

        timestamp = datetime.utcnow().isoformat()


        print(f"📊 [Monitor] CPU: {cpu_percent:.2f}% | RAM: {mem_mb:.2f} MB | "
              f"Threads: {num_threads} | SysRAM: {total_used_mb:.2f} MB ({total_mem_percent:.1f}%)")

# write to csv file
        with open(log_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, cpu_percent, mem_mb, num_threads,
                total_used_mb, total_mem_percent
            ])
            f.flush()

def start_monitoring_v3():
    t = threading.Thread(target=monitor_resource_usage_v3, daemon=True)
    t.start()
