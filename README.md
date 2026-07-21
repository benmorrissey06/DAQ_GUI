# Project Setup & Run Guide
Current version works beautifully
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

## Notes

Master controls will always override individual device controls, unless a recording on an individual device has already been started, in which case the user will be notified that they cannot start all until all devices has been stopped

While starting a recording, manual controls will be locked

While automating a recording, the time segments determine the value of the VIS LED at a given moment, but for any times for which a segment is not defined, the value set for VIS LED before the recording starts will be the default baseline for that recording

## Data format

...

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

MOST IMPORTANT: IR LED INTENSITY

Polish this very readme to be more organized and clear

if multiple events occur at once, there is no system in place right now.

Make it so that resizing plots does not erase previous data

ensure everything is safe if device unexpectedly disconnects

Make graph resume where you left off when you stop via Live button***

X button for tabs

Adapt to any new firmware changes

Note: turning on with live in master applies master's settings from decimation/sample - not sure if we want this

0 s recording is kinda a bug.

Make the warnings look nicer, maybe no separators

make the error pop up for no folder selected in master like it does in individual device

Package in Executable program

```