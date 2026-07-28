# DAQ GUI

A graphical interface for connecting to *DAQ devices*, **streaming and plotting data**, **controlling hardware settings**, and **running timed recordings** across one or multiple devices.

Made with the **DearPyGUI** library for **clean interface**, **super readable code**, and **low line counts** to make it easy to maintain. 

Also **very modular**, so made up of 7 distinct files, each with a manageable size. 

- **daq.py** for serial communication
- **device_tab.py** for a single device interface
- **main_gui.py** to manage tabs 
- **master_tab.py** interface to control multiple devices at once
- **save_recording.py** to handle file saving
- **toolbox.py** shared class to draw controls for both device tab and master tab
- **main.py** starts the program

 Set to light mode by default. Hope you find it useful! 👍

## Key Features

- Define the save location and recording duration from the GUI.
- Automatically name files from the cohort, animal ID, test label, and current time.
- Set timed VIS LED controls during a recording, such as:
  - 0-20 seconds: no VIS light
  - 20-40 seconds: VIS DAC set to 250
  - 40+ seconds: VIS DAC set to 230
- View all four channels, with a dropdown to select CH3 or CH4 for the bottom-right plot.
- Adjust the plot window and plot height to fit different screens.
- Control multiple devices at once from the Master tab
- Rename, monitor, add, and safely remove device tabs
- Save results as CSV and capture recording settings in a JSON sidecar
- Record significant controls and schedule changes in the CSV `event` column
- Display color-coded event markers directly on the live plots
<img width="379" height="222" alt="image" src="https://github.com/user-attachments/assets/36895d3c-fab2-4345-836f-bddd17efd4f1" />


## Requirements

- Python 3.12 recommended.
- An ESP32-S3 board flashed with [`firmware/firmware.ino`](firmware/firmware.ino) and connected over USB.
- The AD524X Arduino library if rebuilding the firmware. Can be uploaded via Platform IO extension in VS code, or Arduino IDE (more beginner friendly)

## Setup

### 1. Create a virtual environment

Windows:

```powershell
python -m venv my_venv
```

Mac / Linux:

```bash
python3 -m venv my_venv
```

### 2. Activate the virtual environment

Windows (PowerShell):

```powershell
.\my_venv\Scripts\Activate.ps1
```

Mac / Linux:

```bash
source my_venv/bin/activate
```

### 3. Upgrade pip

Windows:

```powershell
python -m pip install --upgrade pip
```

Mac / Linux:

