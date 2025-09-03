"""Example of analog input voltage acquisition with digital start and reference trigger.

This example demonstrates how to acquire a finite amount of data
using an internal clock and a digital start and reference
trigger.
"""

import matplotlib.pyplot as plot

import nidaqmx
from nidaqmx.constants import READ_ALL_AVAILABLE, AcquisitionType

tasks = {
    "photodiode_difference": nidaqmx.Task(),
    "photodiode_A": nidaqmx.Task(),
    "photodiode_B": nidaqmx.Task()
}

for i, task in enumerate(tasks.values()):
    task.ai_channels.add_ai_voltage_chan(f"PCIe-6376/ai{i}")
    task.timing.cfg_samp_clk_timing(2500000,
                                     sample_mode=AcquisitionType.FINITE,
                                     samps_per_chan=20000)
    task.triggers.start_trigger.cfg_dig_edge_start_trig("/PCIe-6376/PFI0")
    task.start()

for _ in range(10):
    tasks["photodiode_difference"].wait_until_done(timeout=10)
    data = tasks["photodiode_A"].read(READ_ALL_AVAILABLE) + tasks["photodiode_B"].read(READ_ALL_AVAILABLE)
    plot.plot(data)
    plot.ylabel("Amplitude")
    plot.title("Waveform")
    plot.show()

task.stop()