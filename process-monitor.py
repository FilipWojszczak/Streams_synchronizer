import psutil
import csv
from datetime import datetime
import time


class Monitor:
    def __init__(self, process_id, process_name, time_period, samples_amount, synchronizer_name, additional_info):
        self.process_id = process_id
        self.process_name = process_name
        self.time_period = time_period
        self.samples_amount = samples_amount
        self.csv_processing = CSVProcessing(synchronizer_name, additional_info)
        self.data = []
        self.process = None

    def monitor(self):
        counter = 0
        self.process = [proc for proc in psutil.process_iter()
                        if proc.name() == self.process_name and proc.pid == self.process_id]
        self.process = self.process[0]
        while True:
            try:
                cpu_usage = self.process.cpu_percent()
                memory_usage = self.process.memory_full_info().uss
                self.data.append([cpu_usage, memory_usage])
                print(cpu_usage, memory_usage)
                time.sleep(self.time_period)
                counter += 1
                if self.samples_amount == counter:
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                print("end")
                self.csv_processing.save(self.data)

    # def __exit__(self):
    #     print("end")
    #     self.csv_processing.save(self.data)


class CSVProcessing:
    def __init__(self, synchronizer_name, additional_info):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.directory = 'pliki_csv\\' + timestamp + "_" + synchronizer_name + "_" + additional_info + ".csv"

    def save(self, data):
        with open(self.directory, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerows(data)
        print("Saved")


pid = 12716
process_num = "python.exe"
time_per = 5  # in seconds
samples_amo = -1
synchronizer_nam = "GStreamer"  # "OpenCV"
ad_info = ""
monitor = Monitor(pid, process_num, time_per, samples_amo, synchronizer_nam, ad_info)
monitor.monitor()