```bash
python3 -m pip install --upgrade pip
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the GUI

Windows:

```powershell
python gui/main.py
```

Mac / Linux:

```bash
python3 gui/main.py
```

## Usage

1. Enter the shared **Cohort** and **Test Label** values in the Master tab.
2. Click **+** button (in tab or device monitor) to add a device.
   <img width="959" height="538" alt="image" src="https://github.com/user-attachments/assets/9eb4ea77-4fcc-48f1-8218-214426b5acde" />
3. Enter a specific device tab by clicking on it, enter an **Animal ID** and click the desired COM port.
4. Turn on **LIVE** to start the device and begin streaming.
5. Apply the desired settings in **General Controls**, or set up a timed recording in **Recording Controls**. (switch between them by clicking on those tabs)
   <img width="1906" height="1030" alt="image" src="https://github.com/user-attachments/assets/1152c7ba-a146-4821-bf1e-508a9c75db32" />
6. Select CH3 or CH4 for the bottom-right plot and adjust the plot window or height as needed.
7. Use the **Master** tab to apply settings or recording controls across all connected devices.

## Multiple Devices

Each DAQ board gets its own tab and its own independent serial connection. The Device Monitor in the Master tab shows whether each device is live, connected, and recording. Device tabs can also be renamed or removed from that monitor.

Master controls apply settings to all connected devices. **START ALL** records the devices that are connected and live, while displaying warnings for devices that are not ready. If an individual recording is already active, stop it before using **START ALL**.

Files are named in this format:

```text
{cohort}_{animal_id}_{test_label}_{MMDDYYYY_HHMM}_Pupil
```

## Per-Device Controls

- **IR LED Intensity (0-100):** Sets the IR LED duty-cycle intensity
- **VIS PD Gain (0-255):** Sets the visible photodiode gain
- **IR PD Gain (0-255):** Sets the IR photodiode gain
- **VIS LED Gain (0-4095):** Sets the visible LED DAC code
- **Stream decimation (1-65535):** Sends every Nth sampled `DATA` line. Lower values provide more data; higher values reduce serial traffic
- **Sample rate (10-250 Hz):** Controls the firmware sampling rate; the default is 100 Hz

Hardware-control integer inputs are clamped to the displayed range when **Set** is pressed, and the clamped value is shown before it is sent

### Live Plots

The live view contains three plots:

- CH1 IR PD across the top, displayed in volts.
- CH2 VIS PD in the bottom-left, displayed in volts.
- CH3 VIS Current or CH4 IR Current in the bottom-right, selectable from the dropdown and currently displayed as raw ADC counts.

Each plot auto-scales on the y axis independently. The plot window defaults to 10 seconds and can be adjusted from 1-60 seconds.

Color-coded vertical event markers show important actions such as LIVE changes, recording controls, gain or LED changes, stream settings, and VIS schedule steps. The event color key can be shown from the device controls.

NOTE*** The plots scale differently depending on your devices screen size, so use the slider to fit it to your screen if it requires adjusting.
<img width="753" height="488" alt="image" src="https://github.com/user-attachments/assets/52714d5d-f3ec-4054-81cc-bbc7568b0a08" />


## Recording Behavior

- Recording requires a connected, live device and a duration greater than 0 seconds
- Choose a save directory before starting a recording
- Timed segments define the VIS LED DAC value between a start and end time
- Segments cannot overlap or extend beyond the recording duration
- For any time without a defined segment, the VIS LED value set before recording becomes the baseline
- Recordings stop automatically when their duration is reached, or can be stopped manually
- Turning on **LIVE** from the Master tab applies the Master decimation and sample-rate settings

### Event Column

The CSV includes an `event` column. Normal data rows leave it empty. Significant controls performed during recording are written as timestamped event rows with empty sample-data columns. Schedule steps are also recorded when the firmware reports that they fired.

Events can be selected in pandas with:

```python
events = df[df["event"].notna()]
```

### Metadata Sidecar

A JSON file with the same base name as the CSV is written when recording starts. It captures the cohort, test label, animal ID, COM port, sample rate, stream decimation, gains, VIS DAC baseline, recording duration, and VIS schedule.

## Tips and Notes

- Turning on **LIVE** from the Master tab applies the Master stream-decimation and sample-rate settings.
- Master controls override individual device controls.
- If a recording has already started on an individual device, **START ALL** is blocked and the user is notified to stop all active recordings first.

## CSV Format

| Column | Type | Notes |
| --- | --- | --- |
| `host_time` | float | `time.time()` timestamp from the PC. |
| `sample_counter` | int | Firmware sample counter; empty on event rows. |
| `high_ch1`-`high_ch4` | int | Signed raw ADC counts with the IR LED on; empty on event rows. |
| `low_ch1`-`low_ch4` | int | Signed raw ADC counts with the IR LED off; empty on event rows. |
| `difference_ch1`-`difference_ch4` | int | High minus low; empty on event rows. |
| `event` | string | Event description; empty on normal data rows. |

## Serial Protocol

The GUI communicates at 115200 baud. Most commands use `COMMAND,VALUE\n`; command 13 uses `13,TIME_S,DAC_CODE\n`. The firmware responds with prefixed lines such as `OK`, `ERR`, `DATA`, `STATUS`, `SINGLE_RAW`, `SINGLE_VOLTS`, and `SCHED`.

| Command | Value | Description |
| --- | --- | --- |
| `0` | `0/1` | Stop or start the device. |
| `1` | `0-255` | Set visible PD gain on AD524X channel 0. |
| `2` | `0-255` | Set IR PD gain on AD524X channel 1. |
| `3` | `0-4095` | Set the VIS LED DAC code on the MCP4725. |
| `4` | microseconds | Pulse the IR LED for the requested duration. |
| `7` | `0` | Print device status. |
| `8` | `0` | Perform a single ADC read and print raw values and volts. |
| `9` | `0/1` | Disable or enable ADC streaming. |
| `10` | `N` | Set stream decimation from 1-65535; default 10. |
| `11` | `N` | Set sample rate in Hz, clamped to 10-250; default 100. |
| `12` | `0` | Clear the VIS light schedule. |
| `13` | `T,D` | At T seconds after schedule start, set the VIS LED to DAC code D. |
| `14` | `0` | Start schedule execution and reset its clock and index. |
| `15` | `0` | Stop schedule execution. |
| `16` | `0-100` | Set IR LED intensity by duty cycle. (0 is not the literal minimum, but rather the minimum the hardware can support, and 100 means always on during high readings so technically it's 50%) |

