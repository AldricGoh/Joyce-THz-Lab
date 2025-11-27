try:
    import sys
    import numpy as np
    import json as js
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QTabWidget, QMainWindow
    )
    from src.GUI.inputWidgets import (
        InputWidget, TuningInputWidget
    )
    from src.GUI.plotWidgets import PlotManager
    from PyQt6.QtCore import QTimer, QThreadPool
    # Import all instrument classes here
    from src.instruments.Picoscope4000 import PS4000 as ps
    from src.instruments.DLS import DLS
    from src.instruments.SC10 import SC10
    from src.instruments.FWxC import FWxC
    from src.instruments.XPS import XPS
    from src.control.dataProcessing import WaveformDP
    from src.control.experiments import *
    from src.control.worker import Worker
    from ctypes import *
    import qdarktheme
    import datetime
    from time import *
except OSError as ex:
    print("Warning:", ex)

# Only scan 180 degrees because of symmetry
# 1 - 2 mW for 
date = "250929"

min_position = 37.461 # DLS position in mm
max_position = 37.554 # DLS position in mm
detector_crystal_angle = 221 # Angle of the detector crystal in degrees
repeats = 15
ascending = True
small_angle = 0.01

with open(r'config\systemDefaults.JSON') as f:
    defaults = js.load(f)

ps4000 = ps()
thz_dls = DLS()
pump_dls = DLS()
XPS = XPS()
XPS.setup(defaults["XPS"]["address"], defaults["XPS"]["port"])

def open_instruments():
    thz_dls.setup(defaults["DLS"]["THz DLS"]["serial port"])
    pump_dls.setup(defaults["DLS"]["Pump DLS"]["serial port"])
    ps4000.setup()

def wind_down():
    ps4000.close()
    thz_dls.close()
    pump_dls.close()

def run_subtraction_program():
    start = time()
    angle = 140 # Initial angle of the QWP in degrees
    open_instruments()
    waveformDP = WaveformDP("QWP",np.array([0]))
    waveformDP.generate_datafile(f"D:/Aldric/Data/{date}",
                                str(detector_crystal_angle),
                                1, "QWP", "txt")
    thz_dls.set_command("move absolute", min_position)
    while angle > 135:
        XPS.set_command("move absolute", defaults["XPS"]["QWP"], position=float(angle))
        QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        while QWP_status != 12:
            QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        waveformDP.update_data()
        waveformDP.clear_buffers()
        thz_dls.set_command("move absolute", max_position)
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        if waveformDP.data["Saturation"][-1] == True:
             waveformDP.data["Delay (mm)"] = np.append(
                waveformDP.data["Delay (mm)"], np.nan)
        else:
            waveformDP.data["Delay (mm)"] = np.append(
                    waveformDP.data["Delay (mm)"], angle)
        waveformDP.clear_buffers()
        thz_dls.set_command("move absolute", min_position)
        angle -= small_angle
        print(f"Angle: {angle} degrees")
    waveformDP.save_data()
    wind_down()
    print("Program ended.")
    end = time()
    print(f"Time taken: {end - start} seconds")
    return

def run_addition_program():
    start = time()
    angle = 135 # Initial angle of the QWP in degrees
    open_instruments()
    waveformDP = WaveformDP("QWP",np.array([0]))
    waveformDP.generate_datafile(f"D:/Aldric/Data/{date}",
                                str(detector_crystal_angle),
                                1, "QWP", "txt")
    thz_dls.set_command("move absolute", min_position)
    while angle < 140:
        XPS.set_command("move absolute", defaults["XPS"]["QWP"], position=float(angle))
        QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        while QWP_status != 12:
            QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        waveformDP.update_data()
        waveformDP.clear_buffers()
        thz_dls.set_command("move absolute", max_position)
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        if waveformDP.data["Saturation"][-1] == True:
             waveformDP.data["Delay (mm)"] = np.append(
                waveformDP.data["Delay (mm)"], np.nan)
        else:
            waveformDP.data["Delay (mm)"] = np.append(
                    waveformDP.data["Delay (mm)"], angle)
        waveformDP.clear_buffers()
        thz_dls.set_command("move absolute", min_position)
        angle += small_angle
        print(f"Angle: {angle} degrees")
    waveformDP.save_data()
    wind_down()
    print("Program ended.")
    end = time()
    print(f"Time taken: {end - start} seconds")
    return

while detector_crystal_angle < 358:
    if ascending:
        run_addition_program()
    else:
        run_subtraction_program()
    proceed = input("Continue? (y/n): ")
    if proceed.lower() in ['y', 'yes']:
        detector_crystal_angle += 1
        ascending = not ascending
    else:
        break