# The XPS controller controls multiple different stages, all of them
# are contolled through the same class.

from json.tool import main
import sys
import clr
from ctypes import *
from src.instruments.instrument import Instrument
import json as js
from System.Reflection import BindingFlags

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

# Add the DLL directory to the system path
DLL_DIRECTORY = (r"./src/instruments/instruments_dlls")
sys.path.append(DLL_DIRECTORY)

# Load the DLL
clr.AddReference("Newport.XPS.CommandInterface")
from CommandInterfaceXPS import XPS as XPS_DLL

class XPS(Instrument):
    def __init__(self):
        self.XPS = XPS_DLL()
        self.is_open = False

        # for debugging only
        # methods = self.XPS.GetType().GetMember("GroupPositionCurrentGet", BindingFlags.Public | BindingFlags.Instance)
        # for m in methods:
        #     print(m)

    def setup(self, address: str, port: int):
        """
        Open communications with the XPS device.
        Args:
        address (str): The address of the XPS device.
        port (int): The port number to connect to.
        Returns:
        0: if successful, -1 otherwise.
        """
        timeout = 1000
        result = self.XPS.OpenInstrument(address, port, timeout)
        if result == 0:
            self.is_open = True
            print('Open ', address, ":", port, " => Successful")
        else:
            print('Open ', address, ":", port, " => failure ", result)
        return result

    def close(self) -> int:
        """
        Close communications with the XPS device.
        Returns:
        0: if successful, -1 otherwise.
        """
        if self.is_open:
            result = self.XPS.CloseInstrument()
            if result == 0:
                print("XPS successfully closed.")
                self.is_open = False
            return result
        else:
            return -1

    def _check_group_status(self, group: str) -> int:
        """
        Check the status of a group.
        Args:
            group (str): The group to check the status of.
        Returns:
            status (int): The status code of the group.
        """
        # Check if stages are enabled
        status = self.XPS.GroupStatusGet(group)
        if status[0] != 0:
            print(f"Error getting status for {group}: {status[1]}")
            return status[0]
        match status[1]:
            case 0 | 1:
                print(f"{group} is not initialized")
            case 2:
                print("Stage has an emergency stop")
                # Print status here
            case 10| 11 | 12 | 13:
                print("Stage is ready")
            case 20 | 21:
                print("Stage is disabled")
            case 44:
                print("Stage is moving")
        return status

    def get_command(self, emit, command: str, group: str , **kwargs):
        """
        Get the command for the XPS device.
        Args:
            group (str): The positioner group to get the command for.
            command (str): The command to get.
        Returns:
            errstring (str): 0 if successful, error message otherwise.
        """
        errstring = ""

        match command:
            case "status data":
                data = self.XPS.GroupStatusGet(group)
                position = [0.0]
                status_string = ""
                position = self.XPS.GroupPositionCurrentGet(group, position, 1)
                status_string = self.XPS.GroupStatusStringGet(data[1], status_string)
                emit({"status": data[1],
                      "position": position[1][0],
                      "status string": status_string[1]})
            case _:
                print(f"Unknown command: {command}")
                return "Unknown command"
        
        return errstring

    def set_command(self, command: str, group: str, **kwargs) -> str:
        """
        Set the command for the XPS device.
        Args:
            group (str): The positioner group to set the command
            for.
            command (str): The command to set.
        Returns:
            errstring (str): 0 if successful.
        """
        errstring = ""
        status = self.XPS.GroupStatusGet(group)[1]
        match command:
            case "initialize & home":
                if status == 0 | 1:
                    print(f"{group} is already initialized.")
                    return
                errstring = self.XPS.GroupInitialize(group)[0]
                if errstring != 0:
                    return errstring
                errstring = self.XPS.GroupHomeSearch(group)[0]
                if errstring != 0:
                    status = self.XPS.GroupStatusGet(group)[1]
                    while status != 11:
                        status = self.XPS.GroupStatusGet(group)[1]
                    return
            case  "move relative":
                step = kwargs.get("step", 0.01)
                if step is None:
                    print("Step size is required for relative move.")
                    return
                if status not in [10, 11, 12, 13]:
                    print(f"{group} is not ready to move.")
                    return status
                errstring = self.XPS.GroupMoveRelative(group, [step], 1)[1]
                if errstring != "":
                    return errstring
                status = self.XPS.GroupStatusGet(group)[1]
                while status != 12:
                    status = self.XPS.GroupStatusGet(group)[1]
                    if status == 2:
                        print("Emergency stop detected, cannot move.")
                        return
            case "move absolute":
                position = kwargs.get("position", 0)
                if position is None:
                    print("Position is required for absolute move.")
                    return
                if status not in [10, 11, 12, 13]:
                    print(f"{group} is not ready to move.")
                    print(status)
                    return status
                errstring = self.XPS.GroupMoveAbsolute(group, [position], 1)[1]
                if errstring != "":
                    return errstring
                status = self.XPS.GroupStatusGet(group)[1]
                while status != 12:
                    status = self.XPS.GroupStatusGet(group)[1]
                    if status == 2:
                        print("Emergency stop detected, cannot move.")
                        return

        return errstring