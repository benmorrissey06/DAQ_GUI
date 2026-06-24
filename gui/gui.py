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
        
        # plot data arrays
        self.x_data = []
        self.y_data = []
        self.max_points = 5000 
        
        #  setup DearPyGui Context
        dpg.create_context()
        self.build_ui()
        dpg.create_viewport(title='Pégard and Rodriguez Romaguera Labs', width=1000, height=800)
        dpg.setup_dearpygui()
        
        # start background worker for serial comms
        threading.Thread(target=self.hardware_thread, daemon=True).start()

    def build_ui(self):
        with dpg.window(Label="DAQ GUI", width=1000,height=800):
            with dpg.child_window(width=350,height=-65):
                with dpg.tab_bar():
                    with dpg.tab(label="Slider Controls"):
                        dpg.add_spacer(height=10)
                        dpg.add_separator()
                        dpg.add_spacer(height=10)
                        dpg.add_slider_int(label="IR LED Blink", max_value = 1000, width = 200) #this may not be a slider in the future, it controls a blink not a gain like the others, but placeholder for now
                        dpg.add_slider_int(label="VIS PD Gain", max_value = VIS_PD_MAX, width = 200) 
                        dpg.add_slider_int(label="IR PD Gain", max_value = IR_PD_MAX, width = 200) 
                        dpg.add_slider_int(label="VIS LED Gain", max_value = VIS_LED_MAX, width = 200) 

                        #possibly place triggers here?
            with dpg.child_window(width =-1,height = -65):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="IR Light", default_value = True)
                    dpg.add_checkbox(label="VIS Light", default_value = True)
                with dpg.subplots(2,1,width=-1,height=-1):
                    with dpg.plot(label="sensor data"):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
                        with dpg.plot_axis(dpg.mvYAxis, label="Sensor Value"):
                            self.line_series = dpg.add_line_series(self.x_data, self.y_data, label="Sensor Data", parent=dpg.last_item())
