import json as js
import numpy as np
from src.control.task import Task
from PyQt6.QtWidgets import (
    QGridLayout, QLabel, QLineEdit, QGroupBox, QComboBox, QWidget,
    QHBoxLayout, QPushButton
)
from src.instruments.DLS import DLS
from src.instruments.Picoscope4000 import PS4000
from src.instruments.MCM3000 import MCM3000
from src.control.dataProcessing import WaveformDP
from src.GUI.usefulWidgets import RowContainer
from time import *

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

class KnifeEdge(Task):
    """
    Class for knife edge spot size measurement.
    """
    def __init__(self, active_DLS):
        """
        """
        super().__init__(active_DLS, None, None)
        self.name = "Knife Edge Measurement"
        self.repeats = defaults["knife edge"]["repeats"]
        self.limits = defaults["knife edge"]["limits"]
        self.step_size = defaults["knife edge"]["step size"]
        self.position = None

    class input_widget:
        def __init__(self):
            """
            Create the input widget for the amplitude tuning task.
            """
            self.GUI = self.GUI()
        
        def GUI(self):
            """
            Create the input menu for the amplitude tuning task.
            """
            tuneAmplitude_widget = QGroupBox("Amplitude")
            TA_widget_layout = QHBoxLayout()
            tuneAmplitude_widget.setLayout(TA_widget_layout)

            self.tune_amplitude_label = QLabel("Tune at (mm):")
            self.tune_amplitude_position = QLineEdit()
            self.tune_amplitude_position.setFixedWidth(150)  # Set a fixed width of 100 pixels
            TA_widget_layout.addWidget(self.tune_amplitude_label)
            TA_widget_layout.addWidget(self.tune_amplitude_position)

            return tuneAmplitude_widget
    
    def run(self,
            emit,
            ps: PS4000,
            mcm3000: MCM3000):
        """
        This is the main function for running the knife edge
        task.
        """
        # Generate the picoscope time array
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, np.array([self.position]))
        # Main loop for the entire experiment
        # Move delay array to the correct position
        self.active_DLS.set_command("move absolute", self.position)
        # Collect data from the Picoscope for the number of repeats
        while not self.stop_task:
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop tuning from the GUI
                if self.stop_task:
                    self.stop_task = False
                    return
                # Emit a dictionary to the main thread to be ploted
                emit({"time": ps_time, "signal": raw_signals})
                self.waveformDP.check_segment_data(raw_signals)
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()

            # Emit the data dictionary to main thread to be plotted
            emit(self.waveformDP.data)
            self.waveformDP.data["Delay (mm)"] = np.append(
                self.waveformDP.data["Delay (mm)"], self.position+value)
            value += 0.000001