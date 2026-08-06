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
        self.last_flush = 0.0

    def open_csv(self):
        self.csv_file = open(f"{self.file_name}.csv", 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["host_time", "sample_counter", "high_ch1", "high_ch2", "high_ch3", "high_ch4", "low_ch1", "low_ch2", "low_ch3", "low_ch4", "difference_ch1", "difference_ch2", "difference_ch3", "difference_ch4", "vis_pd_calibrated", "event"])
        self.last_flush = time.time()

    def write_row(self, sample_counter=None, high=None, low=None, difference=None, vis_pd_calibrated=None, event=""):
        '''
        new feature: flush every 5 seconds to avoid data loss with a crash. can change the 5 if we need better performance, but this makes it so we send data to OS faster
        '''
        if self.csv_writer:
            now = time.time()
            self.csv_writer.writerow([now, sample_counter if sample_counter is not None else ""] + list(high or ["", "", "", ""]) + list(low or ["", "", "", ""]) + list(difference or ["", "", "", ""]) + [vis_pd_calibrated if vis_pd_calibrated is not None else "", event])
            if now - self.last_flush >= 5:
                self.csv_file.flush()
                self.last_flush = now

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
