# Use of Ophir COM object. 
# Works with python 3.5.1 & 2.7.11
# Uses pywin32
import win32gui
import win32com.client
import time
import traceback


OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
# Stop & Close all devices
OphirCOM.StopAllStreams() 
OphirCOM.CloseAll()
 # Scan for connected Devices
DeviceList = OphirCOM.ScanUSB()
print(DeviceList)
for Device in DeviceList:   	# if any device is connected
   DeviceHandle = OphirCOM.OpenUSBDevice(Device)	# open first device
   exists = OphirCOM.IsSensorExists(DeviceHandle, 0)
   if exists:
      print('\n----------Data for S/N {0} ---------------'.format(Device))

   # An Example for Range control. first get the ranges
      ranges = OphirCOM.GetRanges(DeviceHandle, 0)
      print (ranges)
      # change range at your will
      # if ranges[0] > 0:
      #    newRange = ranges[0]-1
      # else:
      newRange = 3 #ranges[0]+1
         # set new range
      OphirCOM.SetRange(DeviceHandle, 0, newRange)
      
      # An Example for data retrieving
      OphirCOM.StartStream(DeviceHandle, 0)		# start measuring
      for i in range(10):		
         time.sleep(.2)				# wait a little for data
         data = OphirCOM.GetData(DeviceHandle, 0)
      if len(data[0]) > 0:		# if any data available, print the first one from the batch
         print('Reading = {0}, TimeStamp = {1}, Status = {2} '.format(data[0][0] ,data[1][0] ,data[2][0]))
      
   else:
      print('\nNo Sensor attached to {0} !!!'.format(Device))

win32gui.MessageBox(0, 'finished', '', 0)
# Stop & Close all devices
OphirCOM.StopAllStreams()
OphirCOM.CloseAll()
# Release the object
OphirCOM = None
