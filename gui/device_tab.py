import dearpygui.dearpygui as dpg
import threading
import time
import os
from tkinter import Tk, filedialog
from daq import DAQController
from save_recording import DataRecorder
from datetime import datetime

'''
DEVICE TAB

An individual device tab, created via the + button in main GUI.
Must connect to COM ports in this tab, for it to be controllable by master.
'''

VIS_PD_MAX = 255
IR_PD_MAX = 255
VIS_LED_MAX = 4095

CH_NAMES = ["CH1 (IR PD)", "CH2 (VIS PD)", "CH3 (VIS Current)", "CH4 (IR Current)"]
CH_TAGS = ["ch1", "ch2", "ch3", "ch4"]
EVENT_COLORS = {
    "live": [0, 102, 204, 255],
    "record": [0, 153, 76, 255],
    "control": [255, 140, 0, 255],
    "stream": [128, 0, 128, 255],
    "uv": [204, 0, 102, 255],
}

class DeviceTab:
    def __init__(self, tid, tab_bar_tag, app):
        self.tid = tid
        self.tab_bar_tag = tab_bar_tag
        self.app = app
        self.animal_id = None

        self.daq = DAQController()
        self.recorder = DataRecorder()
        self.is_live = False
        self.running = True

        self.x_data = []
        self.y_data = []
        self.date = datetime.now().strftime("%m%d%Y_%H%M")
        self.max_points = 5000
        self.times = []
        self.ch_data = [[] for _ in range(4)]
        self.checked_order = []
        self.t0 = None
        self.plot_window_s = 10.0
        self.ch4_active = False

        self.light_values = []
        self.time_stamps = []
        self.recording_duration = 0.0
        self.active_rows = []
        self.is_recording = False
        self.ttl_drops_below = True
        self._plot_event_line_tags = {ch: [] for ch in CH_TAGS}

        '''
        Variables for trigger integration and TTL 
        '''
        self.wait_for_input = False
        self.input_pin = ""
        self.send_output = False
        self.output_pin = ""
        
        self.ttl_enabled = False
        self.ttl_condition = ""
        self.ttl_threshold = 0
        self.ttl_freq = 0.0
        self.ttl_width = 0.0

        #When implementing custom recording controls, this labels each segment of time
        self.segment_counter = 1
        #Whether or not there is an overlap in the segments, will be function to determine
        self.no_overlap = True

        self.build_ui()
        threading.Thread(target=self.hardware_thread, daemon=True).start()

    def t(self, name):
        return f"{name}_{self.tid}"

    def build_ui(self):
        '''
        The main function where we start dpg,
        and build the layout so to speak

        Everything here should be readable without comments, and DPG was chosen for this reason
        to allow easy manipulation of the layout via a code interface, 
        and this easily separates  hardware commands code (in daq.py) from code for the GUI "frontend"or visual elements
        '''
        with dpg.tab(label=f"Device {self.tid}", parent=self.tab_bar_tag, tag=self.t("device_tab"), before="add_tab_button"):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=250, height=-65):
                    with dpg.tab_bar():
                        #One tab here for each slider,this page has sliders and has stuff from before, custom controls are in other tab
                        with dpg.tab(label="General"):
                            dpg.add_input_text(label="Animal ID", callback=self.set_animal_id)
                            dpg.add_separator()
                            with dpg.group(tag=self.t('com_port_group')):
                                self.view_ports()
                            dpg.add_spacer(height=10)
                            dpg.add_text("Hardware Controls")
                            dpg.add_separator()
                            self.slider_cmds = {
                                "IR LED Intensity": (1000, self.daq.pulse_ir_led),
                                "VIS PD Gain": (VIS_PD_MAX, self.daq.set_visible_pd_gain),
                                "IR PD Gain": (IR_PD_MAX, self.daq.set_ir_pd_gain),
                                "VIS LED Gain": (VIS_LED_MAX, self.daq.set_vis_led_dac),
                            }
                            for label, (max_val, _) in self.slider_cmds.items():
                                with dpg.group(horizontal=False):
                                    dpg.add_text(label)
                                    with dpg.group(horizontal=True):
                                        dpg.add_slider_int(max_value=max_val, width=135, tag=self.t(f"s_{label}"),callback = self.on_slider_changed, user_data=label)
                                        dpg.add_input_int(label='', width=33, tag=self.t(f"i_{label}"),callback = self.on_slider_changed, user_data=label, step=0)
                                        dpg.add_button(width = 50, label="Set",tag = self.t(f"set_{label}"), callback=self.on_slider_changed, user_data=label)
       
                            dpg.add_separator()
                            dpg.add_text("Stream decimation")
                            dpg.add_input_int(label="", width=200, default_value=10, min_value=1, max_value=65535, tag=self.t("stream_decimation_input"), callback=self.set_stream_decimation)
                            dpg.add_text("Sample rate (10-250 Hz)")
                            dpg.add_input_int(label="", width=200, default_value=100, min_value=10, max_value=250, tag=self.t("sample_rate_input"), callback=self.set_sample_rate)
                            dpg.add_separator()
                            with dpg.group(horizontal= True):
                                dpg.add_text("LIVE")
                                dpg.add_button(label="OFF", tag=self.t("live_button"), callback=self.live_plot_toggle)
                            dpg.add_separator()
                            with dpg.group(tag=self.t("event_legend"), show=True):
                                dpg.add_checkbox(label ="Show Event Color Key",default_value = False,callback=self.toggle_event_legend)
                                with dpg.group(horizontal=False,tag = self.t("event_legend_group"), show=False):
                                    with dpg.group(horizontal = True):
                                        dpg.add_text("[BLUE]", color=EVENT_COLORS["live"])
                                        dpg.add_text("Live on/off")
                                    with dpg.group(horizontal=True):
                                        dpg.add_text("[GREEN]", color=EVENT_COLORS["record"])
                                        dpg.add_text("Record start/stop")
                                    with dpg.group(horizontal=True):
                                        dpg.add_text("[ORANGE]", color=EVENT_COLORS["control"])
                                        dpg.add_text("Slider Gain / LED")
                                    with dpg.group(horizontal=True):
                                        dpg.add_text("[PURPLE]", color=EVENT_COLORS["stream"])
                                        dpg.add_text("Sample rate / Decimation")
                                    with dpg.group(horizontal=True):
                                        dpg.add_text("[PINK]", color=EVENT_COLORS["uv"])
                                        dpg.add_text("LED Changes (Via Schedule)")

                        #One tab here which has all these automation controls
                        with dpg.tab(label="Recording", tag=self.t('recording_options')):
                            dpg.add_spacer(height=10)
                            dpg.add_text("Start Recording: ")
                            dpg.add_separator()
                            dpg.add_input_float(label="", width=200, default_value=30, min_value=1.0, max_value=3600.0, callback=self.update_recording_duration)
                            dpg.add_text("Recording Duration (s)")
                            dpg.add_spacer(height=10)
                            dpg.add_separator()
                            dpg.add_text("Add Recording Segments: ")
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
                            dpg.add_text("", tag=self.t("filename"))
                            dpg.add_separator()
                            dpg.add_button(label="START", tag=self.t("start_button"), callback=self.start_recording)

                with dpg.child_window(width=-1, height=-65, tag=self.t("plot_panel"), show=True):
                    dpg.configure_item(self.t("plot_panel"), show=True)
                    with dpg.group(horizontal=True, tag=self.t("plot_header_controls"), show=True):
                        dpg.add_input_int(label="Plot Window (s)", width=100, default_value=10, min_value=1, max_value=60, tag=self.t("plot_window_input"), callback=self.update_plot_window_s)
                        dpg.add_combo(label="Select Bottom Right Channel", width=300, items=["CH3 (VIS Current)", "CH4 (IR Current)"], default_value="CH3 (VIS Current)", callback=self.toggle_plots, tag=self.t("bottom_right_combo"))
                    with dpg.group(tag=self.t("plot_area"), show=True):
                        with dpg.group(tag=self.t("plot_staging"), show=True):
    
                            # Create the blue theme once before the loop
                            with dpg.theme(tag=self.t("blue_line_theme")):
                                with dpg.theme_component(dpg.mvLineSeries):
                                    # Using the same RGBA blue fro dictionary
                                    dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 102, 204, 255), category=dpg.mvThemeCat_Plots)

                            for i in range(4):
                                ch = CH_TAGS[i]
                                with dpg.group(tag=self.t(f"wrap_{ch}"), show=True):
                                    with dpg.plot(label=CH_NAMES[i], height=300, width=-1, tag=self.t(f"plot_{ch}")):
                                        dpg.add_plot_legend()
                                        dpg.add_plot_axis(dpg.mvXAxis, label="time (s)", tag=self.t(f"{ch}_x_axis"))
                                        with dpg.plot_axis(dpg.mvYAxis, label="Volts", tag=self.t(f"{ch}_y_axis")):
                                            
                                            #add the line series
                                            series_tag = self.t(f"{ch}_series")
                                            dpg.add_line_series([], [], label=CH_NAMES[i], tag=series_tag)
                        
                                            #Bind the blue theme to the series we just created
                                            dpg.bind_item_theme(series_tag, self.t("blue_line_theme"))
                        with dpg.group(tag=self.t("plot_container"), show=True):
                            pass

            self._layout_plots()

    #Basic info
    def set_animal_id(self, sender, app_data, user_data):
        self.animal_id = app_data

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
            self.recorder.save_directory = folder
            dpg.set_value(self.t("save_dir_display"), f"Saving to: {folder}")

    def refresh_path(self):
        self.date = datetime.now().strftime("%m%d%Y_%H%M")
        
        c = self.app.master.cohort if self.app.master.cohort else ""
        a = self.animal_id if self.animal_id else ""
        tl = self.app.master.test_label if self.app.master.test_label else ""
        
        dpg.set_value(self.t("filename"), f"{c}_{a}_{tl}_{self.date}_Pupil")
        
    # Connection /Hardware Control Buttons

    def view_ports(self):
        dpg.delete_item(self.t('com_port_group'), children_only=True)
        dpg.add_text('Connect to COM Port:', parent=self.t('com_port_group'))
        dpg.add_separator(parent=self.t('com_port_group'))
        dpg.add_button(label='Refresh Ports', parent=self.t('com_port_group'), callback=self.refresh_ports)
        availablePortsStrings = self.daq.get_available_ports()
        if availablePortsStrings:
            for port in availablePortsStrings:
                dpg.add_button(label=port, parent=self.t('com_port_group'), user_data=port, callback=self.connect_port,tag =self.t(f"connect_{port}"))
        else:
            dpg.add_text('No COM Ports detected', parent=self.t('com_port_group'))

    def refresh_ports(self, sender=None, app_data=None, user_data=None):
        self.view_ports()

    def connect_port(self, sender, app_data, user_data):
        self.daq.connect(user_data)
        dpg.configure_item(self.t(f"connect_{user_data}"), label=f"{user_data} (Connected)")

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
            self.slider_cmds[user_data][1](slider_value)
            self.record_event(f"{user_data}={slider_value}", value=slider_value, event_type="control")

    # Plotting
    def update_plot_window_s(self, sender, app_data, user_data):
        self.plot_window_s = app_data

    def _plot_time(self, host_time=None):
        if host_time is None:
            host_time = time.time()
        if self.t0 is None:
            return 0.0
        return host_time - self.t0

    def _add_event_line(self, label, host_time, color, event_type, thickness=1.0):
        x_value = self._plot_time(host_time)
        for ch in CH_TAGS:
            if not dpg.does_item_exist(self.t(f"plot_{ch}")):
                continue
            line_tag = self.t(f"{ch}_event_{len(self._plot_event_line_tags[ch])}")
            dpg.add_drag_line(
                parent=self.t(f"plot_{ch}"),
                tag=line_tag,
                label=label,
                default_value=x_value,
                color=color,
                thickness=thickness,
                show_label=True,
                vertical=True,
                no_inputs=True,
            )
            self._plot_event_line_tags[ch].append(line_tag)

    def record_event(self, message, value=None, event_type="control", host_time=None, write_to_csv=True, thickness=2.0):
        if host_time is None:
            host_time = time.time()
        if value is None:
            label = message
        else:
            label = f"{message}={value}"
        color = EVENT_COLORS.get(event_type, EVENT_COLORS["control"])
        self._add_event_line(label, host_time, color, event_type, thickness=thickness)
        if write_to_csv and self.is_recording and self.recorder.csv_writer:
            self.recorder.write_row(event=label)

    def update_plots(self, volts, host_time):
        '''
        update the plots as data comes in
        '''
        if self.t0 is None:
            self.t0 = host_time

        t = host_time - self.t0
        self.times.append(t)
        for i in range(4):
            self.ch_data[i].append(volts[i])

        cutoff = t - self.plot_window_s
        while self.times and self.times[0] < cutoff:
            self.times.pop(0)
            for i in range(4):
                self.ch_data[i].pop(0)

        for i, ch in enumerate(CH_TAGS):
            dpg.set_value(self.t(f"{ch}_series"), [self.times, self.ch_data[i]])
            if t > self.plot_window_s:
                dpg.set_axis_limits(self.t(f"{ch}_x_axis"), cutoff, t)
            else:
                dpg.set_axis_limits(self.t(f"{ch}_x_axis"), 0, self.plot_window_s)
            dpg.fit_axis_data(self.t(f"{ch}_y_axis"))

    def process_serial_line(self, line):
        '''
        save data we received from DAQ so we can update plots, also save with write_row from save_recording.py if we are recording
        '''
        parsed = self.daq.handle_stream_line(line)
        if parsed is None:
            return

        raw, volts = parsed
        self.update_plots(volts, time.time())

        if self.is_recording:
            self.recorder.write_row(raw)

    def toggle_plots(self, sender, app_data, user_data):
        if app_data == "CH3 (VIS Current)":
            self.ch4_active = False
        elif app_data == "CH4 (IR Current)":
            self.ch4_active = True
        self._layout_plots()

    def _layout_plots(self):
        '''
        layout the plots in a 2x2 grid, with IR PD permanently occupying top 2, VIS PD permanently bottom left. 
        Bottom right can be selected

        This part is one of the hardest to read, but is necessary to achieve a flexible layout
        I don't recommend editing unless you are familiar with all the tags, and how tables, columns, and rows function. 
        '''
        dpg.configure_item(self.t("plot_panel"), show=True)
        dpg.configure_item(self.t("plot_area"), show=True)
        dpg.configure_item(self.t("plot_staging"), show=True)
        dpg.configure_item(self.t("plot_container"), show=True)
        dpg.configure_item(self.t("bottom_right_combo"), show=True)

        for ch in CH_TAGS: #this acts as a reset so previous graphs are no longer showing
            dpg.move_item(self.t(f"wrap_{ch}"), parent=self.t("plot_staging"))
            dpg.configure_item(self.t(f"wrap_{ch}"), show=False)

        dpg.delete_item(self.t("plot_container"), children_only=True)
        #Top table with only one column, spanned by ch1
        top_table = dpg.add_table(parent=self.t("plot_container"), header_row=False)
        dpg.add_table_column(parent=top_table)
        top_row = dpg.add_table_row(parent=top_table)
        dpg.move_item(self.t("wrap_ch1"), parent=top_row)
        dpg.configure_item(self.t("wrap_ch1"), show=True)
        dpg.configure_item(self.t("plot_ch1"), width=-1, height=300)

        #Bottom table has two columns, so we can have ch2 on the left, and condition to have ch3 or 4 on right. they split the area evenly, which is caused by there being two columns.
        bottom_table = dpg.add_table(parent=self.t("plot_container"), header_row=False)
        dpg.add_table_column(parent=bottom_table)
        dpg.add_table_column(parent=bottom_table)
        bottom_row = dpg.add_table_row(parent=bottom_table)
        dpg.move_item(self.t("wrap_ch2"), parent=bottom_row)
        dpg.configure_item(self.t("wrap_ch2"), show=True)
        dpg.configure_item(self.t("plot_ch2"), width=-1, height=300)
        if self.ch4_active:
            dpg.move_item(self.t("wrap_ch4"), parent=bottom_row)
            dpg.configure_item(self.t("wrap_ch4"), show=True)
            dpg.configure_item(self.t("plot_ch4"), width=-1, height=300)
        else:
            dpg.move_item(self.t("wrap_ch3"), parent=bottom_row)
            dpg.configure_item(self.t("wrap_ch3"), show=True)
            dpg.configure_item(self.t("plot_ch3"), width=-1, height=300)

    def live_plot_toggle(self, sender, app_data, user_data):
        '''
        Turn streaming on or off
        '''
        self.is_live = not self.is_live
        label = "ON" if self.is_live else "OFF"
        dpg.configure_item(self.t("live_button"), label=label)
        if self.is_live:
            self.daq.set_adc_streaming(True)
            self.daq.set_adc_stream_decimation(int(dpg.get_value(self.t("stream_decimation_input"))))
            self.daq.set_sample_rate(int(dpg.get_value(self.t("sample_rate_input"))))
            self.daq.start_device()
            self.record_event("LIVE_ON", value=1, event_type="live")
        else:
            self.daq.set_adc_streaming(False)
            self.daq.stop_device()
            self.record_event("LIVE_OFF", value=0, event_type="live")

    # Recording Control
   
    def start_recording(self, sender, app_data, user_data):
        '''
        When the start button is pressed, this callback function is triggered the recording is initiated.
        Despite function being named start recording, after pressing Start that button turns into a Stop,
        which the user can click again to end the recording prematurely

       settings to the recording are retrieved from input fields via dpg.get_value
        '''
        name = dpg.get_value(self.t("filename"))
        
        if not name:
            return

        if not self.recorder.save_directory or not os.path.isdir(self.recorder.save_directory):
            dpg.delete_item(self.t("Confirm info"), children_only=True)
            dpg.add_text("Error: Please select a save location first!", parent=self.t("Confirm info"))
            return

        self.recorder.file_name = os.path.join(self.recorder.save_directory, name)

        self.is_recording = not getattr(self, 'is_recording', False)
        if self.is_recording:
            self.start_time = time.time()
            self.record_event("RECORDING_START", event_type="record")
        else:
            self.record_event("RECORDING_STOP", event_type="record")
        label = "STOP" if self.is_recording else "START"
        try:
            dpg.configure_item(self.t('start_button'), label=label)
        except Exception:
            pass

        if self.is_recording:
            self.prepare_recording()
            if self.no_overlap:
                try:
                    self.recorder.open_csv()
                except OSError as e:
                    dpg.delete_item(self.t("Confirm info"), children_only=True)
                    dpg.add_text(f"Error: Cannot create file - {e}", parent=self.t("Confirm info"))
                    self.is_recording = False
                    dpg.configure_item(self.t('start_button'), label='START')
                    return
                #capture current settings for json file
                self.recorder.write_metadata_sidecar({
                    "date": self.date,
                    "cohort": self.app.master.cohort or "",
                    "animal_id": self.animal_id or "",
                    "test_label": self.app.master.test_label or "",
                    "recording_duration": self.recording_duration,
                    "sample_rate": dpg.get_value(self.t("sample_rate_input")),
                    "decimation": dpg.get_value(self.t("stream_decimation_input")),
                    "vis_pd_gain": dpg.get_value(self.t("s_VIS PD Gain")),
                    "ir_pd_gain": dpg.get_value(self.t("s_IR PD Gain")),
                    "vis_led_dac": dpg.get_value(self.t("s_VIS LED Gain")),
                })
                self.upload_schedule_to_daq()
            else:
                self.is_recording = False
                try:
                    dpg.configure_item(self.t('start_button'), label='START')
                except Exception:
                    pass
        else:
            self.daq.stop_vis_schedule()
            self.recorder.close_csv()

    def update_recording_duration(self, sender, app_data, user_data):
        self.recording_duration = app_data

    def add_recording_segment(self, app_data, user_data):
        #add a new segment under custom recording controls, where you can set start time, stop time, and the gain during that period
        self.segment_counter += 1
        sc = self.segment_counter
        row_tag = self.t(f"row_{sc}")
        self.active_rows.append((row_tag, sc))

        with dpg.group(horizontal=False, parent=self.t("protocol_group"), tag=row_tag):
            dpg.add_separator()
            dpg.add_input_int(label="Start (s)", width=100, step=0, tag=self.t(f"start_{sc}"))
            dpg.add_input_int(label="End (s)", width=100, step=0, tag=self.t(f"end_{sc}"))
            dpg.add_input_int(label="UV Val", width=100, step=0, tag=self.t(f"uv_{sc}"))
        
        
            dpg.add_button(label=" X ", user_data=row_tag, callback=self.delete_segment)

    def delete_segment(self, sender, app_data, user_data):
        #delete when pressing the X button
        self.active_rows = [(rt, sc) for rt, sc in self.active_rows if rt != user_data]
        dpg.delete_item(user_data)

    def prepare_recording(self):
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

    def upload_schedule_to_daq(self):
        if not self.daq.is_open:
            return
        self.daq.clear_vis_schedule()
        for i in range(len(self.time_stamps)):
            start_s, end_s = self.time_stamps[i]
            uv_val = self.light_values[i]
            self.daq.append_schedule_step(start_s, uv_val)
            self.daq.append_schedule_step(end_s, 0)
            self.record_event("UV", value=uv_val, event_type="uv", host_time=self.start_time + start_s)
            self.record_event("UV", value=0, event_type="uv", host_time=self.start_time + end_s)
        self.daq.start_vis_schedule()

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
        self.ttl_condition = 'below' if self.ttl_drops_below else 'above'

    def set_trigger_option(self, sender, app_data, user_data):
        if user_data == 'send':
            self.send_output = app_data
        elif user_data == 'wait':
            self.wait_for_input = app_data

    def set_stream_decimation(self, sender, app_data, user_data):
        value = max(1, int(app_data))
        self.daq.set_adc_stream_decimation(value)
        self.record_event("STREAM_DECIMATION", value=value, event_type="stream")

    def set_sample_rate(self, sender, app_data, user_data):
        value = max(10, min(250, int(app_data)))
        self.daq.set_sample_rate(value)
        self.record_event("SAMPLE_RATE", value=value, event_type="stream")
 
    # general

    def toggle_event_legend(self, sender, app_data, user_data):
        show = app_data
        dpg.configure_item(self.t("event_legend_group"), show=show)

    def hardware_thread(self):
        while self.running:
            self.refresh_path()
            
            if self.is_recording and self.recording_duration > 0:
                if (time.time() - self.start_time) >= self.recording_duration:
                    self.stop_recording_automatically()
            
            if self.is_live and self.daq.is_open and self.daq.serial is not None:
                try:
                    while self.daq.serial.in_waiting > 0:
                        line = self.daq.serial.readline()
                        self.process_serial_line(line)
                except Exception:
                    pass
            time.sleep(0.01)

    def stop_recording_automatically(self):
        self.is_recording = False
        self.daq.stop_vis_schedule()
        self.recorder.close_csv()
        dpg.configure_item(self.t('start_button'), label='START')
