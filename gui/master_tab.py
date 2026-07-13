import dearpygui.dearpygui as dpg
import os
import time
from toolbox import Toolbox, SLIDER_DEFS

'''
MASTER TAB
Controls that will be applied to ALL connected devices.
General controls, and recording controls.
'''

class MasterTab(Toolbox):
    def __init__(self, app):
        self.app = app
        self.tid = "m"
        self.cohort = None
        self.test_label = None
        self.initialize_toolbox(False)

        self.build_ui()

    def build_ui(self):
        with dpg.tab(label="Master", parent="main_tab_bar", tag="master_tab"):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=600, height=-1):
                    dpg.add_separator()
                    dpg.add_spacer(height=10)
                    dpg.add_input_text(label="Cohort", callback=self.collect_info)
                    dpg.add_input_text(label="Test Label", callback=self.collect_info)
                    dpg.add_separator()
                    dpg.add_spacer(height=10)
                    self.draw_general_ctrls(compact=False)

                with dpg.child_window(width=-1, height=-1):
                    self.draw_recording_ctrls(compact=False)

    def collect_info(self, sender, app_data, user_data):
        label = dpg.get_item_label(sender)
        if label == "Cohort":
            self.cohort = app_data
        elif label == "Test Label":
            self.test_label = app_data

    def live_toggle_all(self, sender, app_data, user_data):
        self.is_live = not self.is_live
        label = "ON" if self.is_live else "OFF"
        dpg.configure_item(self.t("live_button"), label=label)
        for tab in self.app.device_tabs:
            if tab.daq.is_open:
                tab.is_live = self.is_live
                dpg.configure_item(tab.t("live_button"), label=label)
                if self.is_live:
                    tab.daq.set_adc_streaming(True)
                    tab.daq.set_adc_stream_decimation(int(dpg.get_value(self.t("stream_decimation_input"))))
                    tab.daq.set_sample_rate(int(dpg.get_value(self.t("sample_rate_input"))))
                    tab.daq.start_device()
                    tab.record_event("MASTER_LIVE_ON", value=1, event_type="live")
                else:
                    tab.daq.set_adc_streaming(False)
                    tab.daq.stop_device()
                    tab.record_event("MASTER_LIVE_OFF", value=0, event_type="live")

    def start_all(self, sender, app_data, user_data):
        self.prepare_recording()
        if not self.no_overlap:
            return
        for tab in self.app.device_tabs:
            if not tab.daq.is_open or tab.is_recording:
                continue
            name = dpg.get_value(tab.t("filename"))
            if not name or not tab.recorder.save_directory:
                continue
            tab.recorder.file_name = os.path.join(tab.recorder.save_directory, name)
            tab.is_recording = True
            tab.start_time = time.time()
            tab.recording_duration = self.recording_duration
            tab.time_stamps = list(self.time_stamps)
            tab.light_values = list(self.light_values)
            dpg.configure_item(tab.t('start_button'), label='STOP')
            try:
                tab.recorder.open_csv()
                tab.recorder.write_metadata_sidecar({
                    "date": tab.date,
                    "cohort": self.cohort or "",
                    "animal_id": tab.animal_id or "",
                    "test_label": self.test_label or "",
                    "recording_duration": self.recording_duration,
                    "sample_rate": dpg.get_value(self.t("sample_rate_input")),
                    "decimation": dpg.get_value(self.t("stream_decimation_input")),
                    "vis_pd_gain": dpg.get_value(self.t("s_VIS PD Gain")),
                    "ir_pd_gain": dpg.get_value(self.t("s_IR PD Gain")),
                    "vis_led_dac": dpg.get_value(self.t("s_VIS LED Gain")),
                })
                tab.upload_schedule_to_daq()
            except OSError:
                tab.is_recording = False
                dpg.configure_item(tab.t('start_button'), label='START')

    def stop_all(self, sender, app_data, user_data):
        for tab in self.app.device_tabs:
            if tab.is_recording:
                tab.is_recording = False
                tab.daq.stop_vis_schedule()
                tab.recorder.close_csv()
                dpg.configure_item(tab.t('start_button'), label='START')
