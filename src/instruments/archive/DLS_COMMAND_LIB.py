import sys
import clr
from ctypes import *
import time


# This is a wrapper for the Newport DLS Command Interface DLL.

# NOTE: Only implemented the commands needed.
# Way more commands are available in the DLL.
# Refer to the Command Interface documentation for more information.
# Implemented commands:
# OpenInstrument, CloseInstrument, AC_Get, AC_Set, PA_Get, PA_Set
# PD, PR_Set, ST, TB, TE, TH, TP, TS, VA_Get, VA_Set

# Add the DLL directory to the system path
DLL_DIRECTORY = (r"./src/instruments/instruments_dlls")
sys.path.append(DLL_DIRECTORY)

# Load the DLL
clr.AddReference("Newport.DLS.CommandInterface")

# Import the DLS class from the DLL
from CommandInterfaceDLS import DLS as DLS_DLL

class DLS:
    def __init__(self):
        self.dls_instance = DLS_DLL()
        self.is_open = False

    def open(self, device_key: str) -> int:
        """
        Open communications with the DLS device.
        Args:
        device_key (str): The COM port to connect to.
        Returns:
        0: if successful, -1 otherwise.
        """
        result = self.dls_instance.OpenInstrument(device_key)
        if result == 0:
            self.is_open = True
        return result

    def close(self) -> int:
        """
        Close communications with the DLS device.
        Returns:
        0: if successful, -1 otherwise.
        """
        if self.is_open:
            result = self.dls_instance.CloseInstrument()
            if result == 0:
                self.is_open = False
            return result
        else:
            return -1

    def is_open(self) -> bool:
        """
        Check connection status of DLS device
        Returns: 
            False: device is not connected; True: device is connected.
        """
        return self.is_open
    
    def AC_get(self) -> str:
        """
        Get the current acceleration value.
        returns:
            acceleration (str): The acceleration value if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.AC_Get()
        if command_out[0] == 0:
            return str(command_out[1])
        else:
            return command_out[2]
        
    def AC_set(self, acceleration: float) -> str:
        """
        Set the acceleration value.
        Args:
            acceleration (float): The acceleration value to set.
        Returns:
            errstring (str): empty if successful.
        """
        return self.dls_instance.AC_Set(acceleration)[1]
    
    def PA_get(self) -> str:
        """
        Get the target position of the DLS.
        Returns:
            position (str): The target position if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.PA_Get()
        if command_out[0] == 0:
            return str(command_out[1])
        else:
            return command_out[2]
        
    def PA_set(self, position: float) -> str:
        """
        Initiates an absolute move.
        When received, the positioner will move to the specified position,
        with the predefined acceleration and velocity
        Args:
            position (float): The target position value to set.
        Returns:
            errstring (str): empty if successful.
        """
        return self.dls_instance.PA_Set(position)[1]
    
    def PD(self, displacement: float) -> str: 
        """
        Initiates a relative move.
        When received, the positioner will move, with the predefined
        acceleration and velocity, to a new target position nn units
        away from the current target position.
        All others commands received by the Controller during PD command
        execution will be executed after the PD command response.
        Args:
            displacement (float): The target displacement value to set.
        Returns:
            errstring (str): The error string if unsuccessful.
        """
        return self.dls_instance.PD(displacement)[2]
    
    def PR_set(self, position: float) -> str:
        """
        Initiates a relative move.
        When received, the positioner will move, with the predefined
        acceleration and velocity, to a new target position nn units
        away from the current target position.
        Args:
            position (float): The target position value to set.
        Returns:
            errstring (str): The error string if unsuccessful.
        """
        return self.dls_instance.AC_Set(position)[1]    

    def ST(self) -> str:
        """
        Stop the DLS motion.
        Returns:
            errstring (str): The error string if unsuccessful.
        """
        return self.dls_instance.ST()[1]

    def TB(self, error_code: str) -> str:
        """
        returns a string that explains the meaning of the error code.
        Used in conjunction with TE command.
        Args:
            error_code (str): The error code to check.
        Returns:
            error_message (str)
        """
        return self.dls_instance.TB(error_code)[1]

    def TE(self) -> str:
        """
        Returns the error code of the last command.
        Returns:
            error_code (str)
        """
        return self.dls_instance.TE()[1]

    def TH(self) -> str:
        """
        Returns the value of the set-point or theoretical position.
        This is the position where the positioner should be.
        Returns:
            theoretical_position (str): The theoretical position if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.TH()
        if command_out[0] == 0:
            return str(command_out[1])
        else:
            return command_out[2]

    def TP(self) -> str:
        """
        Returns the value of the actual position.
        This is the position where the positioner is.
        Returns:
            actual_position (str): The actual position if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.TP()
        if command_out[0] == 0:
            return str(command_out[1])
        else:
            return command_out[2]

    def TS(self) -> str:
        """
        Get the status of the DLS.
        It can do more, but for this implementation, we only need the status.
        Returns:
            status (str): The status string if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.TS()
        if command_out[0] == 0:
            return command_out[3]
        else:
            return command_out[2]
        
    def VA_get(self) -> str:
        """
        Get the current velocity value.
        Returns:
            velocity (str): The velocity value if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.VA_Get()
        if command_out[0] == 0:
            return str(command_out[1])
        else:
            return command_out[2]

    def VA_set(self, velocity: float) -> str:
        """
        Set the velocity value.
        Args:
            velocity (float): The velocity value to set.
        Returns:
            errstring (str): empty if successful.
        """
        return self.dls_instance.VA_Set(velocity)[1]
    
    # ------ Custom methods ------
    # TODO: Fix the alignment mode method to use the new class structure.
    def alignment_mode(self, dwell: int = 1, cycle_num: int = 500) -> None:
        """
        Set the DLS to alignment mode.
        Moving the DLS stage between start and end.
        Args:
            dwell (int): Time to dwell at each position (in seconds).
            cycle_num (int): Number of cycles to perform.
        """
        if self.dls_instance.SN_Get()[1] == 17302001:
            motion_range = [0.5, 124.5]
        elif self.dls_instance.SN_Get()[1] == 18324044:
            motion_range = [0.5, 324.5]
        else:
            raise ValueError("Invalid DLS device serial number."
            "Please check if correct device connected.")
        for current_cycle in range(cycle_num):
            if self.dls_instance.PA_Set(motion_range[0]):
                while self.dls_instance.TS()[3] == '3C':
                    print(self.dls_instance.TP())
                time.sleep(dwell)

            if self.dls_instance.PA_Set(motion_range[1]):
                while self.dls_instance.TS()[3] == '3C':
                    print(self.dls_instance.TP())
                time.sleep(dwell)

            print(f"Cycle {current_cycle + 1} completed")
    
    # def tuning_mode(self,
    #                 motion_range: list,
    #                 cycle_time: int = 10,
    #                 cycle_num: int = 500) -> None:
    #     """
    #     Set the DLS to tuning the THz emitter and detector.
    #     Moving the DLS stage between two points at a high speed.
    #     Args:
    #         motion_range (list): The range of motion [start, end].
    #         cycle_time (int): Time for each cycle (in seconds).
    #         cycle_num (int): Number of cycles to perform.
    #     """
    #     if self.dls_instance.SN_Get() == 17302001:
    #         continue
    #     else:
    #         raise ValueError("Invalid DLS device serial number."
    #         "Please check if correct device connected.")
    #     for current_cycle in range(cycle_num):

    def calculate_time(self, displacement: float, steps: int) -> str:
        """
        Calculate the time needed to complete entire motion.
        Args:
            displacement (float): The target displacement value to set.
            steps (int): The number of steps to move.
        Returns:
            timeout (str): The time needed if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_instance.PTT(displacement)
        if command_out[0] == 0:
            # Convert the time to seconds and multiply by the number of steps
            return float(command_out[1])*steps
        else:
            return command_out[2]