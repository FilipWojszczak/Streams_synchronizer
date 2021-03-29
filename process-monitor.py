import psutil
import csv
from datetime import datetime
import time


class Monitor:
    def __init__(self, process_name, time_period, synchronizer_name, additional_info):
        self.process_name = process_name
        self.time_period = time_period
        self.csv_processing = CSVProcessing(synchronizer_name, additional_info)
        self.data = []
        self.process = None

    def monitor(self):
        while True:
            self.process = [proc for proc in psutil.process_iter() if proc.name == self.process_name]
            self.process = self.process[0]
            cpu_usage = self.process.cpu_percent()
            memory_usage = self.process.memory_full_info().uss
            time.sleep(self.time_period)


class CSVProcessing:
    def __init__(self, synchronizer_name, additional_info):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.directory = '\\pliki_csv\\' + timestamp + "_" + synchronizer_name + "_" + additional_info + ".csv"

    def save(self, data):
        with open(self.directory, newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';')
            csv_writer.writerows(data)



prcs_nm = "python.exe"
tm_prd = 5  # in seconds
snc_nm = "GStreamer"  # "OpenCV"
ad_info = ""
