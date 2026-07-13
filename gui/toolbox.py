import dearpygui.dearpygui as dpg
from tkinter import Tk, filedialog

VIS_PD_MAX = 255
IR_PD_MAX = 255
VIS_LED_MAX = 4095

SLIDER_DEFS = {
    "IR LED Blink": (1000, "pulse_ir_led"),
    "VIS PD Gain": (VIS_PD_MAX, "set_visible_pd_gain"),
    "IR PD Gain": (IR_PD_MAX, "set_ir_pd_gain"),
    "VIS LED Gain": (VIS_LED_MAX, "set_vis_led_dac"),
}

DEVICE_SLIDER_DEFS = {
    "IR LED Intensity": (1000, "pulse_ir_led"),
    "VIS PD Gain": (VIS_PD_MAX, "set_visible_pd_gain"),
    "IR PD Gain": (IR_PD_MAX, "set_ir_pd_gain"),
    "VIS LED Gain": (VIS_LED_MAX, "set_vis_led_dac"),
}

class Toolbox:
    def initialize_toolbox(self, compact):
        self.compact = compact
        self.is_live = False
        self.light_values = []
        self.time_stamps = []
        self.recording_duration = 0.0
        self.active_rows = []
        self.ttl_drops_below = True
        self.wait_for_input = False
        self.send_output = False

        #When implementing custom recording controls, this labels each segment of time
        self.segment_counter = 1
        #Whether or not there is an overlap in the segments, will be function to determine
        self.no_overlap = True

    def t(self, name):
        '''
        Super useful function to generate unique tags for each tab, so we can control each device independently
        '''
        return f"{name}_{self.tid}"

    def draw_general_ctrls(self, compact):
        slider_defs = DEVICE_SLIDER_DEFS if compact else SLIDER_DEFS
        for label, (max_val, _) in slider_defs.items():
            if compact:
                with dpg.group(horizontal=False):
                    dpg.add_text(label)
                    with dpg.group(horizontal=True):
                        dpg.add_slider_int(max_value=max_val, width=135, tag=self.t(f"s_{label}"),callback = self.on_slider_changed, user_data=label)
                        dpg.add_input_int(label='', width=33, tag=self.t(f"i_{label}"),callback = self.on_slider_changed, user_data=label, step=0)
                        dpg.add_button(width = 50, label="Set",tag = self.t(f"set_{label}"), callback=self.on_slider_changed, user_data=label)
            else:
                dpg.add_text(label)
                with dpg.group(horizontal=True):
                    dpg.add_slider_int(max_value=max_val, width=150, tag=self.t(f"s_{label}"), callback=self.on_slider_changed, user_data=label)
                    dpg.add_input_int(label='', width=80, tag=self.t(f"i_{label}"), callback=self.on_slider_changed, user_data=label, step=0)
                    dpg.add_button(label="Set", callback=self.on_slider_changed, user_data=label,tag=self.t(f"set_{label}_button"))
        if not compact:
            dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_text("Stream decimation")
        with dpg.group(horizontal=True):
            dpg.add_input_int(label="", width=200, default_value=10, min_value=1, max_value=65535, tag=self.t("stream_decimation_input"), callback=self.set_stream_decimation)
            dpg.add_button(label="Set", callback=self.set_stream_decimation, user_data=None, tag=self.t("set_stream_decimation_button"))
        dpg.add_text("Sample rate (10-250 Hz)")
        with dpg.group(horizontal=True):
            dpg.add_input_int(label="", width=200, default_value=100, min_value=10, max_value=250, tag=self.t("sample_rate_input"), callback=self.set_sample_rate)
            dpg.add_button(label="Set", callback=self.set_sample_rate, user_data=None,tag=self.t("set_sample_rate_button"))
        if compact:
            dpg.add_separator()
            with dpg.group(horizontal= True):
                dpg.add_text("LIVE")
                dpg.add_button(label="OFF", tag=self.t("live_button"), callback=self.live_plot_toggle)
            dpg.add_separator()
            with dpg.group(tag=self.t("event_legend"), show=True):
                dpg.add_checkbox(label ="Show Event Color Key",default_value = False,callback=self.toggle_event_legend)
                with dpg.group(horizontal=False,tag = self.t("event_legend_group"), show=False):
                    with dpg.group(horizontal = True):
                        dpg.add_text("[BLUE]", color=self.event_colors["live"])
                        dpg.add_text("Live on/off")
                    with dpg.group(horizontal=True):
                        dpg.add_text("[GREEN]", color=self.event_colors["record"])
                        dpg.add_text("Record start/stop")
                    with dpg.group(horizontal=True):
                        dpg.add_text("[ORANGE]", color=self.event_colors["control"])
                        dpg.add_text("Slider Gain / LED")
                    with dpg.group(horizontal=True):
                        dpg.add_text("[PURPLE]", color=self.event_colors["stream"])
                        dpg.add_text("Sample rate / Decimation")
                    with dpg.group(horizontal=True):
                        dpg.add_text("[PINK]", color=self.event_colors["uv"])
                        dpg.add_text("LED Changes (Via Schedule)")
        else:
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_text("LIVE")
            dpg.add_button(label="OFF", tag=self.t("live_button"), callback=self.live_toggle_all)
            dpg.add_spacer(height=10)

    def draw_recording_ctrls(self, compact):
        dpg.add_spacer(height=10)
        dpg.add_text("Start Recording: ")
        dpg.add_separator()
        if compact:
            dpg.add_input_float(label="", width=200, default_value=30, min_value=1.0, max_value=3600.0, callback=self.update_recording_duration,tag=self.t("recording_duration_input"))
            dpg.add_text("Recording Duration (s)")
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_text("Add Recording Segments: ")
        else:
            dpg.add_input_float(label="Duration (s)", width=200, callback=self.update_recording_duration)
            dpg.add_spacer(height=10)
            dpg.add_text("Add Recording Segments: ")
            dpg.add_separator()
        dpg.add_button(label="Add Segment", callback=self.add_recording_segment)
        # The group will then appear here
        with dpg.group(tag=self.t("protocol_group")):
            dpg.add_text("")
        '''
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
        '''
        dpg.add_button(label="Save Recording Settings", callback=self.prepare_recording)
        with dpg.group(tag=self.t("Confirm info")):
            dpg.add_text("")
        dpg.add_spacer(height=10)
        dpg.add_button(label="Browse Save Location", callback=self.browse_save_directory)
        dpg.add_text("No folder selected", tag=self.t("save_dir_display"))
        if compact:
            dpg.add_text("", tag=self.t("filename"))
            dpg.add_separator()
            dpg.add_button(label="START", tag=self.t("start_button"), callback=self.start_recording)
        else:
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="START ALL", callback=self.start_all)
                dpg.add_button(label="STOP ALL", callback=self.stop_all)

    # Slider Control
   
    def on_slider_changed(self, sender, app_data, user_data):
        '''
        Function used when a slider is changed, or input, and when we set, it's called for all 3.
        If we have not clicked set yet, it only updates the value for both, 
        and if we click set,it actually sends the command!
        '''
         #***VERIFY THAT THIS SETUP WORKS!
        if sender == self.t(f"s_{user_data}") or sender == self.t(f"i_{user_data}"):
            dpg.set_value(self.t(f"s_{user_data}"), app_data)
            dpg.set_value(self.t(f"i_{user_data}"), app_data)
        else:
            slider_value = dpg.get_value(self.t(f"s_{user_data}")) 
            method_name = (DEVICE_SLIDER_DEFS if self.compact else SLIDER_DEFS)[user_data][1]
            if self.compact:
                getattr(self.daq, method_name)(slider_value)
                self.record_event(f"{user_data}={slider_value}", value=slider_value, event_type="control")
            else:
                for tab in self.app.device_tabs:
                    if tab.daq.is_open:
                        getattr(tab.daq, method_name)(slider_value)
                        tab.record_event(f"MASTER_{user_data}", value=slider_value, event_type="control")

    def set_stream_decimation(self, sender, app_data, user_data):
        if sender == self.t('set_stream_decimation_button'):
            value = dpg.get_value(self.t("stream_decimation_input"))
            value = max(1, int(value))
            if self.compact:
                self.daq.set_adc_stream_decimation(value)
                self.record_event("STREAM_DECIMATION", value=value, event_type="stream")
            else:
                for tab in self.app.device_tabs:
                    if tab.daq.is_open:
                        tab.daq.set_adc_stream_decimation(value)
                        tab.record_event("MASTER_STREAM_DECIMATION", value=value, event_type="stream")

    def set_sample_rate(self, sender, app_data, user_data):
        if sender == self.t('set_sample_rate_button'):
            value = dpg.get_value(self.t("sample_rate_input"))
            value = max(10, min(250, int(value)))
            if self.compact:
                self.daq.set_sample_rate(value)
                self.record_event("SAMPLE_RATE", value=value, event_type="stream")
            else:
                for tab in self.app.device_tabs:
                    if tab.daq.is_open:
                        tab.daq.set_sample_rate(value)
                        tab.record_event("MASTER_SAMPLE_RATE", value=value, event_type="stream")

    def update_recording_duration(self, sender, app_data, user_data):
        self.recording_duration = app_data

    def add_recording_segment(self, sender=None, app_data=None, user_data=None):
        #add a new segment under custom recording controls, where you can set start time, stop time, and the gain during that period
        self.segment_counter += 1
        sc = self.segment_counter
        row_tag = self.t(f"row_{sc}")
        self.active_rows.append((row_tag, sc))

        with dpg.group(horizontal=not self.compact, parent=self.t("protocol_group"), tag=row_tag):
            dpg.add_separator()
            dpg.add_input_int(label="Start (s)", width=100, step=0, tag=self.t(f"start_{sc}"))
            dpg.add_input_int(label="End (s)", width=100, step=0, tag=self.t(f"end_{sc}"))
            dpg.add_input_int(label="VIS DAC Value" if self.compact else "UV Val", width=100, step=0, tag=self.t(f"uv_{sc}"))
        
        
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
        if self.compact:
            self.recording_duration = dpg.get_value(self.t("recording_duration_input"))
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
        self.ttl_drops_below = not getattr(self, 'ttl_drops_below', True)
        label = 'Drops Below' if self.ttl_drops_below else 'Goes Above'
        try:
            dpg.configure_item(self.t('ttl_direction_button'), label=label)
        except Exception:
            pass
        if self.compact:
            self.ttl_condition = 'below' if self.ttl_drops_below else 'above'

    def set_trigger_option(self, sender, app_data, user_data):
        if user_data == 'send':
            self.send_output = app_data
        elif user_data == 'wait':
            self.wait_for_input = app_data

    def browse_save_directory(self, sender=None, app_data=None, user_data=None):
        '''
        file browser pop up
        '''
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Save Location")
        root.destroy()
        if folder:
            if self.compact:
                self.recorder.save_directory = folder
                dpg.set_value(self.t("save_dir_display"), f"Saving to: {folder}")
            else:
                dpg.set_value(self.t("save_dir_display"), f"Saving to: {folder}")
                for tab in self.app.device_tabs:
                    tab.recorder.save_directory = folder
                    dpg.set_value(tab.t("save_dir_display"), f"Saving to: {folder}")
