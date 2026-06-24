import serial
from serial.tools import list_ports
import time
from datetime import datetime

class DAQController:
    def __init__(self):
        self.serial = None
        self.is_open = False
        self.command_queue = []
        self.buff = None
        self.is_writing = False

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

    def send_command(self, cmd_id, value):
        if self.is_open:
            ## comments start new
            self.command_queue.append((cmd_id, value))
            ## comments end new

    def process_command_queue(self):
        ## comments start new
        while self.command_queue:
            cmd_id, val = self.command_queue.pop(0)
            self.is_writing = True
            try:
                msg = f"{cmd_id},{val}\n"
                self.serial.write(msg.encode())
                time.sleep(0.01)
            except Exception as e:
                print(f"Queue send error: {e}")
            finally:
                self.is_writing = False
        ## comments end new

    def read(self):
        """
        new logic to read the csvs that we are receiving:
        1 read high line (LED ON)
        2 read low line (LED OFF)
        3 subtract to get Clean Signal.
        """
        if self.is_open:
            try:
                line1 = self.serial.readline().decode().strip()# high vals
                if not line1:
                    return None# If we timed out, exit early

                line2 = self.serial.readline().decode().strip() # low vals
                if not line2:
                    return None  #If we timed out on line 2, exit early
            except Exception as e:
                print(f"Read error: {e}")
                return None

            # Split CSV
            high_vals = [int(v) for v in line1.split(',') if v.strip().isdigit()]
            low_vals = [int(v) for v in line2.split(',') if v.strip().isdigit()]

            if len(high_vals) >= 4 and len(low_vals) >= 4:
                # subtract low from high for clean signal, new firmware prepared for this
                subtracted = high_vals[0]# - low_vals[0] COMMENTING OUT JUST TO TEST OUTPUT
                
                #5 Volt range, 16-bit signed int after subtraction, so we can convert to volts like this. seen as transfer function from new ADC, 
                #found all this in the datasheet.
                volts = (subtracted / 32768.0) * 5.0
                return (volts,subtracted) #returning both volts and subtracted value for more flexibility in saving

    def toBin(self):
        date = datetime.now().strftime("%m-%d-%Y-%H-%M")
        filename = str(date + ".bin")
        if self.is_open and self.buff is not None:
            with open(filename, 'wb') as file:
                for data in self.buff:
                    # self.buff now stores (volts, raw (named subtracted)), so save the raw 16-bit number for storage in two bytes
                    _, subtracted = data
                    file.write(int(subtracted).to_bytes(2, byteorder='big', signed=True))
            return "Data saved to bin file"
        elif self.is_open and self.buff is None:
            return "Buffer is empty."
        else:
            return "Serial Port is not open."

    def twos_comp(self, val, bits):
        '''
        
        getting twos comp into 
        '''
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    def turn_off(self):
        if self.is_open:
            self.send_command(0, 0) # turn device off first
            self.serial.close()
            self.is_open = False