import dearpygui.dearpygui as dpg
import threading
import time
from daq import DAQController  

VIS_PD_MAX = 255
IR_PD_MAX = 255
VIS_LED_MAX = 4095

class GUI:
    def __init__(self):
        self.daq = DAQController()
        self.is_live = False
        self.running = True

        self.file_path = ""
        
        self.x_data = []
        self.y_data = []
        self.max_points = 5000 

        self.light_values = []
        self.time_stamps = []
        self.recording_duration = 0.0
        self.active_rows = []
        self.is_recording = False
        self.ttl_drops_below = True


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
        
        dpg.create_context()
        self.build_ui()
        dpg.create_viewport(title='Pégard and Rodriguez Romaguera Labs', width=1000, height=800)
        dpg.setup_dearpygui()
        
        threading.Thread(target=self.hardware_thread, daemon=True).start()

    def build_ui(self):
        '''
        The main function where we start dpg,
        and build the layout so to speak

        Everything here should be readable without comments, and DPG was chosen for this reason
        to allow easy manipulation of the layout via a CODE interface, 
        and this easily separates  hardware commands code (in daq.py) from code for the GUI "frontend"or visual elements
        '''
        with dpg.window(tag="main window", width=1000, height=800):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=350, height=-65):
                    with dpg.tab_bar():
                        #One tab here for each slider,this page has sliders and has stuff from before, custom controls are in other tab
                        with dpg.tab(label="Slider Controls"):
                            dpg.add_separator()
                            dpg.add_spacer(height=10)
                            with dpg.group(tag ='com_port_group'):
                                self.view_ports()
                            dpg.add_spacer(height=10)
                            dpg.add_separator()
                            dpg.add_spacer(height=10)
                            dpg.add_slider_int(label="IR LED Blink", max_value=1000, width=200, callback=self.on_slider_changed) 
                            dpg.add_slider_int(label="VIS PD Gain", max_value=VIS_PD_MAX, width=200, callback=self.on_slider_changed) 
                            dpg.add_slider_int(label="IR PD Gain", max_value=IR_PD_MAX, width=200, callback=self.on_slider_changed) 
                            dpg.add_slider_int(label="VIS LED Gain", max_value=VIS_LED_MAX, width=200, callback=self.on_slider_changed)
                            dpg.add_spacer(height=20)
                            dpg.add_separator()
                            dpg.add_text("LIVE")
                            dpg.add_button(label="OFF", tag = "live_button",callback = self.live_plot_toggle) 
                            dpg.add_separator()
                        #One tab here which has all these automation controls
                        with dpg.tab(label="Recording Options"):
                            dpg.add_spacer(height=10)
                            dpg.add_text("Start Recording: ")
                            dpg.add_separator()
                            dpg.add_input_float(label = "Duration (s)", width = 200, callback=self.update_recording_duration)
                            dpg.add_spacer(height=10)
                            dpg.add_text("Add Recording Segments: ")
                            dpg.add_separator()
                            dpg.add_button(label="Add Segment", callback=self.add_recording_segment)
                            # The group will then appear here
                            with dpg.group(tag="protocol_group"):
                                dpg.add_text("")
                            dpg.add_button(label = "Save Recording Settings",callback=self.prepare_recording)
                            with dpg.group(tag = "Confirm info"):
                                dpg.add_text("")
                            dpg.add_spacer(height=10)

                            dpg.add_input_text(label = "File path",tag = "filepath")
                            dpg.add_button(label="START", tag="start_button", callback=self.start_recording)
                            dpg.add_separator()

                            dpg.add_text("TTL Outputs")
                            dpg.add_separator()
                            dpg.add_checkbox(label = "Enable Closed Loop TTL",default_value = False, callback = self.show_TTL_options)
                            with dpg.group(tag = 'ttl_group',horizontal = True):
                                pass

                            

                with dpg.child_window(width=-1, height=-65):
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(label="IR Light", default_value=True, callback=self.toggle_plots, tag="cb_ir")
                        dpg.add_checkbox(label="VIS Light", default_value=True, callback=self.toggle_plots, tag="cb_vis")
                    
                    with dpg.plot(label="IR Sensor Data", height=350, width=-1, tag="plot_ir"):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="time (s)")
                        with dpg.plot_axis(dpg.mvYAxis, label="Sensor Value"):
                            dpg.add_line_series(self.x_data, self.y_data, label="IR Data")

                    with dpg.plot(label="VIS Sensor Data", height=350, width=-1, tag="plot_vis"):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="time (s)")
                        with dpg.plot_axis(dpg.mvYAxis, label="sensor Value"):
                            dpg.add_line_series(self.x_data, self.y_data, label="VIS data")

    # Connection / Hardware Control Buttons

    def view_ports(self):
        dpg.add_text('Connect to COM Port:', parent='com_port_group')
        dpg.add_separator(parent='com_port_group')
        availablePortsStrings = self.daq.get_available_ports()
        if availablePortsStrings:
            for port in availablePortsStrings:
                dpg.add_button(
                    port,
                    parent='com_port_group',
                    user_data=port,
                    callback=self.connect_port,
                )
        else:
            dpg.add_text('No COM Ports detected', parent='com_port_group')
            #Potentially: refresh button right here

    def connect_port(self, sender, app_data, user_data):
        self.daq.connect(user_data)

    # Slider Control
   
    def on_slider_changed(self, sender, app_data, user_data):
        '''
        This function is called whenever a slider is moved, and sends appropriate command over serial 
        (send_command function handled in daq.py)
        '''

        if sender == "IR LED Blink":
            print(f"IR LED Blink value: {app_data}")
            self.daq.pulse_ir_led(app_data)
        elif sender == "VIS PD Gain":
            print(f"VIS PD Gain value: {app_data}")
            self.daq.set_visible_pd_gain(app_data)
        elif sender == "IR PD Gain":
            print(f"IR PD Gain value: {app_data}")
            self.daq.set_ir_pd_gain(app_data)
        elif sender == "VIS LED Gain":
            print(f"VIS LED Gain value: {app_data}")
            self.daq.set_vis_led_dac(app_data)

    # Plotting

    def toggle_plots(self, sender, app_data, user_data):
        '''
        this function allows us to view either IR or VIS, or both simultaneously
        with checkbox logic
        '''
        ir_checked = dpg.get_value("cb_ir")
        vis_checked = dpg.get_value("cb_vis")
        
        if ir_checked and vis_checked:
            dpg.configure_item("plot_ir", show=True, height=350)
            dpg.configure_item("plot_vis", show=True, height=350)
        elif ir_checked:
            dpg.configure_item("plot_ir", show=True, height=-1)
            dpg.configure_item("plot_vis", show=False)
        elif vis_checked:
            dpg.configure_item("plot_ir", show=False)
            dpg.configure_item("plot_vis", show=True, height=-1)
        else:
            dpg.configure_item("plot_ir", show=False)
            dpg.configure_item("plot_vis", show=False)

    def live_plot_toggle(self, sender, app_data, user_data):
        self.is_live = not self.is_live
        label = "ON" if self.is_live else "OFF"
        dpg.configure_item("live_button", label=label)
        if self.is_live:
            self.daq.start_device()
        else:
            self.daq.stop_device()

    # Recording Control
   
    def start_recording(self, sender, app_data, user_data):
        '''
        When the start button is pressed, this callback function is triggered the recording is initiated.
        Despite function being named start recording, after pressing Start that button turns into a Stop,
        which the user can click again to end the recording prematurely

       settings to the recording are retrieved from input fields via dpg.get_value
        '''
        self.file_path = dpg.get_value("filepath")
        self.is_recording = not getattr(self, 'is_recording', False)
        label = "STOP" if self.is_recording else "START"
        try:
            dpg.configure_item('start_button', label=label)
        except Exception:
            pass
        if self.is_recording:
            self.prepare_recording()
            if self.no_overlap:
                self.upload_schedule_to_daq()
            else:
                self.is_recording = False
                try:
                    dpg.configure_item('start_button', label='START')
                except Exception:
                    pass
        else:
            self.daq.stop_vis_schedule()
            self.daq.stop_device()

    def update_recording_duration(self, sender, app_data, user_data):
        self.recording_duration = app_data

    def add_recording_segment(self, app_data, user_data):
        #add a new segment under custom recording controls, where you can set start time, stop time, and the gain during that period
        self.segment_counter+=1
        row_tag = f"row_{self.segment_counter}"
        self.active_rows.append(row_tag)

        with dpg.group(horizontal=True, parent="protocol_group", tag=row_tag):
            dpg.add_separator()
            dpg.add_input_int(label="Start (s)", width=100, step=0, tag=f"start_{self.segment_counter}")
            dpg.add_input_int(label="End (s)", width=100, step=0, tag=f"end_{self.segment_counter}")
            dpg.add_input_int(label="UV Val", width=100, step=0, tag=f"uv_{self.segment_counter}")
        
        
            dpg.add_button(label=" X ", user_data=row_tag, callback=self.delete_segment)

    def delete_segment(self, sender, app_data, user_data):
        #delete when pressing the X button
        if user_data in self.active_rows:
            self.active_rows.remove(user_data)
        dpg.delete_item(user_data)

    def prepare_recording(self):
        dpg.delete_item("Confirm info", children_only=True)
        self.time_stamps.clear()
        self.light_values.clear()

        self.check_overlaps()

        for row_id in self.active_rows:
            row_num = row_id.split("_")[-1]
            start_val = dpg.get_value(f"start_{row_num}")
            end_val = dpg.get_value(f"end_{row_num}")
            uv_val = dpg.get_value(f"uv_{row_num}")
            self.time_stamps.append((start_val, end_val))
            self.light_values.append(uv_val)

        if self.no_overlap:
            dpg.add_text(f"Recording Duration: {self.recording_duration}", parent="Confirm info")
            for i in range(len(self.light_values)):
                dpg.add_text(
                    f"Segment {i+1}: Value of {self.light_values[i]} from time {self.time_stamps[i][0]} s to time {self.time_stamps[i][1]} s",
                    parent="Confirm info"
                )
        else:
            dpg.add_text("Error - overlapping time segments", parent="Confirm info")

    def upload_schedule_to_daq(self):
        '''
        Upload the schedule to the daq in a good format for the commands
        reads all segments from that little table
        so the schedule can be excecuted in steps via start_vis_schedule
        '''
        if not self.no_overlap:
            return False

        self.daq.clear_vis_schedule()
        schedule_events = []

        for row_id in self.active_rows:
            row_num = row_id.split("_")[-1]
            start_val = dpg.get_value(f"start_{row_num}")
            end_val = dpg.get_value(f"end_{row_num}")
            uv_val = dpg.get_value(f"uv_{row_num}")
            if start_val is None or end_val is None:
                continue
            schedule_events.append((float(start_val), int(uv_val)))
            schedule_events.append((float(end_val), 0))

        schedule_events.sort(key=lambda x: x[0])
        for time_s, dac_code in schedule_events:
            self.daq.append_schedule_step(int(time_s), int(dac_code))

        self.daq.start_vis_schedule()
        self.daq.start_device()
        return True

    def check_overlaps(self):
        '''
        little function just to protect against mistakes by the user
        if they enter overlapping segments
        '''
        intervals = []
        for row_id in self.active_rows:
            row_num = row_id.split("_")[-1]
            start_val = dpg.get_value(f"start_{row_num}")
            end_val = dpg.get_value(f"end_{row_num}")
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
                dpg.delete_item('ttl_group', children_only=True)
            except Exception:
                pass
            return
        dpg.add_text("If IR Light", parent='ttl_group')
        dpg.add_button(label='Drops Below', tag='ttl_direction_button', callback=self.toggle_ttl_direction, parent='ttl_group')
        dpg.add_input_float(tag='ir_value', parent='ttl_group')

    def toggle_ttl_direction(self, sender, app_data, user_data):
        '''
        Toggles button between saying Drops Below and Goes Above
        '''
        self.ttl_drops_below = not getattr(self, 'ttl_drops_below', True)
        label = 'Drops Below' if self.ttl_drops_below else 'Goes Above'
        try:
            dpg.configure_item('ttl_direction_button', label=label)
        except Exception:
            pass
        self.ttl_condition = 'below' if self.ttl_drops_below else 'above'
 
    # general

    def hardware_thread(self):
        while self.running:
            time.sleep(0.1)

    def run(self):
        dpg.set_primary_window("main window", True)
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    app = GUI()
    app.run()


    '''
    TO DO Here another time!!! 
    Decimation from Kam's Github
    Learn more about input output triggers and how to best integrate
    confirm that my setup with the closed loop TTL idea is correct.
    '''