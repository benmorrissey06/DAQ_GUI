# Project Setup & Run Guide

## Create virtual environment

Windows:
```bash
python -m venv my_venv
```

Mac / Linux:
```bash
python3 -m venv my_venv
```

## Activate virtual environment

Windows (PowerShell):
```bash
.\my_venv\Scripts\Activate.ps1
```

Mac / Linux:
```bash
source my_venv/bin/activate
```

## Upgrade pip

Windows:
```bash
python -m pip install --upgrade pip
```

Mac / Linux:
```bash
python3 -m pip install --upgrade pip
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the GUI

Windows:
```bash
python gui/main.py
```

Mac / Linux:
```bash
python3 gui/main.py
```

## Usage Instructions

Click the + button tab to add a device

Click the button for desired COM Port

Turn on LIVE to begin streaming and start device

Apply desired settings in General Controls, or set up a timed recording with a variety of options in Recording Controls

Select which plots you would like to view from the dropdown on the right window of the screen

Switch to master tab to apply settings that affect all devices

## Key Features

```text
Ability to define file name, path, and recording duration from the gui

Automatic file naming based on current time and entered data

Ability to set timed UV light controls (e.g. 0-20s no UV light, 20-40s UV set to 250, 40+s UV set to 230) during a recording from the gui (CURRENTLY ONLY FRONTEND)

Better visualization of the ambient light sensor, all four channels visible via checkbox options

Control multiple devices at once

save results as CSV and capture recording settings in a json

View events in the saved CSV and live on the graph
```

```text
TO DO:

Make master start all toggle to stop all like in device_tab

Make Start All from Master show as green event in individual

Make schedule events greater than duration trigger an error,similar to overlap.

Make recording stop also show up as an event

PROPER CSV FORMAT!
Column	Type	Notes
host_time	float	time.time() on the PC
sample_counter	int	Firmware counter; empty on event rows
high_ch1–high_ch4	int	Raw ADC counts, IR LED on; empty on event rows
low_ch1–low_ch4	int	Raw ADC counts, IR LED off; empty on event rows
difference_ch1–difference_ch4	int	high − low; empty on event rows
event	str	Description; empty on data rows

Make it so that resizing plots does not erase previous data

Make overrides between master and individual intentional

Make graph resume where you left off when you stop via Live button***

X button for tabs

Make buttons on master toggle on ones in individual device

Make master set buttons functional

Make the light value entered in a time segment functional, currently that is only frontend

Verify what settings should be in the json? segments too?

Adapt to any new firmware changes

Quality of life and safety features

Package in Executable program

```