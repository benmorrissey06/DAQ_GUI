import dearpygui.dearpygui as dpg
from master_tab import MasterTab
from device_tab import DeviceTab
import dearpygui_ext.themes as dpg_ext

'''
MAIN APPLICATION

THIS CREATES THE APPLICATION
it's short code that creates the main window and master tab, and allows for the creation of new device tabs via the + button.
'''

class MainGUI:
    def __init__(self):
        self.device_tabs = []
        self.tab_counter = 0
        self.master = None

        dpg.create_context()
        light_theme = dpg_ext.create_theme_imgui_light() #We must use light mode. This is where we set the theme.
        dpg.bind_theme(light_theme)
        self.build_ui()
        dpg.create_viewport(title='Pegard and Rodriguez Romaguera Labs', width=1200, height=800)
        dpg.setup_dearpygui()

    def build_ui(self):
        with dpg.window(tag="main window", width=1200, height=800):
            with dpg.tab_bar(tag="main_tab_bar"):
                self.master = MasterTab(self)
                dpg.add_tab_button(label="+", tag="add_tab_button", callback=self.add_device_tab)

    def add_device_tab(self, sender=None, app_data=None, user_data=None):
        self.tab_counter += 1
        tab = DeviceTab(self.tab_counter, "main_tab_bar", self)
        self.device_tabs.append(tab)

    def run(self):
        dpg.set_primary_window("main window", True)
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
