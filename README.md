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
python gui.py
```

Mac / Linux:
```bash
python3 gui.py
```

## Key Features

```bash
Convenient integration of input & output triggers when recording from the gui

Ability to define file name, path, and recording duration from the gui

Ability to set timed UV light controls (e.g. 0-20s no UV light, 20-40s UV set to 250, 40+s UV set to 230) during a recording from the gui

Better visualization of the ambient light sensor could be nice, e.g. simultaneous plotting of ambient light and IR light

Integration of closed loop TTL outputs when IR light drops below or goes above a set threshold, with customizable stimulation parameters (pulse freq, width, etc.)

Package gui in an executable program
```