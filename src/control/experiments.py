import json as js
import numpy as np
from PyQt6.QtWidgets import (
    QGridLayout, QLabel, QLineEdit, QGroupBox, QComboBox, QWidget
)
from src.instruments.DLS import DLS
from src.GUI.plotWidgets import PlotManager
from src.instruments.Picoscope4000 import PS4000
from src.instruments.SC10 import SC10
from src.instruments.FWxC import FWxC
from src.control.dataProcessing import WaveformDP
from src.GUI.usefulWidgets import RowContainer
from time import *

# TODO: Try to simplify the code

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

class Experiment:
    """
    Base class for all experiments.
    Follow this template when introducing new experiments.
    All experiments should inherit from this class.
    Methods include:
    - __init__: Initialize the experiment with sample attributes.
    - input_widget (class): Create the input widget for the experiment.
        - GUI: Create the input menu for the experiment.
        - check_inputs: Check the inputs for the experiment.
        - set_experiment_parameters: Set the parameters for the experiment.
    - main_delay_array: Generate a delay array for the experiment.
    - run: Run the experiment.
    """
    def __init__(self, active_DLS:DLS,
                 inactive_DLS: DLS,
                 sample_attributes: dict):
        """
        Initialize the experiment with sample attributes.
        Also sets up the parameters for the instruments for the experiment.
        """
        self.sample_attributes = sample_attributes
        #TODO: Consider making DLS into a list.
        # May be useful if we have more than 2 DLS
        self.name = None
        self.active_DLS = active_DLS
        self.inactive_DLS =inactive_DLS
        self.inactive_DL_position = None
        self.fw_positions = []
        self.delay_array = np.array([])
        self.repeats = 25
        self.stop_experiment = False
        self.next_experiment = False

    class input_widget:
        def __init__(self):
            """
            Create the input widget for the experiment.
            """
            raise NotImplementedError("input_widget method not implemented.")

        def check_inputs(self):
            """
            Check the inputs for the experiment.
            TODO: Include checks here
            """
            raise NotImplementedError("check_inputs method not implemented.")
        
        def set_experiment_parameters(self):
            """
            Set the parameters for the experiment.
            """
            raise NotImplementedError("set_experiment_parameters method not" \
            "implemented.")

    def main_delay_array(self,
                         initial_pos: list,
                         final_pos: list,
                         steps: list,
                         type: list = ["Linear"]):
        """
        Generate a delay array for the experiment.
        Allows for a combination of linear and logarithmic delay arrays.
        """
        for i in range(len(initial_pos)):
            if steps[i] <= 0:
                raise ValueError("Steps must be greater than 0.")
            if type[i] == "Linear":
                self.delay_array = np.append(self.delay_array,
                                             np.linspace(initial_pos[i],
                                                         final_pos[i],
                                                         steps[i]))                          
            elif type[i] == "Logarithmic":
                self.delay_array = np.append(self.delay_array,
                                             np.geomspace(initial_pos[i],
                                                         final_pos[i],
                                                         steps[i]))
            else:
                raise ValueError("Invalid delay array type.")
    
    def run(self,
            ps: PS4000,
            pump_shutter: SC10,
            fw1: FWxC,
            fw2: FWxC,
            data_plots: PlotManager,
            experiment_count: int =  None,
            save_dir: str = None,
            sample: str = None,
            save_type: str = ""):
        """
        This is the main function for running the experiment.
        This is written for a typical OPTP experiment. (As of May 2025)
        May need modifications for other experiments, do check.
        """
        # Generate the delay arrays
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        self.waveformDP = WaveformDP(self.name, self.delay_array)
        if save_dir is not None:
            self.waveformDP.generate_datafile(save_dir,
                                            sample,
                                            experiment_count,
                                            self.name,
                                            save_type)
        # Move inactive DLS to the correct position
        if self.inactive_DL_position is not None:
            self.inactive_DLS.set_command("move absolute",
                                            self.inactive_DL_position)
        # Setting filtr wheel positions as needed
        if len(self.fw_positions) != 0:
            fw1.set_command("position from filter", self.fw_positions[0])
            fw2.set_command("position from filter", self.fw_positions[1])
            pump_shutter.set_command("open")
        else:
            pump_shutter.set_command("close")
        for step in range(len(self.delay_array)):
            # Move delay array to the correct position
            self.active_DLS.set_command("move absolute",
                                        self.delay_array[step])
            # Collect data from the Picoscope for the number of repeats
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop the experiment from the GUI
                if self.stop_experiment or self.next_experiment:
                    self.next_experiment = False
                    if save_dir is not None:
                        self.waveformDP.save_data()
                    return
                # Plot the raw Picoscope signal
                data_plots.plots[2].update_plot([ps_time, raw_signals])
                # Segments and checks if for channel overrange.
                self.waveformDP.check_segment_data(raw_signals)
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()
                        
            #Update plots with relevant data
            data_plots.update_plots(self.waveformDP.data)

        if save_dir is not None:
            self.waveformDP.save_data()

