import serial
import sys
from serial.tools import list_ports
import time
from datetime import datetime
'''
HARDWARE
All serial communication code should be handled in this file
so, if there are any changes to the firmware, this file should be modified
'''

class DAQController:
    def __init__(self):
        self.serial = None
        self.is_open = False
        self.last_response = None
        self.is_live = False
        self.running = False
        self.vis_led_dac = 0

    def get_available_ports(self):
        return [port.device for port in list_ports.comports() if sys.platform == "win32" or port.vid is not None or port.device.startswith(("/dev/cu.usb", "/dev/tty.usb", "/dev/ttyUSB", "/dev/ttyACM"))]
        #^^ This part is since mac and linux show other ports outside of usb devices, so this filters them out
    def connect(self, port_name):
        try:
            connection = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=0.01,
                write_timeout=1.0,  # Allow enough time for a command to be written
            )
            self.disconnect() #close previous connections, the new one isnt stored as one until after, so it remains
            self.serial = connection
            self.is_open = connection.is_open

            return self.is_open, ""
        except Exception as e:
            error = str(e).lower()
            return False, "Access denied" if "denied" in error or "permission" in error else "Port unavailable" if "not found" in error or "cannot find" in error else "Connection failed"

    def disconnect(self):
        try:
            if self.serial is not None and self.serial.is_open:
                self.serial.close()
        except Exception:
            pass
        finally:
            self.serial = None
            self.is_open = False

    def send_command(self, command, value=None, value2=None, wait_for_response=False):
        if not self.is_open or self.serial is None:
            raise RuntimeError("Serial port is not open")

        if value is None:
            cmd = f"{command},0\n"
        elif value2 is None:
            cmd = f"{command},{value}\n"
        else:
            cmd = f"{command},{value},{value2}\n"

        try:
            self.serial.write(cmd.encode("utf-8"))
            self.serial.flush()
        except Exception as e:
            raise RuntimeError(f"DAQ write error: {e}")

        if wait_for_response:
            return self.read_response()
        return None

    def read_response(self, timeout=1.0):
        if not self.is_open or self.serial is None:
            return None
        deadline = time.time() + timeout
        line = b""
        while time.time() < deadline:
            if self.serial.in_waiting > 0:
                line = self.serial.readline()
                break
            time.sleep(0.01)
        try:
            text = line.decode("utf-8", errors="ignore").strip()
        except Exception:
            text = ""
        self.last_response = text
        return text

    def parse_stream_data_line(self, text):
        parts = text.split(",")
        if len(parts) < 12 or parts[2] != "H" or parts[7] != "L":
            return None

        try:
            sample_counter = int(parts[1])
            high = tuple(int(parts[i]) for i in (3, 4, 5, 6))
            low = tuple(int(parts[i]) for i in (8, 9, 10, 11))
        except ValueError:
            return None

        high_signed = tuple(r if r < 32768 else r - 65536 for r in high)
        low_signed = tuple(r if r < 32768 else r - 65536 for r in low)
        difference = tuple(h - l for h, l in zip(high_signed, low_signed))
        volts = tuple((r / 32768.0) * 5.0 for r in high_signed[:2])
        return sample_counter, high, low, difference, volts

    def handle_stream_line(self, line):
        if not line:
            return None

        text = line.decode("utf-8", errors="ignore").strip()
        if not text.startswith("DATA,"):
            return None

        return self.parse_stream_data_line(text)

    def turn_off(self):
        try:
            if self.is_open:
                self.send_command(0, 0) # turn device off first
        finally:
            self.disconnect()

    def start_device(self):
        self.send_command(0, 1)

    def stop_device(self):
        self.send_command(0, 0)

    def set_visible_pd_gain(self, value):
        self.send_command(1, value)

    def set_ir_pd_gain(self, value):
        self.send_command(2, value)

    def set_vis_led_dac(self, value):
        self.send_command(3, value)
        self.vis_led_dac = value

    def pulse_ir_led(self, value):
        min_val = 49 #49 is the minimum value for IR LED intensity that actually results in some output - anything below is nothing, likely due to time delays
        max_val = 100
        value_to_send = int((((max_val-min_val)/100)*value)+min_val) #map the sent value between our min and max values
        #also we rounded it to nearest integer since that's what firmware expects
        value_to_send = 100 if value_to_send > 100 else value_to_send
        value_to_send = min_val if value_to_send < min_val else value_to_send 
        #clamp it

        self.send_command(16, value_to_send)

    def request_status(self):
        self.send_command(7, 0)
        return self.read_response()

    def read_single_adc(self):
        self.send_command(8, 0)
        deadline = time.time() + 1.0
        while time.time() < deadline:
            if self.serial.in_waiting:
                parts = self.serial.readline().decode("utf-8", errors="ignore").strip().split(",")
                if parts[0] == "SINGLE_RAW" and len(parts) == 5:
                    try:
                        return tuple(int(value) for value in parts[1:])
                    except ValueError:
                        pass
            time.sleep(0.01)
        return None

    def set_adc_streaming(self, enabled):
        self.send_command(9, 1 if enabled else 0)

    def set_adc_stream_decimation(self, value):
        self.send_command(10, value)

    def set_sample_rate(self, rate_hz):
        self.send_command(11, rate_hz)

    def clear_vis_schedule(self):
        self.send_command(12, 0)

    def append_schedule_step(self, time_s, dac_code):
        self.send_command(13, time_s, dac_code)

    def start_vis_schedule(self):
        self.send_command(14, 0)

    def stop_vis_schedule(self):
        self.send_command(15, 0)
