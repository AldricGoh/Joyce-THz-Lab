Dependencies -- IMPORTANT

Coded in Python 3.13.2. Ensure environment path is set to such a Python version, with the relevant dependencies installed within it.

Make sure to install drivers and command interfaces for:
- MCM3000 4.3 (You may have to email Thorlabs for it, not available online) 
- Newport DLS
- Picoscope 4000
- SC10

Important files to edit to add new experiments/instruments:
- main.py -> Ensure all instruments have instances, and are opened, closed and parsed into the experiment classes as needed.
- src/control/experiments.py -> Inherit the Experiment class to create new classes for new experiments. The input widget for the experiment should also be written here. 
- src/GUI/inputWidget -> ensure that the input widget for the new experiment is included here, and the correct instruments and DLS (note active and inactive DLS) ae parsed.
- config/systemDefaults.json

If sampling changes significantly, files to be aware of:
- src/control/dataProcessing.py - WaveformDP class
- config/systemDefaults.json