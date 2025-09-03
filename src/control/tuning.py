import json as js
import numpy as np
from src.control.task import Task
from PyQt6.QtWidgets import (
    QLabel, QLineEdit, QGroupBox, QHBoxLayout, QGridLayout,
    QPushButton
)
from src.instruments.Picoscope4000 import PS4000
from src.control.dataProcessing import WaveformDP
from src.instruments.XPS import XPS
from time import *

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

class TuneBalance(Task):
    """
    Class for tuning balance.
    """
    def __init__(self, active_DLS):
        """
        """
        super().__init__(active_DLS, None, None)
        self.name = "Balance Tuning"
        self.repeats = defaults["tuning"]["Balance"]["repeats"]
        self.target_precision = defaults["tuning"]["Balance"]["target precision"]
        self.position = None

    class input_widget:
        def __init__(self):
            """
            Create the input widget for the balance tuning task.
            """
            self.GUI = self.GUI()
        
        def GUI(self):
            """
            Create the input menu for the balance tuning task.
            """
            tuneBalance_widget = QGroupBox("QWP controls")
            TB_widget_layout = QGridLayout()
            tuneBalance_widget.setLayout(TB_widget_layout)

            self.QWP_status = QLabel("NA")
            self.QWP_status.setStyleSheet("border: 1px solid white;")
            self.QWP_status_string = QLabel("")
            self.QWP_position = QLabel("NA")
            self.QWP_position.setStyleSheet("border: 1px solid white;")
            self.move_DL_button = QPushButton("Move DL to (mm):")
            self.DL_position = QLineEdit()
            self.QWP_reset_button = QPushButton("Initialize and Home QWP")
            self.QWP_move_absolute_button = QPushButton("Move QWP to:")
            self.QWP_move_absolute_position = QLineEdit()
            self.QWP_move_relative_step = QLineEdit()
            self.QWP_reduce_step = QPushButton("-")
            self.QWP_add_step = QPushButton("+")
            self.tune_balance_button = QPushButton("Magic Tune at (mm):")
            TB_widget_layout.addWidget(QLabel("QWP status:"), 0, 0, 1, 1)
            TB_widget_layout.addWidget(self.QWP_status, 1, 0, 1, 1)
            TB_widget_layout.addWidget(QLabel("QWP position:"), 0, 1, 1, 1)
            TB_widget_layout.addWidget(self.QWP_position, 1, 1, 1, 1)
            TB_widget_layout.addWidget(self.QWP_reset_button, 0, 2, 2, 4)
            TB_widget_layout.addWidget(self.QWP_status_string, 2, 0, 1, 6)
            TB_widget_layout.addWidget(self.QWP_move_absolute_button, 3, 0, 1, 1)
            TB_widget_layout.addWidget(self.QWP_move_absolute_position, 3, 1, 1, 1)
            TB_widget_layout.addWidget(self.QWP_reduce_step, 3, 2, 1, 1)
            TB_widget_layout.addWidget(self.QWP_move_relative_step, 3, 3, 1, 1)
            TB_widget_layout.addWidget(self.QWP_add_step, 3, 4, 1, 1)
            TB_widget_layout.addWidget(self.tune_balance_button, 4, 0, 1, 2)
            TB_widget_layout.addWidget(self.DL_position, 4, 2, 1, 3)
            return tuneBalance_widget
        
        # Min E_off @ QWP position with balance of {} and balance noise of {}

        def update_data(self, data: dict):
            """
            Update the QWP status and position in the input widget.
            """
            self.QWP_status.setText(str(data["status"]))
            self.QWP_position.setText(f"{data['position']}")
            self.QWP_status_string.setText(data["status string"])

    def gradient_descent_tune(self,
                              emit,
                              XPS: XPS,
                              ps: PS4000,
                              group: str = defaults["XPS"]["QWP"]):
        """
        Auto tune the balance of the QWP using gradient descent.
        Args:
            XPS (XPS): The XPS instance to use for tuning.
            emit (function): Function to emit data to the main thread.
            command (str): The command to execute.
            group (str): The positioner group to set the command for.
        """
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, np.array([self.position]))
        # self.waveformDP.generate_datafile("D:/Aldric/250818",
        #                                     "balance drift",
        #                                     1,
        #                                     self.name,
        #                                     "txt")
        # Main loop for the entire experiment
        # Move delay array to the correct position
        self.active_DLS.set_command("move absolute", self.position)
        # Collect data from the Picoscope for the number of repeats
        value = 0.000001
        while not self.stop_task:
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop tuning from the GUI
                if self.stop_task:
                    self.stop_task = False
                    # self.waveformDP.save_data()
                    del self.waveformDP
                    return
                processed_PS_signals = self.waveformDP.check_and_segment_data(
                    raw_signals)
                # Emit a dictionary to the main thread to be ploted
                emit({"time": ps_time, "signal": processed_PS_signals})
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()

            # Emit the data dictionary to main thread to be plotted
            emit(self.waveformDP.data)
            self.waveformDP.data["Delay (mm)"] = np.append(
                self.waveformDP.data["Delay (mm)"], self.position+value)
            value += 0.000001

