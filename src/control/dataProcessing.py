import numpy as np
import json as js
import pandas as pd
from picosdk.functions import adc2mV
import pyfftw  # FFTW used in Matlab.

# TODO: Spectrum analysis, enabling bandwidth measurements. Remember to do it for noise floor too.
# TODO: Add method to save data to file
# TODO: Convert knifeedge matlab code to python
# TODO: The only data necessary: Delay (mm), A, B, C, D

with open(r'config/systemDefaults.json') as f:
    defaults = js.load(f)

class WaveformDP:
    """
    Data Processing class for the waveforms from the PicoScope.

    This is current written with the sampling scheme for OPTP, which
    is what we primarily run. The data processing is done in the
    following way:
    1. The data is segmented into 4 segments, A, B, C, D. These
       segments correspond to the 4 different signals that we measure.
            -> A: Gate pulse,
               B: E_on + pump + gate pulse,
               C: Pump + gate pulse,
               D: E_off + gate pulse
        To get an accurate DT, (B - C) - (D - A) to account for
        potential generation of THz via pump in the sample.
    2. These segments are appended to the buffers for the duration of
       the repeat.
    3. The values in the buffers are then averaged to get the mean
       signal for each segment. The mean signals are appended to lists
       in the data dictionary.
    4. The data dictionary will also hold values of computed THz
       signals to be plotted and saved.
    5. The buffers are cleared after each step (you'd need to call the
       function to do so in your experiment program).
    6. The data is saved and cleared after each experiment (you'd need
       to call the function to do so in your experiment program).
    """

    # Buffers are cleared after each step
    A_buffer = []
    B_buffer = []
    C_buffer = []
    D_buffer = []

    # These are reset/changed after each experiment
    saturation = False

    def __init__(self,
                 experiment_name: str,
                 delay_mm: np.ndarray):
        self.pulse_duration = defaults["main laser"]["pulse duration"]
        self.sampling_signals = (defaults["experiments"][experiment_name]
                            ["pulses"])
        sampling_counts = (defaults["experiments"][experiment_name]
                            ["sampling counts"])
        self.pulses_per_sample = self.sampling_signals * sampling_counts
        
        # Make a frequency array
        delay_ps = 2* delay_mm * 1e9 / defaults["C"]
        double_bandwidth = (len(delay_mm)/(delay_ps[-1] - delay_ps[0]))
        frequencies = np.linspace(0, double_bandwidth, len(delay_ps))       
        self.data = {"Delay (mm)": delay_mm, "Delay (ps)": delay_ps, "A": [],
                    "B": [], "C": [], "D": [], "E_off": [], "E_on": [],
                    "DT": [], 'E_off_fft': [], "E_on_fft": [], "DT_fft": [],
                    "Frequency (THz)": frequencies}
        
    def check_segment_data(self, ps_raw_output: np.ndarray):
        """ Check for saturation and segment the PicoScope data """
        if (ps_raw_output.max() >= 32760 or
            ps_raw_output.min() <= -32751):
            self.saturation = True
            print("Saturation detected")
        
        # Segment the data into individual pulses.
        # For 80000 sample points, we have 40 pulses. 
        segmented_list = np.array_split(ps_raw_output,
                                        self.pulses_per_sample)
        
        # Get pulse ABCD, and aggregate them into buffers.
        A = np.concatenate([segmented_list[i] for i in
                            range(0, self.pulses_per_sample,
                                  self.sampling_signals)])
        B = np.concatenate([segmented_list[i] for i in
                            range(1, self.pulses_per_sample,
                                  self.sampling_signals)])
        C = np.concatenate([segmented_list[i] for i in
                            range(2, self.pulses_per_sample,
                                  self.sampling_signals)])
        D = np.concatenate([segmented_list[i] for i in
                            range(3, self.pulses_per_sample,
                                  self.sampling_signals)])
        
        if len(self.A_buffer) == 0:
            self.A_buffer = A
            self.B_buffer = B
            self.C_buffer = C
            self.D_buffer = D

        else:
            self.A_buffer = np.concatenate([self.A_buffer, A])
            self.B_buffer = np.concatenate([self.B_buffer, B])
            self.C_buffer = np.concatenate([self.C_buffer, C])
            self.D_buffer = np.concatenate([self.D_buffer, D])
    
    def update_data(self):
        """
        Return the mean of segmented data and updates data dictionary
        to be saved later. Calculations are made for plotting
        """
        ABCD = [np.mean(self.A_buffer), np.mean(self.B_buffer),
                np.mean(self.C_buffer), np.mean(self.D_buffer)]
        self.data["A"].append(ABCD[0])
        self.data["B"].append(ABCD[1])
        self.data["C"].append(ABCD[2])
        self.data["D"].append(ABCD[3])
        self.data["E_off"].append(ABCD[3] - ABCD[0])
        self.data["E_on"].append(ABCD[1] - ABCD[0])
        self.data["DT"].append(ABCD[3] - ABCD[1])

        # Method to calculate FFT can be changed
        # Calculating spectra using FFTW, similar to Matlab
        # https://pyfftw.readthedocs.io/en/latest/source/pyfftw/builders/builders.html
        self.data['E_off_fft'] = pyfftw.builders.fft(
            np.array(self.data['E_off']))()
        self.data['E_on_fft'] = pyfftw.builders.fft(
            np.array(self.data['E_on']))()
        self.data["DT_fft"] = pyfftw.builders.fft(
            np.array(self.data["DT"]))()
        self.data['E_off_fft'] = np.abs(self.data['E_off_fft'])
        self.data['E_on_fft'] = np.abs(self.data['E_on_fft'])
        self.data["DT_fft"] = np.abs(self.data["DT_fft"])

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
                    f'{filename}.h5', key='df', mode='w')
            case "json":
                with open(f'{filename}.json', 'w') as f:
                    js.dump(self.data, f, indent=4)
            case _:
                raise ValueError("Invalid file type. Choose from txt," \
                "hdf5 or json.")
    
    def save_data(self,
                  keys: list = ["Delay (mm)", "A", "B", "C", "D"]):
        """
        Save the experiment's data and reset the experiment's
        attributes.
        Should be called after each experiment and each stop.
        Can store in either hdf5 file format for efficient storage, or
        csv for easy access.
        """
        # TODO: Implement saving to file

        min_len = min(len(self.data[key]) for key in keys)
        result = pd.DataFrame({k: self.data[k][:min_len] for k in keys})
        if self.save_type == 'txt':
            result.to_csv(f"{self.filename}.txt", sep="\t", index=False)
        #     np.savetxt(f'{filename}.txt', pd.DataFrame.from_dict(self.data))
        # elif type == 'hdf5':
        #     pd.DataFrame.from_dict(self.data).to_hdf(f'{filename}.h5',
        #                                               key='df',
        #                                               mode='w')
        # elif type == "json":

        # self.saturation = False
    

class KnifeEdgeDP:
    """ Data Processing class for Knife Edge signals """
    
    def __init__(self, pulse_duration, sampling_signals, sampling_counts):
        self.pulse_duration = pulse_duration
        self.sampling_signals = sampling_signals
        self.sampling_counts = sampling_counts
        
    def calculate_mean_signals(self):
        """ Calculate the mean signals """
        A_buffer_mean = np.mean(self.A_buffer)
        B_buffer_mean = np.mean(self.B_buffer)
        C_buffer_mean = np.mean(self.C_buffer)
        D_buffers_mean = np.mean(self.D_buffer)

        return [A_buffer_mean, B_buffer_mean, C_buffer_mean,
                D_buffers_mean]

# TODO: Consider implementing the .thz file format:
# https://github.com/dotTHzTAG/Documentation/blob/main/thz_file_format.md