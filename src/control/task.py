from src.instruments.DLS import DLS
from src.instruments.Picoscope4000 import PS4000
from src.instruments.SC10 import SC10
from src.instruments.FWxC import FWxC
from src.control.dataProcessing import WaveformDP
import numpy as np
from time import *

class Task:
    """
    Base class for all tasks, both experiments and tuning.
    Follow this template when introducing new tasks.
    All tasks should inherit from this class.
    Methods include:
    - __init__: Initialize the task (potentially with sample
                attributes).
    - input_widget (class): Create the input widget for the task.
        - GUI: Create the input menu for the task.
        - check_inputs: Check the inputs for the task.
        - set_task_parameters: Set the parameters for the task.
    - main_delay_array: Generate a delay array for the task.
    - run: Run the task.
    """
    def __init__(self, active_DLS:DLS,
                 inactive_DLS: DLS,
                 sample_attributes: dict):
        """
        Initialize the task with sample attributes.
        Also sets up the parameters for the instruments for the task.
        """
        self.sample_attributes = sample_attributes
        #TODO: Consider making DLS into a list.
        # May be useful if we have more than 2 DLS
        self.name = None
        self.active_DLS = active_DLS
        self.inactive_DLS = inactive_DLS
        self.inactive_DL_position = None
        self.fw_positions = []
        self.delay_array = np.array([])
        self.repeats = 25
        self.stop_task = False
        self.next_task = False

    class input_widget:
        def __init__(self):
            """
            Create the input widget for the task.
            """
            raise NotImplementedError("input_widget method not implemented.")

        def check_inputs(self):
            """
            Check the inputs for the task.
            TODO: Include checks here
            """
            raise NotImplementedError("check_inputs method not implemented.")
        
        def set_task_parameters(self):
            """
            Set the parameters for the task.
            """
            raise NotImplementedError("set_task_parameters method not" \
            "implemented.")

    def main_delay_array(self,
                         initial_pos: list,
                         final_pos: list,
                         steps: list,
                         type: list = ["Linear"]):
        """
        Generate a delay array for the task.
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
    
    def task_setup(self,
                    emit,
                    ps: PS4000,
                    pump_shutter: SC10,
                    fw1: FWxC,
                    fw2: FWxC):
        # Generate the picoscope time array
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, self.delay_array)
        # Setting filter wheel positions as needed and open up pump
        # shutter if it is required.
        if len(self.fw_positions) != 0:
            fw1.set_command("position from filter", self.fw_positions[0])
            fw2.set_command("position from filter", self.fw_positions[1])
            pump_shutter.set_command("open")
        else:
            # Otherwise, ensure pump shutter is closed.
            pump_shutter.set_command("close")


    def run(self,
            emit,
            ps: PS4000,
            pump_shutter: SC10,
            fw1: FWxC,
            fw2: FWxC,
            task_count: int =  None,
            save_dir: str = None,
            sample: str = None,
            save_type: str = ""):
        """
        This is the main function for running the task.
        This is written for a typical OPTP task. (As of May 2025)
        May need modifications for other tasks, do check.
        """
        # Generate the picoscope time array
        ps_time = np.linspace(0, (ps.max_samples - 1) * 0.0001,
                              ps.max_samples)
        # Create the data processing class instance
        self.waveformDP = WaveformDP(self.name, self.delay_array)
        # If save file enabled, create a data file for the current
        # task. If data file exists, this will fail.
        if save_dir is not None:
            self.waveformDP.generate_datafile(save_dir,
                                            sample,
                                            task_count,
                                            self.name,
                                            save_type)
        # Move inactive DLS to the correct position
        if self.inactive_DL_position is not None:
            self.inactive_DLS.set_command("move absolute",
                                            self.inactive_DL_position)
        # Setting filter wheel positions as needed and open up pump
        # shutter if it is required.
        if len(self.fw_positions) != 0:
            fw1.set_command("position from filter", self.fw_positions[0])
            fw2.set_command("position from filter", self.fw_positions[1])
            pump_shutter.set_command("open")
        else:
            # Otherwise, ensure pump shutter is closed.
            pump_shutter.set_command("close")
        start = time()
        # Main loop for the entire task
        for step in range(len(self.delay_array)):
            # Move delay array to the correct position
            self.active_DLS.set_command("move absolute",
                                        self.delay_array[step])
            # Collect data from the Picoscope for the number of repeats
            for repeat in range(self.repeats):
                raw_signals = ps.get_data()
                # This is a flag to stop the task from the GUI
                if self.stop_task or self.next_task:
                    self.next_task = False
                    if save_dir is not None:
                        # Save data if required
                        self.waveformDP.save_data()
                    del self.waveformDP
                    return
                # Emit a dictionary to the main thread to be ploted
                emit({"time": ps_time, "signal": raw_signals})
                self.waveformDP.check_and_segment_data(raw_signals)
            self.waveformDP.update_data()
            self.waveformDP.clear_buffers()

            # Emit the data dictionary to main thread to be plotted
            emit(self.waveformDP.data)

        end = time()
        print(f"Time taken: {end - start} seconds")

        if save_dir is not None:
            self.waveformDP.save_data()