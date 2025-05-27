import sys
import clr
from ctypes import *
from src.instruments.instrument import Instrument
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

class DLS(Instrument):
    def __init__(self):
        self.dls_dll = DLS_DLL()

    def setup(self, device_key: str) -> int:
        """
        Open communications with the DLS device.
        Args:
        device_key (str): The COM port to connect to.
        Returns:
        0: if successful, -1 otherwise.
        """
        result = self.dls_dll.OpenInstrument(device_key)
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
            result = self.dls_dll.CloseInstrument()
            if result == 0:
                self.is_open = False
            return result
        else:
            return -1

    def _TB(self, error_code: str) -> str:
        """
        returns a string that explains the meaning of the error code.
        Used in conjunction with TE command.
        Args:
            error_code (str): The error code to check.
        Returns:
            error_message (str)
        """
        return self.dls_dll.TB(error_code)[1]

    def _TS(self) -> str:
        """
        Get the status of the DLS.
        It can do more, but for this implementation, we only need the
        status.
        Returns:
            status (str): The status string if successful.
            errstring (str): The error string if unsuccessful.
        """
        command_out = self.dls_dll.TS()
        if command_out[0] == 0:
            return command_out[3]
        else:
            return command_out[2]

    def set_command(self, command: str, value: float) -> str:
        """
        Set the command for the DLS device.
        Args:
            command (str): The command to set.
            value (float): The value to set.
        Returns:
            errstring (str): empty if successful.
        """
        errstring = ""
        status = ""
        match command:
            case "move absolute":
                errstring = self.dls_dll.PA_Set(value)[1]
                if errstring != "":
                    return self._TB(errstring)
                while status != "47":
                    status = self._TS()

        return errstring