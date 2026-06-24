import dearpygui.dearpygui as dpg
import threading
import time
from daq import DAQController

class GUI:
    def __init__(self):
        self.daq = DAQController()
        self.is_live = False
        self.running = True
        
        # plot Data Arrays
        self.x_data = []
        self.y_data = []
        self.max_points = 5000 
        
        # setup DearPyGui Context
        dpg.create_context()
        self.build_ui()
        dpg.create_viewport(title='Pégard and Rodriguez Romaguera Labs', width=1000, height=800)
        dpg.setup_dearpygui()
        
        # start background worker for serial comms
        threading.Thread(target=self.hardware_thread, daemon=True).start()
