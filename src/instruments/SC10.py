from ctypes import *
from src.instruments.instrument import Instrument

class SC10(Instrument):
    """ Class for SC10 device """
    sc10Lib = None
    isLoad = False

    @staticmethod
    def list_devices():
        """ List all connected mcm301 devices
        Returns:
           The mcm301 device list, each device item is serialNumber/COM
        """
        str1 = create_string_buffer(10240)
        result = SC10.sc10Lib.List(str1, 10240)
        devicesStr = str1.value.decode("utf-8",
                                       "ignore").rstrip('\x00').split(',')
        length = len(devicesStr)
        i = 0
        devices = []
        devInfo = ["", ""]
        while i < length:
            str2 = devicesStr[i]
            if i % 2 == 0:
                if str2 != '':
                    devInfo[0] = str2
                else:
                    i += 1
            else:
                devInfo[1] = str2
                devices.append(devInfo.copy())
            i += 1
        return devices

    @staticmethod
    def load_library(path):
        SC10.sc10Lib = cdll.LoadLibrary(path)
        SC10.isLoad = True

    def __init__(self):
        super().__init__("SC10")
        self.type = "Shutter"
        lib_path = "./src/instruments/instruments_dlls/SC10CommandLib_x64.dll"
        if not SC10.isLoad:
            SC10.load_library(lib_path)
        self.hdl = -1

    def setup(self, serialNo: str, nBaud: int, timeout=20):
        """ Setup the SC10 device
        Args:
            serialNo: serial number of SC10 device
            nBaud: the bit per second of port
            timeout: set timeout value in (s)
        Returns: 
            non-negative number: hdl number returned Successful;
            negative number: failed.
        """
        ret = -1
        if SC10.isLoad:
            ret = SC10.sc10Lib.Open(serialNo.encode('utf-8'), nBaud, timeout)
            if ret >= 0:
                self.hdl = ret
            else:
                self.hdl = -1
        return ret

    def is_connected(self, serialNo: str) -> bool:
        """ Check opened status of SC10 device
        Args:
            serialNo: serial number of SC10 device
        Returns: 
            False: SC10 device is not opened;
            True: SC10 device is opened.
        """
        ret = -1
        if SC10.isLoad:
            ret = SC10.sc10Lib.IsOpen(serialNo.encode('utf-8'))
            if ret == 1:
                return True
            else:
                return False

    def _toggle_enable(self) -> int:
        """ Enable/Disable the shutter
        Args:
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = SC10.sc10Lib.ToggleEnable(self.hdl)
        return ret

    def _get_closed_state(self) -> int:
        """  Get closed state
        Returns:
            1: shutter is closed; 0: shutter is open; -1: failed.
        """
        if self.hdl >= 0:
            state_val = c_int(0)
            SC10.sc10Lib.GetClosedState(self.hdl, byref(state_val))
            return state_val.value
        else:
            return -1

    def set_command(self, command: str) -> int:
        """ Set command to SC10 device
        Args:
            command: command string
            value: value of command
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            match command:
                case "open":
                    if self._get_closed_state() == 1:
                        ret = self._toggle_enable()

                case "close":
                    if self._get_closed_state() == 0:
                        ret = self._toggle_enable()

        return ret

    def close(self) -> int:
        """ Close opened SC10 device
        Returns: 
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            self.set_command("Close shutter")
            ret = SC10.sc10Lib.Close(self.hdl)
        return ret