"""Example of AI raw operation."""

import pprint

import matplotlib.pyplot as plot
import nidaqmx
from nidaqmx.constants import READ_ALL_AVAILABLE, AcquisitionType
import numpy as np

pp = pprint.PrettyPrinter(indent=4)

DAQ = nidaqmx.Task()
DAQ.ai_channels.add_ai_voltage_chan("PCIe-6376/ai0:2", min_val = -10.0, max_val=10.0)
DAQ.timing.cfg_samp_clk_timing(2500000,
                                sample_mode=AcquisitionType.FINITE,
                                samps_per_chan=20000)
DAQ.triggers.start_trigger.cfg_dig_edge_start_trig("/PCIe-6376/PFI0")
data = DAQ.read(number_of_samples_per_channel=READ_ALL_AVAILABLE)

plot.plot(np.add(data[1], data[2]), label="A+B")
plot.plot(data[0], label="A-B")

# plot.plot(np.divide(np.add(data[1], data[2]), data[0]), label="Normalised")
plot.ylabel("Amplitude")
plot.title("Waveform")
plot.legend()
plot.tight_layout()
plot.show()

DAQ.close()