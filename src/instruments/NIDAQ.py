import matplotlib.pyplot as plot
import json as js
from src.instruments.instrument import Instrument
from picosdk.functions import mV2adc
import nidaqmx
from nidaqmx.constants import READ_ALL_AVAILABLE, AcquisitionType
import numpy as np
from time import *

with open(r'config/systemDefaults.json') as f:
    defaults = js.load(f)

class DAQ(Instrument):
    """ Class for the National Instruments DAQ card """
    def __init__(self):
        super().__init__("NI DAQ")
        self.type = "DAQ"
        self.status = {}
        self.is_connected = False
        self.pulse_duration = defaults["main laser"]["pulse duration"]
        self.sampling_mode = defaults["experiments"]["OPTP"]

        self.sample_num = int(self.pulse_duration *
                           self.sampling_mode["pulses"] *
                           self.sampling_mode["sampling counts"]/
                           defaults["NIDAQ"]["timebase"])

    def setup(self) -> None:
        """ Set up the NI DAQ device
        Returns: 
            0 if success, or relevant error code if failed
        """
        self.task = nidaqmx.Task()
        # Only 2 channels are important
        self.task.ai_channels.add_ai_voltage_chan("PCIe-6376/ai1:2", min_val = -10.0, max_val=10.0)
        self.is_connected = True

    def close(self) -> None:
        """ Close the NI DAQ device """
        self.task.close()
        self.is_connected = False

    def get_data(self, channels: str = "PCIe-6376/ai0:2", min_val: float = -10.0, max_val: float = 10.0,
                 sample_rate: int = 2500000, samples_per_chan: int = 500, trigger_source: str = "/PCIe-6376/PFI0") -> list:
        """ Get data from the NI DAQ device
        Args:
            channels (str): Channels to read from
            min_val (float): Minimum voltage value
            max_val (float): Maximum voltage value
            sample_rate (int): Sample rate in Hz
            samples_per_chan (int): Number of samples per channel
            trigger_source (str): Trigger source
        Returns:
            data (list): List of data from the channels
        """
         # Example usage of nidaqmx to read data from the DAQ card
         # For more information, refer to the nidaqmx documentation
         # https://nidaqmx-python.readthedocs.io/en/latest/
         # and the NI-DAQmx C Reference Help

DAQ.timing.cfg_samp_clk_timing(2500000,
                                sample_mode=AcquisitionType.FINITE,
                                samps_per_chan=500)
DAQ.triggers.start_trigger.cfg_dig_edge_start_trig("/PCIe-6376/PFI0")
data = DAQ.read(number_of_samples_per_channel=READ_ALL_AVAILABLE)
power = np.add(data[1], data[2])
print(np.mean(power[462:]))
plot.vlines(x=462, ymin=-3, ymax=3)
plot.plot(power, label="A+B")
plot.plot(data[0], label="A-B")

# plot.plot(np.divide(np.add(data[1], data[2]), data[0]), label="Normalised")
plot.ylabel("Amplitude")
plot.title("Waveform")
plot.legend()
plot.tight_layout()
plot.show()

DAQ.close()