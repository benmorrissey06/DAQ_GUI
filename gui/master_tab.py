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
                    dpg.add_spacer(height = 40)
                    dpg.add_text("Device Monitor")
                    dpg.add_separator()
                    with dpg.group(tag=self.t("devices")):
                        pass
                    dpg.add_button(label="+", callback=self.app.add_device_tab)

                with dpg.child_window(width=-1, height=-1):
                    self.draw_recording_ctrls(compact=False)
                    

    def add_device(self, tab):
        with dpg.group(parent=self.t("devices"), tag=tab.t("manager")):
            with dpg.group(horizontal=True):
                dpg.add_input_text(default_value=tab.name, width=200, callback=self.rename_device, user_data=tab)
                dpg.add_button(label="X", callback=self.remove_device, user_data=tab)
                dpg.add_text("", tag=tab.t("delete_warning"))
            dpg.add_text("", tag=tab.t("device_status"))
        self.update_device_status(tab)

    def rename_device(self, sender, app_data, tab):
        tab.name = app_data
        dpg.configure_item(tab.t("device_tab"), label=app_data)
        self.update_recording_state()

    def remove_device(self, sender, app_data, tab):
        if dpg.get_value(tab.t("delete_warning")):
            self.app.remove_device_tab(tab)
        else:
            dpg.set_value(tab.t("delete_warning"), "Are you sure? Click X again to remove this device.")

    def update_device_status(self, tab):
        dpg.set_value(tab.t("device_status"), f"Live: {'yes' if tab.is_live else 'no'}, Connected: {'yes' if tab.daq.is_open else 'no'}, Recording: {'yes' if tab.is_recording else 'no'}")

    def update_device_statuses(self):
        for tab in self.app.device_tabs:
            self.update_device_status(tab)

    def collect_info(self, sender, app_data, user_data):
        label = dpg.get_item_label(sender)
        if label == "Cohort":
            self.cohort = app_data
        elif label == "Test Label":
            self.test_label = app_data

    def live_toggle_all(self, sender, app_data, user_data):
        if not any(tab.daq.is_open for tab in self.app.device_tabs):
            self.set_general_message("No device tabs available." if not self.app.device_tabs else "No connected devices.")
            return
        self.set_general_message("")
        self.is_live = not self.is_live
        label = "ON" if self.is_live else "OFF"
        dpg.configure_item(self.t("live_button"), label=label)
        for tab in self.app.device_tabs:
            if tab.daq.is_open:
                dpg.configure_item(tab.t("live_button"), label=label)
                if tab.is_live == self.is_live:
                    continue
                tab.is_live = self.is_live
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
        self.update_device_statuses()

    def update_recording_state(self):
        active = [tab.name for tab in self.app.device_tabs if tab.is_recording]
        dpg.configure_item(self.t("start_all_button"), label="STOP ALL" if active else "START ALL")
        dpg.set_value(self.t("recording_status"), f"Recording: {', '.join(active)}. Stop all before starting again." if active else "")
        self.update_device_statuses()

    def start_all(self, sender, app_data, user_data):
        if any(tab.is_recording for tab in self.app.device_tabs):
            self.stop_all(sender, app_data, user_data)
            return
        warnings = []
        ready = []
        for tab in self.app.device_tabs:
            if not tab.daq.is_open:
                warnings.append(f"{tab.name} not connected.")
            elif not tab.is_live:
                warnings.append(f"{tab.name} not live.")
            else:
                ready.append(tab)
        if not self.app.device_tabs:
            warnings.append("No device tabs available.")
        self.set_recording_warning(warnings)
        if not ready:
            return
        self.prepare_recording()
        if not self.no_overlap:
            return
        for tab in ready:
            name = dpg.get_value(tab.t("filename"))
            if not name or not tab.recorder.save_directory:
                continue
            tab.recorder.file_name = os.path.join(tab.recorder.save_directory, name)
            tab.is_recording = True
            tab.start_time = time.time()
            tab.recording_duration = self.recording_duration
            tab.time_stamps = list(self.time_stamps)
            tab.light_values = list(self.light_values)
            tab.vis_dac_baseline = dpg.get_value(tab.t("s_VIS LED Gain"))
            tab.make_vis_schedule()
            dpg.configure_item(tab.t('start_button'), label='STOP')
            try:
                tab.recorder.open_csv()
                tab.record_event("RECORDING_START", event_type="record", write_to_csv=False)
                tab.recorder.write_metadata_sidecar(tab.recording_metadata(dpg.get_value(self.t("sample_rate_input")), dpg.get_value(self.t("stream_decimation_input")), dpg.get_value(self.t("s_VIS PD Gain")), dpg.get_value(self.t("s_IR PD Gain"))))
                tab.upload_schedule_to_daq()
            except OSError:
                tab.is_recording = False
                dpg.configure_item(tab.t('start_button'), label='START')
        self.update_recording_state()

    def stop_all(self, sender, app_data, user_data):
        for tab in self.app.device_tabs:
            if tab.is_recording:
                tab.record_event("RECORDING_STOP", event_type="record", write_to_csv=False)
                tab.is_recording = False
                tab.daq.stop_vis_schedule()
                tab.daq.set_vis_led_dac(tab.vis_dac_baseline)
                tab.recorder.close_csv()
                dpg.configure_item(tab.t('start_button'), label='START')
        self.update_recording_state()
