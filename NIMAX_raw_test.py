"""Example of AI raw operation."""

import pprint

import matplotlib.pyplot as plot
import nidaqmx
from nidaqmx.constants import READ_ALL_AVAILABLE, AcquisitionType
import numpy as np
from time import *

pp = pprint.PrettyPrinter(indent=4)

DAQ = nidaqmx.Task()

DAQ.ai_channels.add_ai_voltage_chan("PCIe-6376/ai0:1", min_val = -10.0, max_val=10.0)
DAQ.timing.cfg_samp_clk_timing(2500000,
                                sample_mode=AcquisitionType.FINITE,
                                samps_per_chan=25600) # 2560000
DAQ.triggers.start_trigger.cfg_dig_edge_start_trig("/PCIe-6376/PFI0")
start = time()
data = DAQ.read(number_of_samples_per_channel=READ_ALL_AVAILABLE)
end = time()
print(f"Time taken for data acquisition: {end - start} seconds")
# power = np.add(data[1], data[2])
# print(np.mean(power[462:]))
plot.vlines(x=462, ymin=-3, ymax=3)
# plot.plot(power, label="A+B")
plot.plot(data[0], label="A-B")
# plot.plot(data[3], label="Trigger")

# plot.plot(np.divide(np.add(data[1], data[2]), data[0]), label="Normalised")
plot.ylabel("Amplitude")
plot.title("Waveform")
plot.legend()
plot.tight_layout()
plot.show()

DAQ.close()