class filterWheelWidget(QGroupBox):
    """ Class to create a widget to get filter wheels inputs. """
    def __init__(self, title: str = "Filter wheels settings"):
        super().__init__(title)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.OPTP_fw1 = QComboBox()
        self.OPTP_fw2 = QComboBox()
        for filter in defaults["FWxC"]["fw1"]["filters"]:
            self.OPTP_fw1.addItem(defaults["FWxC"]["fw1"]["filters"]
                                 [filter]["value"])
        for filter in defaults["FWxC"]["fw2"]["filters"]:
            self.OPTP_fw2.addItem(defaults["FWxC"]["fw2"]["filters"]
                                 [filter]["value"])

        self.layout.addWidget(QLabel("Filter wheel 1"), 0, 1)
        self.layout.addWidget(self.OPTP_fw1, 1, 1)
        self.layout.addWidget(QLabel("Filter wheel 2"), 0, 2)
        self.layout.addWidget(self.OPTP_fw2, 1, 2)

    def get_data(self):
        """
        Get the data from the filter wheels.
        """
        return [self.OPTP_fw1.currentText(), self.OPTP_fw2.currentText()]

class darkTHz(Experiment):
    """
    Class for the dark THz experiment.
    """
    def __init__(self,
                 active_DLS: DLS,
                 inactive_DLS: DLS = None,
                 sample_attributes: dict = {}):
        super().__init__(active_DLS, inactive_DLS, sample_attributes)
        self.name = "Dark THz"
    
    class input_widget:
        def __init__(self):
            """
            Create the input widget for the dark THz experiment.
            """
            self.GUI = self.GUI()
        
        def GUI(self):
            """ Create the input menu for the dark THz experiment. """
            darkTHz_widget = QGroupBox("Dark THz settings")
            darkTHz_widget_layout = QGridLayout()
            DLS125_box = QGroupBox("DLS125 settings")
            DLS125_boxlayout = QGridLayout()
            DLS125_box.setLayout(DLS125_boxlayout)
            darkTHz_widget_layout.addWidget(DLS125_box, 0, 0, 1, 5)
            darkTHz_widget_layout.setRowStretch(0|1|2|3|4|5, 1)
            darkTHz_widget.setLayout(darkTHz_widget_layout)

            self.DT_DLS125_initial = QLineEdit()
            self.DT_DLS125_final = QLineEdit()
            self.DT_step_count = QLineEdit()
            self.DT_step_count.setText(str(defaults["experiments"]["Dark THz"]
                                    ["step frequency"]))
            self.DT_repeats = QLineEdit()
            self.DT_repeats.setText(str(defaults["experiments"]["Dark THz"]
                                    ["repeats"]))
            
            DLS125_boxlayout.addWidget(QLabel("Initial position (mm)"), 0, 0)
            DLS125_boxlayout.addWidget(self.DT_DLS125_initial, 1, 0)
            DLS125_boxlayout.addWidget(QLabel("Final position (mm)"), 0, 1)
            DLS125_boxlayout.addWidget(self.DT_DLS125_final, 1, 1)
            DLS125_boxlayout.addWidget(QLabel("Step count"), 0, 2)
            DLS125_boxlayout.addWidget(self.DT_step_count, 1, 2)
            DLS125_boxlayout.addWidget(QLabel("Repeats"), 0, 3)
            DLS125_boxlayout.addWidget(self.DT_repeats, 1, 3)

            return darkTHz_widget

        def set_experiment_parameters(self, active_DLS: DLS):
            """
            Set the parameters for the dark THz experiment.
            This gives us the setting dictionary to display the info
            in the GUI, and also create an instance of the experiment class
            to be appended to a program list that we can run.
            """
            # self.check_inputs()
            self.settings = {}

            self.settings["active_DLS_initial"] = float(
                self.DT_DLS125_initial.text())
            self.settings["active_DLS_final"] = float(
                self.DT_DLS125_final.text())
            self.settings["active_DLS_steps"] = int(
                self.DT_step_count.text())
            self.settings["repeats"] = int(self.DT_repeats.text())

            darkTHz_instance = darkTHz(active_DLS)
            darkTHz_instance.repeats = self.settings["repeats"]
            darkTHz_instance.main_delay_array(
                [self.settings["active_DLS_initial"]],
                [self.settings["active_DLS_final"]],
                [self.settings["active_DLS_steps"]])

            return darkTHz_instance

