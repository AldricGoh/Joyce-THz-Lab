from struct import pack,unpack
from turtle import position
import serial
import time
from src.instruments.instrument import Instrument


# Constants for PLS operation
Scale_Factor = 4735.597 # Encoder Counts/mm for PLS-X
channel_x = 0
channel_y = 1

class MCM3000(Instrument):
	'''
	Class for controlling the MCM3000 PLSXY stage. 

	This class is a wrapper for the MCM3000 PLSXY stage and provides
	methods for initializing the stage, getting position, absolute
	moves, and checking status. 
	'''
	def __init__(self, name):
		super().__init__(name)
		self.type = "motion stage"
		self.hdl = None

	def setup(self, port, baud_rate=115200, byte_size=8, stop_bits=1):
		Parity = serial.PARITY_NONE
		try:
			stage = serial.Serial(port=port,
							baudrate=baud_rate,
							bytesize=byte_size,
							parity=Parity,
							stopbits=stop_bits,
							timeout=0.1)
			time.sleep(0.1)
			if stage.is_open:
				self.hdl = stage
				return 
			else:
				print(f"Failed to open port {port}.")
				return
		except serial.SerialException as e:
			print(f"Error connecting to {self.name} at {port}: {e}")
			return None

	def _in_motion(self, chan_num):
		'''
		Methods returns 0 if the stage is not in motion and 1 if in motion
		'''

		GetStatus_id = 0x0480
		Get_Motor_Status = pack('<HBBBB',GetStatus_id,chan_num,0x00,0x00,0x00)
		self.hdl.write(Get_Motor_Status)
		str1,return_status,str2 = unpack('<16sB3s',self.hdl.read(20))
		if return_status != 0:
			return_status=1

		return return_status

	def set_command(self, command: str, **kwargs):
		""" Execute command on the MCM3000 device
        Args:
            command: the command to execute
            value: the value to set
        """
		match command:
			case("define x position"):
                # This command sets the x encoder count to a user defined value.
				# Setting the encoder_value parameter to 0 will take the current
				# stage position as being home position.
				# Absolute moves would be in reference to that position of the
				# stage.

				encoder_value = kwargs.get("value", 0)
				SetEncoderCount_id = 0x0409
				SetEncoderCount = pack('<HBBBBHi', SetEncoderCount_id, 0x06, 0x00, 0x00,
									0x00, channel_x, encoder_value)
				self.hdl.write(SetEncoderCount)

				return
			
			case("define y position"):
                # This command sets the y encoder count to a user defined value.
				# Setting the encoder_value parameter to 0 will take the current
				# stage position as being home position.
				# Absolute moves would be in reference to that position of the
				# stage.

				encoder_value = kwargs.get("value", 0)
				SetEncoderCount_id = 0x0409
				SetEncoderCount = pack('<HBBBBHi', SetEncoderCount_id, 0x06, 0x00,
						   0x00, 0x00, channel_y, encoder_value)
				self.hdl.write(SetEncoderCount)

				return

			case("move absolute x position"):
				# This command moves the stage to an absolute x position in mm.
				abs_pos = kwargs.get("value")*Scale_Factor
				Move_Absolute_id = 0x0453
				device_units = int(abs_pos)
				Move_Absolute = pack('<HBBBBHi',Move_Absolute_id,0x06,0x00,0x00,0x00,
						 channel_x,device_units)
				self.hdl.write(Move_Absolute)

				while self._in_motion(channel_x):
					time.sleep(0.01)
				return

			case("move absolute y position"):
				# This command moves the stage to an absolute y position in mm.
				abs_pos = kwargs.get("value")*Scale_Factor
				Move_Absolute_id = 0x0453
				device_units = int(abs_pos)
				Move_Absolute = pack('<HBBBBHi',Move_Absolute_id,0x06,0x00,0x00,0x00,
						 channel_y,device_units)
				self.hdl.write(Move_Absolute)

				while self._in_motion(channel_y):
					time.sleep(0.01)
				return

	def get_command(self, command: str, value: str):
		""" Get command from the FWxC device
		Args:
			command: the command to eget
		Returns: 
			0: Success; negative number: failed.
		"""
		match command:
			case("current x position"):
				# Returns the positions of the stage in mm
				GetPosition_id = 0x040A
				self.hdl.write(pack('<HBBBB',
						GetPosition_id,channel_x,0x00,0x00,0x00))
				Rx = self.hdl.read(12)
				header, chan_dent, position_dUnits = unpack('<6sHi',Rx)
				return float(position_dUnits)/Scale_Factor

			case("current y position"):
				# Returns the positions of the stage in mm
				GetPosition_id = 0x040A
				self.hdl.write(pack('<HBBBB',
						GetPosition_id,channel_y,0x00,0x00,0x00))
				Rx = self.hdl.read(12)
				header, chan_dent, position_dUnits = unpack('<6sHi',Rx)
				return float(position_dUnits)/Scale_Factor