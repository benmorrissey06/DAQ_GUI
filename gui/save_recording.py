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
        self.csv_writer.writerow(["host_time", "ch1_raw", "ch2_raw", "ch3_raw", "ch4_raw"])

    def write_row(self, raw):
        if self.csv_writer:
            self.csv_writer.writerow([time.time()] + list(raw))

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
