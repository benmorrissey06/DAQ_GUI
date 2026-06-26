import dearpygui.dearpygui as dpg
import threading
import time
#from daq import DAQController  (Will implement tis later)
'''
currently commenting out all DAQ references so we can test GUI before that is finished.
'''
VIS_PD_MAX = 255
IR_PD_MAX = 255
VIS_LED_MAX = 4095

class GUI:
    def __init__(self):
        #self.daq = DAQController()
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

        #When implementing custom recording controls, this labels each segment of time
        self.segment_counter = 1
        #Whether or not there is an overlap in the segments, will be function to determine
        self.no_overlap = True
        
        dpg.create_context()
        self.build_ui()
        dpg.create_viewport(title='Pégard and Rodriguez Romaguera Labs', width=1000, height=800)
        dpg.setup_dearpygui()
        
        threading.Thread(target=self.hardware_thread, daemon=True).start()

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

    def start_recording(self,sender,app_data,user_data):
        self.file_path=dpg.get_value("filepath") #Save filepath, maybe have file expolorer open instead?
        pass
        #self.daq.begin_recording()
    '''
    This function is unnecessary once we have prepare_recording
    def store_segment(self,sender,app_data,user_data):
        self.time_stamps.clear()
        self.light_values.clear()
        
        for row_id in self.active_rows:
            start_val = dpg.get_value(f"start_{row_id}")
            end_val = dpg.get_value(f"end_{row_id}")
            uv_val = dpg.get_value(f"uv_{row_id}")
            
            self.time_stamps.append((start_val, end_val))
            self.light_values.append(uv_val)
    '''
    def update_recording_duration(self, sender, app_data, user_data):
        self.recording_duration = app_data

    def delete_segment(self, sender, app_data, user_data):
        #delete when pressing the X button
        if user_data in self.active_rows:
            self.active_rows.remove(user_data)
        dpg.delete_item(user_data)
    

    def add_recording_segment(self, app_data, user_data):
        #add a new segment under custom recording controls
        self.segment_counter+=1
        row_tag = f"row_{self.segment_counter}"
        self.active_rows.append(row_tag)

        with dpg.group(horizontal=True, parent="protocol_group", tag=row_tag):
            dpg.add_separator()
            dpg.add_input_int(label="Start (s)", width=100, step=0, tag=f"start_{self.segment_counter}",callback = self.store_segment)
            dpg.add_input_int(label="End (s)", width=100, step=0, tag=f"end_{self.segment_counter}",callback =self.store_segment)
            dpg.add_input_int(label="UV Val", width=100, step=0, tag=f"uv_{self.segment_counter}",callback = self.store_segment)
        
        
            dpg.add_button(label=" X ", user_data=row_tag, callback=self.delete_segment)

    def prepare_recording(self):
        dpg.delete_item("Confirm info", children_only=True)
        self.time_stamps.clear()
        self.light_values.clear()

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


    def slider_callback(self, sender, app_data,user_data):
        '''
        This function is called whenever a slider is moved, and sends appropriate command over serial 
        (send_command function handled in daq.py)
        '''

        if sender == "IR LED Blink":
            print(f"IR LED Blink value: {app_data}")
            # self.daq.send_command(1, app_data) these are wrong for now placeholders, but will match to firmware
        elif sender == "VIS PD Gain":
            print(f"VIS PD Gain value: {app_data}")
            # self.daq.send_command(2, app_data)
        elif sender == "IR PD Gain":
            print(f"IR PD Gain value: {app_data}")
            # self.daq.send_command(3, app_data)
        elif sender == "VIS LED Gain":
            print(f"VIS LED Gain value: {app_data}")
            # self.daq.send_command(4, app_data)

    def build_ui(self):
        with dpg.window(tag="main window", width=1000, height=800):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=350, height=-65):
                    with dpg.tab_bar():
                        #One tab here for each slider
                        with dpg.tab(label="Slider Controls"):
                            dpg.add_spacer(height=10)
                            dpg.add_separator()
                            dpg.add_spacer(height=10)
                            dpg.add_slider_int(label="IR LED Blink", max_value=1000, width=200, callback=self.slider_callback) 
                            dpg.add_slider_int(label="VIS PD Gain", max_value=VIS_PD_MAX, width=200, callback=self.slider_callback) 
                            dpg.add_slider_int(label="IR PD Gain", max_value=IR_PD_MAX, width=200, callback=self.slider_callback) 
                            dpg.add_slider_int(label="VIS LED Gain", max_value=VIS_LED_MAX, width=200, callback=self.slider_callback) 
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
                            
                            dpg.add_button(label="START",callback=self.start_recording)
                            dpg.add_separator()
                            dpg.add_text("TTL Outputs")
                            dpg.add_separator()

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