class TuneAmplitude(Task):
    """
    Class for tuning amplitude.
    """
    def __init__(self, active_DLS):
        """
        """
        super().__init__(active_DLS, None, None)
        self.name = "Amplitude Tuning"
        self.repeats = defaults["tuning"]["Amplitude"]["repeats"]
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
            ps: PS4000):
        """
        This is the main function for running the amplitude tuning
        task.
        """
        # Generate the picoscope time array
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, np.array([self.position]))
        self.waveformDP.generate_datafile("D:/Aldric/250902",
                                            "balance drift",
                                            1,
                                            self.name,
                                            "txt")
        # Main loop for the entire experiment
        # Move delay array to the correct position
        self.active_DLS.set_command("move absolute", self.position)
        # Collect data from the Picoscope for the number of repeats
        value = 0.000001
        start = time()
        while not self.stop_task:
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop tuning from the GUI
                if self.stop_task or value == 0.01:
                    self.stop_task = False
                    end = time()
                    print(f"Time taken: {end - start} seconds")
                    self.waveformDP.save_data()
                    del self.waveformDP
                    return
                processed_PS_signals = self.waveformDP.check_and_segment_data(
                    raw_signals)
                # Emit a dictionary to the main thread to be ploted
                emit({"time": ps_time, "signal": processed_PS_signals})
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()

            # Emit the data dictionary to main thread to be plotted
            emit(self.waveformDP.data)
            self.waveformDP.data["Delay (mm)"] = np.append(
                self.waveformDP.data["Delay (mm)"], self.position+value)
            value += 0.000001

class TuneBandwidth(Task):
    """
    Class for tuning bandwidth.
    """
    def __init__(self, active_DLS):
        """
        """
        super().__init__(active_DLS, None, None)
        self.name = "Bandwidth Tuning"
        self.repeats = defaults["tuning"]["Bandwidth"]["repeats"]

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
            ps: PS4000):
        """
        This is the main function for running the amplitude tuning
        task.
        """
        # Generate the picoscope time array
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        print(self.position)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, np.array([self.position]))
        # Main loop for the entire experiment
        # Move delay array to the correct position
        self.active_DLS.set_command("move absolute", self.position)
        # Collect data from the Picoscope for the number of repeats
        value = 0.000001
        while not self.stop_task:
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop tuning from the GUI
                if self.stop_task:
                    self.stop_task = False
                    del self.waveformDP
                    return
                processed_PS_signals = self.waveformDP.check_and_segment_data(
                    raw_signals)
                # Emit a dictionary to the main thread to be ploted
                emit({"time": ps_time, "signal": processed_PS_signals})
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()

            # Emit the data dictionary to main thread to be plotted
            emit(self.waveformDP.data)
            self.waveformDP.data["Delay (mm)"] = np.append(
                self.waveformDP.data["Delay (mm)"], self.position+value)
            value += 0.000001