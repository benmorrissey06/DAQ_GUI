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

Click the button for desired COM Port

Turn on LIVE to begin streaming and start device

Apply desired settings in General Controls, or set up a timed recording with a variety of options in Recording Controls

Select which plots you would like to view from the checkboxes on the right window of the screen

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
PROPER CSV FORMAT!
Column	Type	Notes
host_time	float	time.time() on the PC
sample_counter	int	Firmware counter; empty on event rows
high_ch1–high_ch4	int	Raw ADC counts, IR LED on; empty on event rows
low_ch1–low_ch4	int	Raw ADC counts, IR LED off; empty on event rows
difference_ch1–difference_ch4	int	high − low; empty on event rows
event	str	Description; empty on data rows

Make it so that resizing plots does not erase previous data

Add apply button for sliders

Make overrides between master and individual intentional

Make graph resume where you left off when you stop via Live button***

X button for tabs

Refactor codebase since master tab and device tab share MANY functions, just copied and pasted. We should make those in a shared class (Toolbox class which holds these repeated functions? And the repeated ui code)  e.g. new function called draw_general_ctrls, and draw_recording_ctrls

Add event column

Make the light value entered in a time segment functional, currently that is only frontend

Add signs on graph for events

Verify what settings should be in the json? segments too?

Adapt to any new firmware changes

Quality of life and safety features

Package in Executable program

```