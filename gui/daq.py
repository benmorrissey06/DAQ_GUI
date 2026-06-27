import serial
from serial.tools import list_ports
import time
from datetime import datetime

class DAQController:
    def __init__(self):
        self.serial = None
        self.is_open = False

        #NOT SURE YET IF WE NEED THESE!
        #self.command_queue = []
        #self.buff = None
        #self.is_writing = False

    def get_available_ports(self):
        availablePorts = serial.tools.list_ports.comports()
        availablePortsStrings = []
        for a in availablePorts:
            availablePortsStrings.append(str(a.device))
        return availablePortsStrings
    
    def connect(self, port_name):
        try:
            self.serial = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=0.01,
                write_timeout=1.0,  # Allow enough time for a command to be written
            )
            self.is_open = self.serial.isOpen()
            return True
        except Exception as e:
            print(e)
            return False

    def turn_off(self):
        if self.is_open:
            self.send_command(0, 0) # turn device off first
            self.serial.close()
            self.is_open = False

    def start_live_chart(self):
        if not self.is_live and self.is_open:
            self.running = True
            # command 0,1 starts the device in firmware
            self.send_command(0, 1)
            '''
            Insert code for chart here
            '''
            self.is_live = True
        elif self.is_open:
            self.is_live = False
            self.running = False
            # command 0,0 stops the device in firmware
            self.send_command(0, 0)
        else:
            self.textBox.setText("Serial Port is not open.")