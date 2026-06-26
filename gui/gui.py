import dearpygui.dearpygui as dpg
import threading
import time
#from daq import DAQController  (Will implement tis later)

VIS_PD_MAX = 255
IR_PD_MAX = 255
VIS_LED_MAX = 4095


class GUI:
    def __init__(self):
        #self.daq = DAQController()
        self.is_live = False
        self.running = True
        
        self.x_data = []
        self.y_data = []
        self.max_points = 5000 
        
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
                            dpg.add_slider_int(label="IR LED Blink", max_value=1000, width=200) 
                            dpg.add_slider_int(label="VIS PD Gain", max_value=VIS_PD_MAX, width=200) 
                            dpg.add_slider_int(label="IR PD Gain", max_value=IR_PD_MAX, width=200) 
                            dpg.add_slider_int(label="VIS LED Gain", max_value=VIS_LED_MAX, width=200) 
                        #One tab here which has all these automation controls
                        with dpg.tab(label="Automation"):
                            dpg.add_spacer(height=10)
                            dpg.add_text("Timing Controls")
                            dpg.add_separator()
                            dpg.add_spacer(height=30)
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