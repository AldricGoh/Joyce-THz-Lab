try:
    import numpy as np
    import json as js
    from src.instruments.Picoscope4000 import PS4000 as ps
    from src.instruments.XPS import XPS
    from src.control.dataProcessing import WaveformDP
    from ctypes import *
    from time import *
except OSError as ex:
    print("Warning:", ex)

initial_angle = 138.3 # Initial angle of the detector crystal in degrees
target_balance = 82.5
calibration_range = 5 # Target range of balance
repeats = 15
step_size = 0.01

with open(r'config\systemDefaults.JSON') as f:
    defaults = js.load(f)

# Gradient (numerical derivative)
def numerical_gradient(f, x, h=1e-3):
    return (f(x + h) - f(x - h)) / (2 * h)

# Gradient descent optimizer
def gradient_descent(ps4000,
                     XPS,
                     initial_angle=None,
                     target_balance=target_balance,
                     step_size=step_size,
                     max_iter=5000,
                     tolerance=calibration_range):
    if initial_angle is None:
        status = XPS.get_command("status data", defaults["XPS"]["QWP"])
        angle = status["position"]
    else:
        angle = initial_angle
    waveformDP = WaveformDP("QWP Tuning", np.array([angle]))
    for repeat in range(repeats):
        raw_signals = ps4000.get_data()
        waveformDP.check_and_segment_data(raw_signals)
    waveformDP.update_data()
    waveformDP.clear_buffers()
    waveformDP.data["Delay (mm)"] = np.append(waveformDP.data["Delay (mm)"], angle)
    last_difference = target_balance - waveformDP.data["D"][-1]

    for i in range(max_iter):
        XPS.set_command("move absolute", defaults["XPS"]["QWP"], position=float(angle))
        QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        while QWP_status != 12:
            QWP_status = XPS.XPS.GroupStatusGet(defaults["XPS"]["QWP"])[1]
        for repeat in range(repeats):
            raw_signals = ps4000.get_data()
            waveformDP.check_and_segment_data(raw_signals)
        waveformDP.update_data()
        waveformDP.clear_buffers()
    
        current_difference = target_balance - waveformDP.data["D"][-1]
        if abs(current_difference) < tolerance:
            # If balanced, end program
            print(f"Converged at QWP angle: {angle}")
            print(f"Balance value: {waveformDP.data['D'][-1]}")
            return
        elif current_difference*last_difference < 0:
            # Sign of difference changed
            step_size *= -1
        else:
            # Sign unchanged
            if abs(current_difference) > abs(last_difference):
                step_size *= -1
        print(f"Angle: {angle} degrees  Difference: {current_difference}")
        angle += step_size*current_difference/50
        last_difference = current_difference
        waveformDP.data["Delay (mm)"] = np.append(waveformDP.data["Delay (mm)"], angle)

    print("Oops did not converge")

if __name__ == "__main__":
    XPS = XPS()
    XPS.setup(defaults["XPS"]["address"], defaults["XPS"]["port"])
    ps4000 = ps()
    ps4000.setup()
    gradient_descent(ps4000, XPS=XPS, initial_angle=initial_angle)