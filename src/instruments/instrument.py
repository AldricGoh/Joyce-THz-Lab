# TODO: Create main class for all instruments
# Main methods: open, close, set, get data, get status

class Instrument:
    """ Base class for all instruments. """
    def __init__(self, name):
        # Types of instruments: Measurements, control and motion
        self.name = name
        self.type = None
        self.status = None
        self.is_connected = False
        self.data = None

    def setup(self):
        """ Setup the instrument. """
        raise NotImplementedError("Open method not implemented.")

    def is_connected(self) -> bool:
        """ Check if the instrument is connected. """
        return self.is_connected

    def close(self):
        """ Close the instrument. """
        raise NotImplementedError("Close method not implemented.")

    def set_command(self):
        """ Execute a command on the instrument. """
        raise NotImplementedError("Set command method not implemented for stage.")

    def get_command(self):
        """ Get command from the instrument. """
        raise NotImplementedError("Get command method not implemented.")

    def get_data(self):
        """ Get data from the instrument. """
        raise NotImplementedError("Get data method not implemented.")
    
    def check_status(self):
        """ Check the status of the instrument. """
        raise NotImplementedError("Check status method not implemented.")