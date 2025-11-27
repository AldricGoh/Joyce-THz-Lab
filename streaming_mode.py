import ctypes
from ctypes import *
import numpy as np
import time
import matplotlib.pyplot as plt
from picosdk.ps4000 import ps4000 as ps
from picosdk.functions import adc2mV, assert_pico_ok

# Load driver
ps = ctypes.windll.ps4000

# Handle for device
handle = c_int16()
status = ps.ps4000OpenUnit(byref(handle))
if status != 0:
    raise OSError(f"ps4000OpenUnit failed (status={status})")

print(f"Opened PicoScope 4262 (handle={handle.value})")

# Configure channel A (enabled, DC, 5V range, 0 offset)
chA = c_int16(0)  # PS4000_CHANNEL_A
enabled = c_int16(1)
dcCoupling = c_int16(1)  # PS4000_DC
range_5V = c_int16(7)    # check programmer's guide for enum
status = ps.ps4000SetChannel(handle, chA, enabled, dcCoupling, range_5V)
if status != 0:
    raise OSError(f"ps4000SetChannel failed (status={status})")

# Set simple trigger on channel A, rising, threshold 1000 ADC counts
status = ps.ps4000SetSimpleTrigger(handle, 1, chA, 1000, 2, 0, 0)
if status != 0:
    raise OSError(f"ps4000SetSimpleTrigger failed (status={status})")

# Streaming setup
sampleInterval = c_uint32(100)  # 100 ns
timeUnits = c_int16(0)          # PS4000_NS
preTriggerSamples = c_uint32(0)
postTriggerSamples = c_uint32(80000)  # 0.8s @ 10MS/s
autoStop = c_int16(1)
downSampleRatio = c_uint32(1)
ratioMode = c_int16(0)  # PS4000_RATIO_MODE_NONE
overviewBufferSize = postTriggerSamples

status = ps.ps4000RunStreaming(
    handle,
    byref(sampleInterval),
    timeUnits,
    preTriggerSamples,
    postTriggerSamples,
    autoStop,
    downSampleRatio,
    ratioMode,
    overviewBufferSize
)
if status != 0:
    raise OSError(f"ps4000RunStreaming failed (status={status})")

print("Streaming started... waiting for trigger")

# Allocate buffers
totalSamples = postTriggerSamples.value
bufferA = (c_int16 * totalSamples)()

# Wrap buffer to Python array
cbuf_ptr = ctypes.cast(bufferA, ctypes.POINTER(c_int16))

# Callback prototype
def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
    """Called when new samples are ready"""
    global collected, done
    for i in range(noOfSamples):
        collected[startIndex + i] = bufferA[startIndex + i]
    if autoStop:
        done = True
    return 0

CALLBACK = ctypes.WINFUNCTYPE(
    None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p
)
cb_func = CALLBACK(streaming_callback)

# Register buffers for channel A
status = ps.ps4000SetDataBuffers(
    handle, chA, bufferA, None, totalSamples
)
if status != 0:
    raise OSError(f"ps4000SetDataBuffers failed (status={status})")

# Start timing
t0 = time.time()

# Collect data
collected = np.zeros(totalSamples, dtype=np.int16)
done = False
while not done:
    ps.ps4000GetStreamingLatestValues(handle, cb_func, None)
    time.sleep(0.01)  # be nice to CPU

t1 = time.time()

print(f"Acquisition complete in {t1 - t0:.3f} seconds")

# Convert ADC counts to volts
# Get ADC conversion factor
maxADC = c_int16()
ps.ps4000MaximumValue(handle, byref(maxADC))
adc_max = maxADC.value
voltage_range = 5.0  # 5 V full scale
voltages = collected.astype(np.float32) / adc_max * voltage_range

# Create time axis
times = np.arange(totalSamples) * sampleInterval.value * 1e-9  # seconds

# Plot
plt.figure(figsize=(10,5))
plt.plot(times, voltages, lw=0.7)
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("PicoScope 4262 Streaming Capture")
plt.show()

# Stop and close
ps.ps4000Stop(handle)
ps.ps4000CloseUnit(handle)