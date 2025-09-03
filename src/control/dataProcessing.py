import re
import numpy as np
import json as js
import pandas as pd
from picosdk.functions import adc2mV
import pyfftw  # FFTW used in Matlab.

# TODO: Spectrum analysis, enabling bandwidth measurements. Remember to do it for noise floor too.
# TODO: Add method to save data to file
# TODO: Convert knifeedge matlab code to python
# TODO: The only data necessary: Delay (mm), A, B, C, D, std of signals, std of delay
# TODO: Windowing function: ignore noise

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

class WaveformDP:
    """
    Data Processing class for the waveforms from the PicoScope.

    This is current written with the sampling scheme for OPTP, which
    is what we primarily run. The data processing is done in the
    following way:
    1. The data is segmented into 4 segments, A, B, C, D. These
       segments correspond to the 4 different signals that we measure.
            -> A: E_on + pump + gate pulse,
               B: Pump + gate pulse,
               C: E_off + gate pulse,
               D: Gate pulse
        To get an accurate DT, (A - B) - (C - D) to account for
        potential generation of THz via pump in the sample.
    2. The mean of each segments are appended to the buffers for the
       duration of the repeat.
    3. The values in the buffers are then averaged to get the mean
       signal for each signal. The mean signals are appended to lists
       in the data dictionary. Noise of the signals are also calculated
       and appended to the data dictionary.
    4. The data dictionary will also hold values of computed THz
       signals to be plotted and saved. The min max values are also
       noted.
    5. The buffers are cleared after each step (you"d need to call the
       function to do so in your experiment program).
    6. The data is saved and cleared after each experiment (you"d need
       to call the function to do so in your experiment program).
    """

    # Buffers are cleared after each step
    A_buffer = []
    B_buffer = []
    C_buffer = []
    D_buffer = []

    def __init__(self,
                 experiment_name: str,
                 delay_mm: np.ndarray):
        self.pulse_duration = defaults["main laser"]["pulse duration"]
        self.sampling_signals = (defaults["sampling scheme"]
                            ["pulses"])
        sampling_counts = (defaults["sampling scheme"]
                            ["sampling counts"])
        self.pulses_per_sample = self.sampling_signals * sampling_counts
        self.signal_window = (defaults["sampling scheme"]
                              ["signal windowing"]["start"],
                              defaults["sampling scheme"]["signal windowing"]["start"] +
                              defaults["sampling scheme"]["signal windowing"]["width"])

        # Make a frequency array
        delay_ps = 2* delay_mm * 1e9 / defaults["C"]
        if len(delay_mm) != 1:
            double_bandwidth = (len(delay_mm)/(delay_ps[-1] - delay_ps[0]))
            frequencies = np.linspace(0, double_bandwidth, len(delay_ps))
        else:
            frequencies = np.array([0.0])  # No frequency for single point      
        self.data = {"Delay (mm)": delay_mm, "Delay (ps)": delay_ps, "A": [],
                     "B": [], "C": [], "D": [], "E_off": [], "E_on": [],
                     "DT": [], "E_off Spectrum": [], "E_on Spectrum": [],
                    "DT Spectrum": [], "Frequency (THz)": frequencies,
                    "E_off max": [], "E_off min": [], "E_on max": [],
                    "E_on min": [], "DT max": [], "DT min": [],
                    "Saturation": False, "Background noise": [],
                    "Emitter noise": [], "Pump-induced noise": [],
                    "Total noise": [], "OPTP noise": []}
        
    def check_and_segment_data(self, ps_raw_output: np.ndarray):
        """ Check for saturation and segment the PicoScope data """
        # Check for saturation (9.7 V)
        if (ps_raw_output.max() >= 31800 or
            ps_raw_output.min() <= -31801):
            self.data["Saturation"] = True
        
        # Segment the data into individual pulses.
        # For 80000 sample points, we have 40 pulses (10 pulse cycles). 
        segments = ps_raw_output.reshape(self.pulses_per_sample, -1)
        # Zero out the parts of the segments that are not in the signal window
        # This is to avoid noise from other parts of the signal.
        segments[:, :self.signal_window[0]] = 0
        segments[:, self.signal_window[1]+1:] = 0
        
        # Get the average of pulse ABCD, and aggregate them into buffers.
        # Only average the signal window (1850 to 2000).
        for i in range(0, self.pulses_per_sample, self.sampling_signals):
            self.A_buffer.append(np.mean(segments[i][self.signal_window[0]:
                                                           self.signal_window[1]]))
            self.B_buffer.append(np.mean(segments[i+1][self.signal_window[0]:
                                                             self.signal_window[1]]))
            self.C_buffer.append(np.mean(segments[i+2][self.signal_window[0]:
                                                             self.signal_window[1]]))
            self.D_buffer.append(np.mean(segments[i+3][self.signal_window[0]:
                                                             self.signal_window[1]]))

        # return the segments reshaped to 2D array
        # This is useful for plotting the data.
        return segments.reshape(-1)

    def update_data(self):
        """
        Return the mean of segmented data and updates data dictionary
        to be saved later. Calculations are made for plotting.
        
        Noise is a difficult thing to calculate, it should always be
        calculated here as it is the number of repeats that determines
        the noise floor.

        The noise calculated are as follows:
        - Baseline background noise: std(D)
        - Emitter only noise: std(C - D)
        - Optical pump-induced noise: std(B - D)
        - Total noise from pump + THz + interactions: std(A - D)
        - OPTP (THz change induced by the optical pump) noise:
            std(A - B - C + D)
        """
        A = np.array(self.A_buffer)
        B = np.array(self.B_buffer)
        C = np.array(self.C_buffer)
        D = np.array(self.D_buffer)
        ABCD = [np.mean(A), np.mean(B), np.mean(C), np.mean(D)]
        noise = [np.std(D), # Baseline background noise
                 np.std(C - D), # Emitter noise
                 np.std(B - D), # Pump-induced noise
                 np.std(A - D), # Total noise
                 np.std(A - B - C + D)] # OPTP noise

        for i, key in enumerate(["A", "B", "C", "D"]):
            self.data[key].append(ABCD[i])
        
        for i, key in enumerate(["Background noise", "Emitter noise",
                                "Pump-induced noise", "Total noise",
                                "OPTP noise"]):
            self.data[key].append(noise[i])

        # Calculate E_off, E_on and DT
        self.data["E_off"].append(ABCD[2] - ABCD[3])
        
        self.data["E_on"].append(ABCD[0] - ABCD[1])
        # E_on - E_off = (A - B) - (C - D)
        self.data["DT"].append(ABCD[0] - ABCD[1] - ABCD[2] + ABCD[3])

        for key in ["E_off", "E_on", "DT"]:
            self.data[f"{key} max"] = [max(self.data[key]),
                                       self.data["Delay (mm)"]
                                       [self.data[key].index(
                                       max(self.data[key]))]]
            self.data[f"{key} min"] = [min(self.data[key]),
                                       self.data["Delay (mm)"]
                                       [self.data[key].index(
                                       min(self.data[key]))]]

        if len(self.data["Frequency (THz)"]) != 1:
            # Method to calculate FFT can be changed
            # Calculating spectra using FFTW, similar to Matlab
            # https://pyfftw.readthedocs.io/en/latest/source/pyfftw/builders/builders.html
            self.data["E_off Spectrum"] = pyfftw.builders.fft(
                np.array(self.data["E_off"]))()
            self.data["E_on Spectrum"] = pyfftw.builders.fft(
                np.array(self.data["E_on"]))()
            self.data["DT Spectrum"] = pyfftw.builders.fft(
                np.array(self.data["DT"]))()
            self.data["E_off Spectrum"] = np.abs(self.data["E_off Spectrum"])
            self.data["E_on Spectrum"] = np.abs(self.data["E_on Spectrum"])
            self.data["DT Spectrum"] = np.abs(self.data["DT Spectrum"])
        else:
            # If only one point, no FFT can be calculated
            self.data["E_off Spectrum"] = np.array([0.0])
            self.data["E_on Spectrum"] = np.array([0.0])
            self.data["DT Spectrum"] = np.array([0.0])

    def clear_buffers(self):
        """
        Clear the ABCD buffers. Should be called after each step
        """
        self.A_buffer = []
        self.B_buffer = []
        self.C_buffer = []
        self.D_buffer = []

    def generate_datafile(self,
                          save_dir:str,
                          sample: str,
                          experiment_count: int,
                          experiment_name: str,
                          type: str):
        """
        Generate a data file with its name based on the sample and
        experimental parameters dictionary and attributes.
        The data is saved in either txt, json or hfd5.
        """
        self.save_type = type
        match self.save_type:
            case "txt":
                try:
                    self.filename = (f"{save_dir}/{experiment_count}_"
                                f"{sample}_{experiment_name}")
                    with open(f"{self.filename}.txt", "x") as f:
                        pass
                except FileExistsError:
                    print("File already exists.\nSuggest using a different" \
                    "directory to save similar samples.")
            case "hdf5":
                pd.DataFrame.from_dict(self.data).to_hdf(
                    f"{filename}.h5", key="df", mode="w")
            case "json":
                with open(f"{filename}.json", "w") as f:
                    js.dump(self.data, f, indent=4)
            case _:
                raise ValueError("Invalid file type. Choose from txt," \
                "hdf5 or json.")
    
    def save_data(self,
                  keys: list = ["Delay (mm)", "A", "B", "C", "D",
                                "Background noise", "Emitter noise",
                                "Pump-induced noise", "Total noise",
                                "OPTP noise"]):
        """
        Save the experiment"s data and reset the experiment"s
        attributes.
        Should be called after each experiment and each stop.
        Can store in either hdf5 file format for efficient storage, or
        csv for easy access.
        """
        # TODO: Implement saving to file types json and hdf5

        min_len = min(len(self.data[key]) for key in keys)
        result = pd.DataFrame({k: self.data[k][:min_len] for k in keys})
        if self.save_type == "txt":
            result.to_csv(f"{self.filename}.txt", sep="\t", index=False)
        #     np.savetxt(f"{filename}.txt", pd.DataFrame.from_dict(self.data))
        # elif type == "hdf5":
        #     pd.DataFrame.from_dict(self.data).to_hdf(f"{filename}.h5",
        #                                               key="df",
        #                                               mode="w")
        # elif type == "json":
        self.clear_buffers()

# TODO: Consider implementing the .thz file format:
# https://github.com/dotTHzTAG/Documentation/blob/main/thz_file_format.md