import psutil
import csv
from datetime import datetime
import time
import sys


class Monitor:
    def __init__(self, process_id, process_name, time_period, samples_amount, synchronizer_name, additional_info):
        self.process_id = process_id
        self.process_name = process_name
        self.time_period = time_period
        self.samples_amount = samples_amount
        self.csv_processing = CSVProcessing(synchronizer_name, additional_info)
        self.data = [["Sample number", "CPU usage [%]", "Memory usage [B]"]]
        self.process = None
        self.cpus_threads = psutil.cpu_count()

    def monitor(self):
        counter = 1
        for proc in psutil.process_iter():
            if proc.name() == self.process_name and proc.pid == self.process_id:
                self.process = proc
                break

        while True:
            try:
                cpu_usage = self.process.cpu_percent() / self.cpus_threads
                memory_usage = self.process.memory_full_info().uss
                self.data.append([counter, cpu_usage, memory_usage])
                print(cpu_usage, memory_usage)
                # , self.process.num_threads()
                time.sleep(self.time_period)
                counter += 1
                if self.samples_amount == counter:
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                self.csv_processing.save(self.data)
                sys.exit(0)


class CSVProcessing:
    def __init__(self, synchronizer_name, additional_info):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.directory = 'pliki_csv\\' + timestamp + "_" + synchronizer_name + "_" + additional_info + ".csv"

    def save(self, data):
        with open(self.directory, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerows(data)
        print("Saved")


pid = 4264
process_num = "python.exe"
time_per = 1  # in seconds
samples_amo = -1
synchronizer_nam = "GStreamer"  # "OpenCV"
ad_info = ""
monitor = Monitor(pid, process_num, time_per, samples_amo, synchronizer_nam, ad_info)
monitor.monitor()
