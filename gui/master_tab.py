import dearpygui.dearpygui as dpg
import os
import time
from tkinter import Tk, filedialog
from device_tab import VIS_PD_MAX, IR_PD_MAX, VIS_LED_MAX

'''
MASTER TAB
Global controls that broadcast to all connected device tabs.
'''

SLIDER_DEFS = {
    "IR LED Blink": (1000, "pulse_ir_led"),
    "VIS PD Gain": (VIS_PD_MAX, "set_visible_pd_gain"),
    "IR PD Gain": (IR_PD_MAX, "set_ir_pd_gain"),
    "VIS LED Gain": (VIS_LED_MAX, "set_vis_led_dac"),
}

class MasterTab:
    def __init__(self, app):
        self.app = app
        self.tid = "m"
        self.cohort = None
        self.test_label = None
        self.is_live = False

        self.recording_duration = 0.0
        self.time_stamps = []
        self.light_values = []
        self.active_rows = []
        self.segment_counter = 1
        self.no_overlap = True
        self.ttl_drops_below = True
        self.wait_for_input = False
        self.send_output = False

        self.build_ui()

    def t(self, name):
        return f"{name}_{self.tid}"

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
                    for label, (max_val, _) in SLIDER_DEFS.items():
                        with dpg.group(horizontal=True):
                            dpg.add_slider_int(max_value=max_val, width=150, tag=self.t(f"s_{label}"), callback=self.on_slider_changed, user_data=label)
                            dpg.add_input_int(label=label, width=80, tag=self.t(f"i_{label}"), callback=self.on_slider_changed, user_data=label, step=0)
                    dpg.add_spacer(height=10)
                    dpg.add_separator()
                    dpg.add_text("Streaming")
                    dpg.add_input_int(label="Stream decimation", width=200, default_value=10, min_value=1, max_value=65535, tag=self.t("stream_decimation_input"), callback=self.set_stream_decimation)
                    dpg.add_input_int(label="Sample rate (10-250 Hz)", width=200, default_value=100, min_value=10, max_value=250, tag=self.t("sample_rate_input"), callback=self.set_sample_rate)
                    dpg.add_spacer(height=10)
                    dpg.add_separator()
                    dpg.add_text("LIVE")
                    dpg.add_button(label="OFF", tag=self.t("live_button"), callback=self.live_toggle_all)
                    dpg.add_spacer(height=10)

                with dpg.child_window(width=-1, height=-1):
                    dpg.add_spacer(height=10)
                    dpg.add_text("Start Recording: ")
                    dpg.add_separator()
                    dpg.add_input_float(label="Duration (s)", width=200, callback=self.update_recording_duration)
                    dpg.add_spacer(height=10)
                    dpg.add_text("Add Recording Segments: ")
                    dpg.add_separator()
                    dpg.add_button(label="Add Segment", callback=self.add_recording_segment)
                    with dpg.group(tag=self.t("protocol_group")):
                        dpg.add_text("")
                    dpg.add_separator()
                    dpg.add_text("TTL Outputs")
                    dpg.add_checkbox(label="Enable Closed Loop TTL", default_value=False, callback=self.show_TTL_options)
                    with dpg.group(tag=self.t('ttl_group'), horizontal=True):
                        pass
                    dpg.add_separator()
                    dpg.add_text("Triggers")
                    with dpg.group(tag=self.t('triggers'), horizontal=True):
                        dpg.add_checkbox(label="Send Output Trigger", default_value=False, tag=self.t("send_output_trigger"), callback=self.set_trigger_option, user_data="send")
                        dpg.add_checkbox(label="Wait for Input Trigger", default_value=False, tag=self.t("wait_for_input_trigger"), callback=self.set_trigger_option, user_data="wait")
                    dpg.add_separator()
                    dpg.add_button(label="Save Recording Settings", callback=self.prepare_recording)
                    with dpg.group(tag=self.t("Confirm info")):
                        dpg.add_text("")
                    dpg.add_spacer(height=10)
                    dpg.add_button(label="Browse Save Location", callback=self.browse_save_directory)
                    dpg.add_text("No folder selected", tag=self.t("save_dir_display"))
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="START ALL", callback=self.start_all)
                        dpg.add_button(label="STOP ALL", callback=self.stop_all)

    def collect_info(self, sender, app_data, user_data):
        label = dpg.get_item_label(sender)
        if label == "Cohort":
            self.cohort = app_data
        elif label == "Test Label":
            self.test_label = app_data

    def on_slider_changed(self, sender, app_data, user_data):
        dpg.set_value(self.t(f"s_{user_data}"), app_data)
        dpg.set_value(self.t(f"i_{user_data}"), app_data)
        method_name = SLIDER_DEFS[user_data][1]
        for tab in self.app.device_tabs:
            if tab.daq.is_open:
                getattr(tab.daq, method_name)(app_data)

    def set_stream_decimation(self, sender, app_data, user_data):
        value = max(1, int(app_data))
        for tab in self.app.device_tabs:
            if tab.daq.is_open:
                tab.daq.set_adc_stream_decimation(value)

    def set_sample_rate(self, sender, app_data, user_data):
        value = max(10, min(250, int(app_data)))
        for tab in self.app.device_tabs:
            if tab.daq.is_open:
                tab.daq.set_sample_rate(value)

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
                else:
                    tab.daq.set_adc_streaming(False)
                    tab.daq.stop_device()

    def update_recording_duration(self, sender, app_data, user_data):
        self.recording_duration = app_data

    def add_recording_segment(self, sender=None, app_data=None, user_data=None):
        #add a new segment under custom recording controls, where you can set start time, stop time, and the gain during that period
        self.segment_counter += 1
        sc = self.segment_counter
        row_tag = self.t(f"row_{sc}")
        self.active_rows.append((row_tag, sc))

        with dpg.group(horizontal=True, parent=self.t("protocol_group"), tag=row_tag):
            dpg.add_separator()
            dpg.add_input_int(label="Start (s)", width=100, step=0, tag=self.t(f"start_{sc}"))
            dpg.add_input_int(label="End (s)", width=100, step=0, tag=self.t(f"end_{sc}"))
            dpg.add_input_int(label="UV Val", width=100, step=0, tag=self.t(f"uv_{sc}"))
            dpg.add_button(label=" X ", user_data=row_tag, callback=self.delete_segment)

    def delete_segment(self, sender, app_data, user_data):
        #delete when pressing the X button
        self.active_rows = [(rt, sc) for rt, sc in self.active_rows if rt != user_data]
        dpg.delete_item(user_data)

    def prepare_recording(self, sender=None, app_data=None, user_data=None):
        '''
        When the user is ready to Start a recording, they can press save beforehand to check for overlaps
        and confirm their info, as it will be printed out for them with this.
        '''
        dpg.delete_item(self.t("Confirm info"), children_only=True)
        self.time_stamps.clear()
        self.light_values.clear()

        self.check_overlaps()

        for row_tag, sc in self.active_rows:
            start_val = dpg.get_value(self.t(f"start_{sc}"))
            end_val = dpg.get_value(self.t(f"end_{sc}"))
            uv_val = dpg.get_value(self.t(f"uv_{sc}"))
            self.time_stamps.append((start_val, end_val))
            self.light_values.append(uv_val)

        if self.no_overlap:
            dpg.add_text(f"Recording Duration: {self.recording_duration}", parent=self.t("Confirm info"))
            for i in range(len(self.light_values)):
                dpg.add_text(
                    f"Segment {i+1}: Value of {self.light_values[i]} from time {self.time_stamps[i][0]} s to time {self.time_stamps[i][1]} s",
                    parent=self.t("Confirm info")
                )
        else:
            dpg.add_text("Error - overlapping time segments", parent=self.t("Confirm info"))

    def check_overlaps(self):
        '''
        little function just to protect against mistakes by the user
        if they enter overlapping segments
        '''
        intervals = []
        for row_tag, sc in self.active_rows:
            start_val = dpg.get_value(self.t(f"start_{sc}"))
            end_val = dpg.get_value(self.t(f"end_{sc}"))
            if start_val is None or end_val is None:
                self.no_overlap = False
                return False
            intervals.append((min(start_val, end_val), max(start_val, end_val)))
        intervals.sort(key=lambda x: x[0])
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i-1][1]:
                self.no_overlap = False
                return False
        self.no_overlap = True
        return True

    # TTL Options

    def show_TTL_options(self, sender, app_data, user_data):
        '''
        makes the checkbox for closed loop TTL settings,
        work, so the input fields are shown when it's pressed
        '''
        if not app_data:
            try:
                dpg.delete_item(self.t('ttl_group'), children_only=True)
            except Exception:
                pass
            return
        with dpg.group(parent=self.t('ttl_group')):
            with dpg.group(horizontal=True):
                dpg.add_text("If IR Light")
                dpg.add_button(label='Drops Below', tag=self.t('ttl_direction_button'), callback=self.toggle_ttl_direction)
                dpg.add_input_float(label='Threshold', tag=self.t('ir_value'))
            with dpg.group(horizontal=True):
                dpg.add_text("Then Pulse:")
                dpg.add_input_float(label='Freq (Hz)', tag=self.t('ttl_freq'))
                dpg.add_input_float(label='Width (ms)', tag=self.t('ttl_width'))

    def toggle_ttl_direction(self, sender, app_data, user_data):
        '''
        Toggles button between saying Drops Below and Goes Above
        '''
        self.ttl_drops_below = not self.ttl_drops_below
        label = 'Drops Below' if self.ttl_drops_below else 'Goes Above'
        try:
            dpg.configure_item(self.t('ttl_direction_button'), label=label)
        except Exception:
            pass

    def set_trigger_option(self, sender, app_data, user_data):
        if user_data == 'send':
            self.send_output = app_data
        elif user_data == 'wait':
            self.wait_for_input = app_data

    def browse_save_directory(self, sender=None, app_data=None, user_data=None):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Save Location")
        root.destroy()
        if folder:
            dpg.set_value(self.t("save_dir_display"), f"Saving to: {folder}")
            for tab in self.app.device_tabs:
                tab.recorder.save_directory = folder
                dpg.set_value(tab.t("save_dir_display"), f"Saving to: {folder}")

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
