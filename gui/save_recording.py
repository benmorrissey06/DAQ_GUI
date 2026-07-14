import csv
import json
import os
import time
#STORAGE
'''
all file writing code should be handled in this file
'''
class DataRecorder:
    def __init__(self):
        self.csv_file = None
        self.csv_writer = None
        self.file_name = ""
        self.save_directory = ""

    def open_csv(self):
        self.csv_file = open(f"{self.file_name}.csv", 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["host_time", "sample_counter", "high_ch1", "high_ch2", "high_ch3", "high_ch4", "low_ch1", "low_ch2", "low_ch3", "low_ch4", "difference_ch1", "difference_ch2", "difference_ch3", "difference_ch4", "event"])

    def write_row(self, sample_counter=None, high=None, low=None, difference=None, event=""):
        if self.csv_writer:
            self.csv_writer.writerow([time.time(), sample_counter if sample_counter is not None else ""] + list(high or ["", "", "", ""]) + list(low or ["", "", "", ""]) + list(difference or ["", "", "", ""]) + [event])

    def close_csv(self):
        if self.csv_file:
            self.csv_file.flush()
            os.fsync(self.csv_file.fileno())
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None

    def write_metadata_sidecar(self, meta):
        with open(f"{self.file_name}.json", 'w') as f:
            json.dump(meta, f, indent=2)