class OPTP(Experiment):
    """
    Class for the OPTP experiment.
    """
    def __init__(self,
                 active_DLS: DLS,
                 inactive_DLS:DLS,
                 sample_attributes: dict = {}):
        super().__init__(active_DLS, inactive_DLS, sample_attributes)
        self.name = "OPTP"
    
    class input_widget:
        def __init__(self):
            """
            Create the input widget for the OPTP experiment.
            """
            self.GUI = self.GUI()

        def GUI(self):
            """ Create the input menu for the dark THz experiment. """
            OPTP_widget = QGroupBox("OPTP settings")
            OPTP_widget_layout = QGridLayout()
            DLS125_box = QGroupBox("DLS125 settings")
            DLS125_boxlayout = QGridLayout()
            DLS325_box = QGroupBox("DLS325 settings")
            DLS325_boxlayout = QGridLayout()
            self.fws_widget = filterWheelWidget()
            DLS125_box.setLayout(DLS125_boxlayout)
            DLS325_box.setLayout(DLS325_boxlayout)
            OPTP_widget_layout.addWidget(DLS325_box, 0, 0, 1, 1)
            OPTP_widget_layout.addWidget(self.fws_widget, 0, 1, 1, 3)
            OPTP_widget_layout.addWidget(DLS125_box, 1, 0, 1, 4)
            OPTP_widget.setLayout(OPTP_widget_layout)

            self.OPTP_DLS125_initial = QLineEdit()
            self.OPTP_DLS125_final = QLineEdit()
            self.OPTP_step_count = QLineEdit()
            self.OPTP_step_count.setText(str(defaults["experiments"]["OPTP"]
                                        ["step frequency"]))
            self.OPTP_repeats = QLineEdit()
            self.OPTP_repeats.setText(str(defaults["experiments"]["OPTP"]
                                        ["repeats"]))
            self.OPTP_DLS325_position = QLineEdit()

            DLS125_boxlayout.addWidget(QLabel("Initial position (mm)"), 0, 0)
            DLS125_boxlayout.addWidget(self.OPTP_DLS125_initial, 1, 0)
            DLS125_boxlayout.addWidget(QLabel("Final position (mm)"), 0, 1)
            DLS125_boxlayout.addWidget(self.OPTP_DLS125_final, 1, 1)
            DLS125_boxlayout.addWidget(QLabel("Step count"), 0, 2)
            DLS125_boxlayout.addWidget(self.OPTP_step_count, 1, 2)
            DLS125_boxlayout.addWidget(QLabel("Repeats"), 0, 3)
            DLS125_boxlayout.addWidget(self.OPTP_repeats, 1, 3)

            DLS325_boxlayout.addWidget(QLabel("Set position (mm)"), 0, 0)
            DLS325_boxlayout.addWidget(self.OPTP_DLS325_position, 1, 0)

            return OPTP_widget

        def set_experiment_parameters(self,
                                      active_DLS: DLS,
                                      inactive_DLS: DLS):
            """
            Set the parameters for the OPTP experiment.
            This gives us the setting dictionary to display the info
            in the GUI, and also create an instance of the experiment class
            to be appended to a program list that we can run.
            """
            # self.check_inputs()
            self.settings = {}

            self.settings["DLS125_initial"] = float(self.OPTP_DLS125_initial.
                                                    text())
            self.settings["DLS125_final"] = float(self.OPTP_DLS125_final.
                                                  text())
            self.settings["DLS125_steps"] = int(self.OPTP_step_count.text())
            self.settings["DLS125_repeats"] = int(self.OPTP_repeats.text())
            self.settings["DLS325_position"] = float(
                self.OPTP_DLS325_position.text())
            self.settings["fw1"] = self.fws_widget.get_data()[0]
            self.settings["fw2"] = self.fws_widget.get_data()[1]

            OPTP_instance = OPTP(active_DLS, inactive_DLS)
            OPTP_instance.repeats = self.settings["DLS125_repeats"]
            OPTP_instance.main_delay_array(
                [self.settings["DLS125_initial"]],
                [self.settings["DLS125_final"]],
                [self.settings["DLS125_steps"]])
            OPTP_instance.inactive_DL_position = self.settings[
                "DLS325_position"]
            OPTP_instance.fw_positions = [self.settings["fw1"],
                                         self.settings["fw2"]]

            return OPTP_instance

