try:
    import sys
    sys.path.append('./src/instruments')
    from DLS_COMMAND_LIB import *
    from Picoscope4000 import ps4000 as ps
    import time
    from ctypes import *
    import numpy as np
    import matplotlib.pyplot as plt
except OSError as ex:
    print("Warning:", ex)

# COM port definitions
DLS125 = "COM11"
DLS325 = "COM5"

# Set up parameters
repeats = 15 # Number of times to repeat the measurement. Each repeat is 10 measurements
delay = [35, 37]
steps = 100 # Number of steps in the delay
delay_array = np.linspace(delay[0], delay[1], steps) # Create an array of delay values

plt.ion() # Turn on interactive mode for live updates

# Create time data
ps_time = np.linspace(0, (80000 - 1) * 0.0001, 80000)
ps_buffer = (c_int16 * 80000)()

dark_THz_signal = []
# delay = []
# fig, ax = plt.subplots()
# ps_graph = ax.plot(delay,dark_THz_signal,color = 'g')[0]

def main():

    fig, ax = plt.subplots()
    ps_graph = ax.plot(ps_time,ps_buffer,color = 'g')[0]
    plt.xlabel('Time (ms)')
    plt.ylabel('ADC Counts')
    plt.xlim(35, 37)

    # Create instances of the DLS interface
    thz_dls = DLS()
    pump_dls = DLS()

    # Open connections to the instruments
    thz_dls.open(DLS125)
    pump_dls.open(DLS325)

    thz_dls.set_mode(0) # Set the mode to 0 for THz DLS

    ps4000 = ps()
    ps4000.setup()

    for step in range(delay_array.size):
        thz_dls.PA_set(delay_array[step])
        checking_buffer = 0
        while checking_buffer != 47:
            checking_buffer = int(thz_dls.TS())
        raw_signals = ps4000.collect_data(repeats)

        # removing the older graph
        ps_graph.remove()
        #ps_graph = ax.plot(delay,dark_THz_signal,color = 'g')[0]
        ps_graph = ax.plot(delay_array[:step+1],dark_THz_signal,color = 'g')[0]
        plt.pause(0.01) # Pause for a short time to allow the graph to update

    time.sleep(0.1)

    ps4000.close()

    print(dark_THz_signal)

    # Close connections to the instruments
    thz_dls.close()
    pump_dls.close()


if __name__ == "__main__":
    main()