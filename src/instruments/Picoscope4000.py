try:
    import sys
    import json as js
    from picosdk.ps4000 import ps4000 as ps
    from picosdk.functions import adc2mV, assert_pico_ok
    from src.instruments.instrument import Instrument
    from ctypes import *
    import numpy as np
except OSError as ex:
    print("Warning:", ex)


# TODO: Add method to measure total sampling duration
# TODO: add method to change channel range

with open(r'config/systemDefaults.json') as f:
    defaults = js.load(f)

# For information on the PicoSDK, please refer to the programmer guide

class PS4000(Instrument):
    """ Class for PicoScope 4000 series (4262) device"""

    chandle = c_int16()  # Handle for the PicoScope device

    def __init__(self):
        super().__init__("PicoScope 4262")
        self.type = "PicoScope"
        self.status = {}
        self.pulse_duration = defaults["main laser"]["pulse duration"]
        self.sampling_mode = defaults["experiments"]["OPTP"]
        self.trigger = defaults["picoscope"]["trigger"]

        self.max_samples = int(self.pulse_duration *
                               self.sampling_mode["pulses"] *
                               self.sampling_mode["sampling counts"]/
                               defaults["picoscope"]["timebase"])

        self.output = (c_int16 * self.max_samples)()

    def setup(self, range:str = "PS4000_10V") -> None:
        """ Set up picoscope 4262 device
        Returns: 
            0 if success, or relevant error code if failed
        """
        self.status["openunit"] = ps.ps4000OpenUnit(
            byref(self.chandle))
        assert_pico_ok(self.status["openunit"])
        self.is_connected = True
        
        # Set up channel A
        self.status["setChA"] = ps.ps4000SetChannel(self.chandle,
                                     ps.PS4000_CHANNEL["PS4000_CHANNEL_A"],
                                     1,
                                     ps.PICO_COUPLING["AC"],
                                     ps.PS4000_RANGE[range])
        assert_pico_ok(self.status["setChA"])
        
        # Set up trigger
        self.status["setTrigger"] = ps.ps4000SetSimpleTrigger(
                                        self.chandle,
                                        1,
                                        ps.PS4000_CHANNEL["PS4000_EXTERNAL"],
                                        self.trigger["trigger threshold"],
                                        2, # trigger direction rising edge
                                        self.trigger["trigger delay"],
                                        self.trigger["autotrigger"])
        assert_pico_ok(self.status["setTrigger"])

    def close(self) -> None:
        """ Close picoscope 4262 device
        Args:
            chandle (c_int): Handle of device to close
        Returns: 
            0 if success, or relevant error code if failed
        """
        if self.is_connected:
            self.status["stop"] = ps.ps4000Stop(self.chandle)
            assert_pico_ok(self.status["stop"])
            
            # Close the PicoScope device
            self.status["close"] = ps.ps4000CloseUnit(self.chandle)
            assert_pico_ok(self.status["close"])
            self.is_connected = False

    def get_data(self, bits2Volts:bool= False) -> np.ndarray:
        """
        Collect data from picoscope 4262 device. Current implementation
        is the block mode.
        """
        # Set up overflow buffer for data collection
        min_buffer = (c_int16 * self.max_samples)()
        # Run block mode capture
        self.status["runBlock"] = ps.ps4000RunBlock(self.chandle,
                                self.trigger["pretrigger samples"],
                                (self.max_samples -
                                self.trigger["pretrigger samples"]),
                                0, 0, None, 0, None, None)
        assert_pico_ok(self.status["runBlock"])

        ready = c_int16(0)
        check = c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps4000IsReady(self.chandle,
                                                        byref(ready))

        self.status["setDataBuffersA"] = ps.ps4000SetDataBuffers(
                                            self.chandle,
                                            ps.PS4000_CHANNEL
                                            ["PS4000_CHANNEL_A"],
                                            byref(self.output),
                                            byref(min_buffer),
                                            self.max_samples)
        assert_pico_ok(self.status["setDataBuffersA"])

        # create overflow loaction
        overflow = c_int16()
        cmaxsamples = c_int32(self.max_samples)

        # Get data from the device
        self.status["getValues"] = ps.ps4000GetValues(self.chandle,
                                    0,
                                    byref(cmaxsamples),
                                    1,
                                    0,
                                    0,
                                    byref(overflow))
        assert_pico_ok(self.status["getValues"])

        # Convert the ADC counts data to mV if enabled
        if bits2Volts:
            maxADC = c_int16(32767)
            self.output =  adc2mV(self.output,
                                    ps.PS4000_RANGE["PS4000_10V"],
                                    maxADC)

        return np.array(self.output, dtype=np.int16)