class pumpDecay(Experiment):
    """
    Class for the pump decay experiment.
    """
    def __init__(self,
                 active_DLS: DLS,
                 inactive_DLS:DLS,
                 sample_attributes: dict = {}):
        super().__init__(active_DLS, inactive_DLS, sample_attributes)
        self.name = "Pump decay"
    
    class input_widget:
        def __init__(self):
            """
            Create the input widget for the pump decay experiment.
            """
            self.GUI = self.GUI()

        def GUI(self):
            """ Create the input menu for the pump decay experiment """
            pumpDecay_widget = QGroupBox("Pump decay settings")
            pumpDecay_widget_layout = QGridLayout()
            DLS125_box = QGroupBox("DLS125 settings")
            DLS125_boxlayout = QGridLayout()
            repeats = QGroupBox("Repeats")
            repeats_layout = QGridLayout()
            DLS125_box.setLayout(DLS125_boxlayout)
            self.fws_widget = filterWheelWidget()
            repeats.setLayout(repeats_layout)
            pumpDecay_widget_layout.addWidget(DLS125_box, 0, 0, 1, 1)
            pumpDecay_widget_layout.addWidget(self.fws_widget, 0, 1, 1, 3)
            pumpDecay_widget_layout.addWidget(repeats, 0, 4, 1, 1)
            pumpDecay_widget.setLayout(pumpDecay_widget_layout)

            self.PD_repeats = QLineEdit()
            self.PD_repeats.setText(str(defaults["experiments"]["Pump decay"]
                                    ["repeats"]))

            self.PD_DLS125_position = QLineEdit()

            class DLS325_inputs(QWidget):
                """ Class to create rows for DLS325 inputs. """
                def __init__(self):
                    super().__init__()
                    self.layout = QGridLayout(self)

                    self.PD_DLS325_initial = QLineEdit()
                    self.PD_DLS325_final = QLineEdit()
                    self.PD_sampling_mode = QComboBox()
                    self.PD_sampling_mode.addItems(["Linear", "Logarithmic"])
                    self.PD_step_count = QLineEdit()
                    self.PD_step_count.setText(str(defaults["experiments"]
                                                ["Pump decay"]
                                                ["step frequency"]["low"]))
                    self.layout.addWidget(QLabel("Initial position\n(mm)"),
                                          0, 0)
                    self.layout.addWidget(self.PD_DLS325_initial, 1, 0)
                    self.layout.addWidget(QLabel("Final position\n(mm)"),
                                          0, 1)
                    self.layout.addWidget(self.PD_DLS325_final, 1, 1)
                    self.layout.addWidget(QLabel("Step count"), 0, 2)
                    self.layout.addWidget(self.PD_step_count, 1, 2)
                    self.layout.addWidget(QLabel("Sampling mode"), 0, 3)
                    self.layout.addWidget(self.PD_sampling_mode, 1, 3)

                def get_data(self):
                    data_list = []
                    for i in range(self.layout.count()):
                        widget = self.layout.itemAt(i).widget()
                        if isinstance(widget, QLineEdit):
                            data_list.append(float(widget.text()))
                        elif isinstance(widget, QComboBox):
                            data_list.append(widget.currentText())
                    return data_list

            self.row_container = RowContainer("DLS325 settings",
                                                DLS325_inputs)
            pumpDecay_widget_layout.addWidget(self.row_container, 1, 0, 1, 5)

            DLS125_boxlayout.addWidget(QLabel("Set position (mm)"), 0, 0)
            DLS125_boxlayout.addWidget(self.PD_DLS125_position, 1, 0)

            repeats_layout.addWidget(self.PD_repeats, 0, 0)

            return pumpDecay_widget
    
        def set_experiment_parameters(self,
                                      active_DLS: DLS,
                                      inactive_DLS: DLS):
            """
            Set the parameters for the OPTP experiment.
            This gives us the setting dictionary to display the info
            in the GUI, and also create an instance of the experiment class
            to be appended to a program list that we can run.
            """
            # self.check_inputs()
            self.settings = {"DLS325_initial": [], "DLS325_final": [],
                            "DLS325_steps": [], "sampling_mode": []}
            for row in self.row_container.rows:
                data = row.content_widget.get_data()
                self.settings["DLS325_initial"].append(data[0])
                self.settings["DLS325_final"].append(data[1])
                self.settings["DLS325_steps"].append(int(data[2]))
                self.settings["sampling_mode"].append(data[3])
            self.settings["DLS325_repeats"] = int(self.PD_repeats.text())
            self.settings["DLS125_position"] = float(
                self.PD_DLS125_position.text())
            self.settings["fw1"] = self.fws_widget.get_data()[0]
            self.settings["fw2"] = self.fws_widget.get_data()[1]

            PD_instance = pumpDecay(active_DLS, inactive_DLS)
            PD_instance.repeats = self.settings["DLS325_repeats"]
            PD_instance.main_delay_array(
                self.settings["DLS325_initial"],
                self.settings["DLS325_final"],
                self.settings["DLS325_steps"],
                self.settings["sampling_mode"])
            PD_instance.inactive_DL_position = self.settings[
                "DLS125_position"]
            PD_instance.fw_positions = [self.settings["fw1"],
                                         self.settings["fw2"]]

            return PD_instance