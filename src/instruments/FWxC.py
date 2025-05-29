from ctypes import *
import json as js
from src.instruments.instrument import Instrument

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

class FWxC(Instrument):
    """ Class for FWxC device"""
    FWxCLib = None
    isLoad = False

    @staticmethod
    def list_devices():
        """ List all connected FWxC devices
        Returns: 
            The FWxC device list, each deice item is [serialNumber, FWxCType]
        """
        str = create_string_buffer(1024, "\0") 
        result = FWxC.FWxCLib.List(str,1024)
        devicesStr = str.raw.decode("utf-8").rstrip("\x00").split(",")
        length = len(devicesStr)
        i = 0
        devices = []
        devInfo = ["",""]
        while(i < length):
            str = devicesStr[i]
            if (i % 2 == 0):
                if str != "":
                    devInfo[0] = str
                else:
                    i+=1
            else:
                    if(str.find("FWxC") >= 0):
                        isFind = True
                    devInfo[1] = str
                    devices.append(devInfo.copy())
            i+=1
        return devices
    
    @staticmethod
    def load_library(path):
        FWxC.FWxCLib = cdll.LoadLibrary(path)
        FWxC.isLoad = True

    def __init__(self):
        super().__init__("FWxC")
        self.type = "fw"
        if not FWxC.isLoad:
            FWxC.load_library("./src/instruments/instruments_dlls/" \
                               "FilterWheel102_win64.dll")
        self.hdl = -1

    def setup(self, serialNo: str, nBaud: int, timeout: int = 3) -> int:
        """ Open FWxC device
    Args:
        serialNo: serial number of FWxC device
        nBaud: bit per second of port
        timeout: set timeout value in (s)
    Returns: 
        non-negative number: hdl number returned Successful;
        negative number: failed.
    """
        ret = -1
        if FWxC.isLoad:
            ret = FWxC.FWxCLib.Open(serialNo.encode("utf-8"),
                                    nBaud, timeout)
        if ret >= 0:
            if serialNo == defaults["FWxC"]["fw1"]["serial port"]:
                self.name = "fw1"
            elif serialNo == defaults["FWxC"]["fw2"]["serial port"]:
                self.name = "fw2"
            self.status = f"Connect to FWxC at {serialNo} success."
            self.hdl = ret
        else:
            self.status = f"Connect to FWxC at {serialNo} fail."
            self.hdl = -1
        return ret

    def is_connected(self, serialNo: str) -> bool:
        """ Check opened status of FWxC device
        Args:
            serialNo: serial number of FWxC device
        Returns: 
            False: FWxC device is not opened; True: FWxC device is opened.
        """
        ret = -1
        if FWxC.isLoad:
            ret = FWxC.FWxCLib.IsOpen(serialNo.encode("utf-8"))
            if ret == 1:
                return True
            else:
                return False

    def close(self) -> int:
        """ Close opened FWxC device
        Returns: 
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = FWxC.FWxCLib.Close(self.hdl)
            if ret == 0:
                self.status = f"Close FWxC at {self.name} success."
            else:
                self.status = f"WARNING: Close FWxC at {self.name} fail!"
        return ret

    def set_command(self, command: str, value: str) :
        """ Execute command on the FWxC device
        Args:
            command: the command to execute
            value: the value to set
        Returns: 
            0: Success; negative number: failed.
        """
        match command:
            case("position"):
                # This command sets the filter position
                ret = FWxC.FWxCLib.SetPosition(self.hdl, int(value))

            case("position from filter"):
                # This command sets the filter position depending on the
                # filter value as mapped in the systemDefaults.json file
                filter_val = self.get_command("which position", value)
                ret = FWxC.FWxCLib.SetPosition(self.hdl, filter_val)
                if ret == 0:
                    self.status = (f"Set {self.name} to filter {value} at"
                                    f"position {filter_val}.")
                elif ret == 235:
                    self.status = (f"WARNING: {self.name} timed out setting"
                                f"filter {value} at position {filter_val}.\n"
                                f"It may have been set still, please check!")
                else:
                    self.status = (f"ERROR: {self.name} failed to set to"
                                   f"filter {value} at position"
                                   f"{filter_val}!")

    def get_command(self, command: str, value: str):
        """ Get command from the FWxC device
        Args:
            command: the command to eget
        Returns: 
            0: Success; negative number: failed.
        """
        match command:
            case("current position"):
                value = c_int(0)
                FWxC.FWxCLib.GetPosition(self.hdl, byref(value))
                return value.value

            case("which position"):
                for filter in defaults["FWxC"][self.name]["filters"]:
                    if (defaults["FWxC"][self.name]["filters"]
                        [filter]["value"] == value):
                        return int(filter)
                self.status = (f"Warning: filter {value} not found in"
                               f"{self.name}!\nFilter position value"
                               f"not found!")
            
            case("filter power value"):
                for filter in defaults["FWxC"][self.name]["filters"]:
                    if (defaults["FWxC"][self.name]["filters"]
                        [filter]["value"] == value):
                        return float(defaults["FWxC"][self.name]["filters"]
                                    [filter]["power"])
                self.status = (f"Warning: filter {value} not found in"
                               f"{self.name}!\nFilter power value not"
                               f"found!")