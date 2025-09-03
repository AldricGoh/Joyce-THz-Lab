from struct import pack,unpack
import serial
import time

def Initialize(Port,Baud_Rate=115200,ByteSize=8,StopBits=1):

	'''
	Intializes the stage and returns a Serial object for communicating
	with the controller. 

	The Port settings default to the correct values for the PLS-X. The only
	requires input parameter is the relevent COM port the stage is assigned. 

	'''
	
	baud_rate = Baud_Rate
	data_bits = ByteSize
	stop_bits = StopBits
	Parity = serial.PARITY_NONE
	stage = serial.Serial(port = Port, baudrate = baud_rate, bytesize=data_bits, parity=Parity, stopbits=stop_bits,timeout=0.1)
	print(stage)
	return stage

def Set_Encoder_Count(Stage,chan_num,encoder_value):

	'''
	Allows setting the encoder count to a user defined value. 

	Setting the encoder_value parameter to 0 will take the current
	stage position as being home position. Absolute moves would be in refernece
	to that posiion of the stage. 
	'''

	SetEncoderCount_id = 0x0409
	SetEncoderCount = pack('<HBBBBHi',SetEncoderCount_id,0x06,0x00,0x00,0x00,Channel,encoder_value)
	Stage.write(SetEncoderCount)

	return	

def getPositionDU(Stage,chan_num):

	'''
	Returns the positions of the stage in device units(Encoder Counts)

	diving the retuned values by the Counts/mm scale factor will yield
	a value in real units. 

	'''


	GetPosition_id = 0x040A

	Stage.write(pack('<HBBBB',GetPosition_id,Channel,0x00,0x00,0x00))
	Rx = Stage.read(12)
	header, chan_dent, position_dUnits = unpack('<6sHi',Rx)
	return float(position_dUnits)

def Absolute_Move(Stage,chan_num,ScaleFactor,abs_pos,wait=True):

	'''
	Method for moving to an Absolute Position. abs_pos should be in units of millimeters
	
	'wait' is an optional parameter and defaults to True, which means the Method
	will wait for the stage to complete the move to the requested position before
	advancing in the program. 

	A wait=False argument will result in the program immediately advancing. 
	This can be useful if you needed to take data in the program while the stage
	is moving. 
	'''

	Move_Absolute_id = 0x0453
	device_units = int(abs_pos*Scale_Factor) # mm position*conversion to encoder counts
	Move_Absolute = pack('<HBBBBHi',Move_Absolute_id,0x06,0x00,0x00,0x00,chan_num,device_units)
	Stage.write(Move_Absolute)

	Status=1
	stopped = 0
	#Waits until the current position is within absolute position by 5um for 3 positions
	if wait:
		while stopped < 3:

			if abs((abs_pos-getPositionDU(Stage,chan_num)/ScaleFactor)) <0.005:
				stopped +=1

		return 

	#wait=False, Absolute_Move will return immediately after the command is sent 
	#Program will not wait for motor to stop before advancing
	else:
		return

def getStatus(Stage,chan_num):

	'''
	Methods returns 0 if the stage is not in motion and 1 if in motion
	'''

	GetStatus_id = 0x0480
	Get_Motor_Status = pack('<HBBBB',GetStatus_id,chan_num,0x00,0x00,0x00) 
	Stage.write(Get_Motor_Status)
	str1,return_status,str2 = unpack('<16sB3s',Stage.read(20))
	if return_status != 0:
		return_status=1


	return return_status



Com_Port = 'COM4'
Scale_Factor = 4735.597 # Encoder Counts/mm for PLS-X
Channel = 0 # Channel 1 indexes at 0

#Intialize PlS-X Stage 
PLS_X = Initialize(Com_Port)

#Set Encoder Count to 0
Set_Encoder_Count(PLS_X,Channel,0)
time.sleep(0.1)

#Get Position Before Move
Position = getPositionDU(PLS_X,Channel)/Scale_Factor
print('Position: %.4f mm' % (Position))

#Move Stage to 5 mm
pos = -5 #mm

Absolute_Move(PLS_X,Channel,Scale_Factor,pos)

#Get Position After Move
Position = getPositionDU(PLS_X,Channel)/Scale_Factor
print('Position: %.4f mm' % (Position))


del PLS_X