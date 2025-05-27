from ctypes import *


# This is a wrapper for the Newport SC10 Command Interface DLL.

class MCM3000:
    mcm3000Lib = None
    isLoad = False
    isOpen = False

    @staticmethod
    def list_devices() -> list:
        """ List all connected mcm3000 devices
        Returns:
           The mcm3000 device list, each device item is serialNumber/COM
        """
        deviceCount = c_long(0)
        MCM3000.mcm3000Lib.FindDevices(byref(deviceCount))
        #print(deviceCount)
        return result

    @staticmethod
    def load_library(path):
        MCM3000.mcm3000Lib = cdll.LoadLibrary(path)
        MCM3000.isLoad = True

    def __init__(self):
        lib_path = "./src/instruments/instruments_dlls/ThorMCM3000.dll"
        if not MCM3000.isLoad:
            MCM3000.load_library(lib_path)
        self.hdl = -1

    def open(self, device: int = 0):
        """ Open MCM3000 device
        Args:
            device (int): 0 for 1st device (typically only 0)
        Returns: 
            non-negative number: hdl number returned Successful; negative number: failed.
        """
        ret = -1
        if MCM3000.isLoad:
            ret = MCM3000.mcm3000Lib.SelectDevice(device)
            if ret >= 0:

                self.hdl = ret
            else:
                self.hdl = -1
        return ret

    def is_open(self, serialNo):
        """ Check opened status of SC10 device
        Args:
            serialNo: serial number of SC10 device
        Returns: 
            0: SC10 device is not opened; 1: SC10 device is opened.
        """
        ret = False
        if MCM3000.isLoad:
           ret = MCM3000.isOpen
        return ret

    def close(self):
        """ Close opened MCM3000 device
        Returns: 
            True: Success; False: failed.
        """
        ret = False
        if self.hdl >= 0:
            ret = MCM3000.mcm3000Lib.TeardownDevice()
        return ret

    def Xposition(self, xpos: float):
        """ Set X position of MCM3000 device
        Args:
            xpos (float): X position in mm
        Returns: 
            True: Success; False: failed.
        """
        ret = False
        MCM3000.mcm3000Lib.SetParam("Param_X_POS", c_double(xpos/10.0))
        MCM3000.mcm3000Lib.PreflightPosition()
        MCM3000.mcm3000Lib.SetupPosition()
        MCM3000.mcm3000Lib.StartPosition()
        return ret