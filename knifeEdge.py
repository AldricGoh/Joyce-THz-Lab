import json as js
from src.instruments.MCM3000 import MCM3000
import numpy as np
import time
from src.instruments.XPS import XPS
from QWP_tuning import gradient_descent
from src.instruments.Picoscope4000 import PS4000 as ps
from src.instruments.DLS import DLS
from src.control.dataProcessing import WaveformDP
from src.control.email import send_notification

# -------------------- Knife Edge Scan --------------------
# -------------------- Setup --------------------
# Limits are 0 and 29.9 mm
date = "251027"
position = 37.422 # DLS position in mm
y_pos = 28.5
x_map = np.arange(9, 13.01, 0.05)
y_map = np.arange(15.5, 29.6, 1)
repeats = 3
is_THz = True

# -----------------------------------------------

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

ps4000 = ps()
thz_dls = DLS()
pump_dls = DLS()
XPS = XPS()

def open_instruments():
    thz_dls.setup(defaults["DLS"]["THz DLS"]["serial port"])
    pump_dls.setup(defaults["DLS"]["Pump DLS"]["serial port"])
    ps4000.setup()
    XPS.setup(defaults["XPS"]["address"], defaults["XPS"]["port"])

def wind_down():
    ps4000.close()
    thz_dls.close()
    pump_dls.close()

start = time.time()

MCM3000 = MCM3000("MCM3000")

# x mid point = 14.8
# y mid point = 15.5

MCM3000.setup(defaults["MCM3000"]["serial port"])
print(MCM3000.get_command("current x position"))
print(MCM3000.get_command("current y position"))
ascending_x = True

def THz_knife_edge_scan_1D(x_map=x_map, y=y_pos):
    dict_to_save = {}
    open_instruments()
    thz_dls.set_command("move absolute", position)
    MCM3000.set_command("move absolute y position", value = y)
    print("Y position:", MCM3000.get_command("current y position"))
    gradient_descent(ps4000=ps4000, XPS=XPS)
    waveformDP = WaveformDP("Knife Edge",np.array([x_map[0]]))
    for x in x_map:
        MCM3000.set_command("move absolute x position", value = x)
        print("X position:", MCM3000.get_command("current x position"))
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        waveformDP.update_data()
        waveformDP.clear_buffers()
        waveformDP.data["Delay (mm)"] = np.append(
                    waveformDP.data["Delay (mm)"], x)
    dict_to_save["x"] = list(x_map)
    dict_to_save["Amplitude"] = list(np.subtract(waveformDP.data["C"],
                                            waveformDP.data["D"]))
    wind_down()
    with open(f"D:/Aldric/Data/{date}/{y}_THz_knifeEdge_1D.json", "w") as f:
        js.dump(dict_to_save, f)
    end = time.time()
    print("Program ended. Time taken:", end - start, "seconds")

def THz_knife_edge_scan_2D(x_map=x_map, y_map=y_map):
    dict_to_save = {}
    open_instruments()
    thz_dls.set_command("move absolute", position)
    for y in y_map:
        MCM3000.set_command("move absolute y position", value = y)
        print("Y position:", MCM3000.get_command("current y position"))
        gradient_descent(ps4000=ps4000, XPS=XPS)
        waveformDP = WaveformDP("Knife Edge",np.array([x_map[0]]))
        for x in x_map:
            MCM3000.set_command("move absolute x position", value = x)
            print("X position:", MCM3000.get_command("current x position"))
            for repeat in range(repeats):
                raw_signals = ps4000.get_data()
                waveformDP.check_and_segment_data(raw_signals)
            waveformDP.update_data()
            waveformDP.clear_buffers()
            waveformDP.data["Delay (mm)"] = np.append(
                        waveformDP.data["Delay (mm)"], x)
        dict_to_save[f"{y}"] = {"x": list(x_map),
                                "Amplitude": list(np.subtract(waveformDP.data["C"],
                                                         waveformDP.data["D"]))}
        del waveformDP
        x_map = x_map[::-1]
    wind_down()
    with open(f"D:/Aldric/Data/{date}/THz_knifeEdge.json", "w") as f:
        js.dump(dict_to_save, f)
    end = time.time()
    print("Program ended. Time taken:", end - start, "seconds")

THz_knife_edge_scan_1D()
send_notification("azkg2@cam.ac.uk")
