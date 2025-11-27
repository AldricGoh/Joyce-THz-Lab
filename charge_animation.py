# Simulates motion of three charges in a plane - does not cope with
# the case when any two of the charges collide, will produce entirely
# spurious results if this happens

# Uncomment the next line if running in a notebook
# %matplotlib inline
import numpy as np
import math
import matplotlib.pyplot as plt
import warnings

# Ignore irritating warning
warnings.filterwarnings("ignore", ".*GUI is implemented.*")

# Charge A - charge, position, velocity, mass
ca = 100e-9
pa = np.array([0, 1])
va = np.array([0, 0])
ma = 1

# Charge B - charge, position, velocity, mass
cb = -120e-9
pb = np.array([1, 0])
vb = np.array([0, 0])
mb = 1

# Charge D - charge, position, velocity, mass
cd = 150e-9
pd = np.array([-1, -1])
vd = np.array([0, 0])
md = 1

# Permittivity of free space
e0 = 8.85418727e-12

# Simulation parameters - time step, integration method,
# iteration counter, display interval
dt = 0.1
verlet = True
i = 0
di = 100

# Initialise empty lists to record trajectories
tra = []
trb = []
trd = []

# Loop indefinitely, ctrl-c to interrupt
while True:

    # Update plots
    if i == 0:  # plot starting points

        plt.figure(1)
        plt.clf()
        plt.xlabel('x (m)')
        plt.ylabel('y (m)')
        plt.grid()
        plt.plot(pa[0], pa[1], 'b*')
        plt.plot(pb[0], pb[1], 'r*')
        plt.plot(pd[0], pd[1], 'g*')
        plt.axis('equal')
        plt.pause(0.0001)

    elif i % di == 0:  # plot trajectory segments

        # Convert trajectory lists into arrays,
        # so they can be sliced and plotted
        tra_array = np.array(tra)
        trb_array = np.array(trb)
        trd_array = np.array(trd)
        tra = []
        trb = []
        trd = []
        plt.plot(tra_array[:, 0], tra_array[:, 1], 'b')
        plt.plot(trb_array[:, 0], trb_array[:, 1], 'r')
        plt.plot(trd_array[:, 0], trd_array[:, 1], 'g')
        plt.pause(0.0001)

    # Force on A due to B and D
    fa = (pa-pb) * ca*cb/(4*math.pi*e0*math.pow(np.linalg.norm(pa-pb), 3))
    fa = fa + (pa-pd) * ca*cd/(4*math.pi*e0*math.pow(np.linalg.norm(pa-pd), 3))

    # Force on B due to A and D
    fb = (pb-pa) * cb*ca/(4*math.pi*e0*math.pow(np.linalg.norm(pb-pa), 3))
    fb = fb + (pb-pd) * cb*cd/(4*math.pi*e0*math.pow(np.linalg.norm(pb-pd), 3))

    # Force on D due to A and B
    fd = (pd-pa) * cd*ca/(4*math.pi*e0*math.pow(np.linalg.norm(pd-pa), 3))
    fd = fd + (pd-pb) * cd*cb/(4*math.pi*e0*math.pow(np.linalg.norm(pd-pb), 3))

    if verlet:

        # Verlet integration - better than Euler. If you are
        # interested in how it works, look it up on the web or wait
        # for the long vacation "Mars Lander" programming exercise.

        if i == 0:  # first iteration, no previous value, fall back to Euler

            pa_next = pa + dt*va
            pb_next = pb + dt*vb
            pd_next = pd + dt*vd

        else:  # subsequent iterations, use Verlet method

            pa_next = 2*pa - pa_prev + fa/ma*dt*dt
            pb_next = 2*pb - pb_prev + fb/mb*dt*dt
            pd_next = 2*pd - pd_prev + fd/md*dt*dt

        pa_prev = pa
        pb_prev = pb
        pd_prev = pd
        pa = pa_next
        pb = pb_next
        pd = pd_next

    else:

        # Simple Euler update rules - not very accurate!
        # It is just position = position + velocity * delta_t,
        # and velocity = velocity + acceleration * delta_t. You will
        # see better ways of numerically integrating equations of
        # motion in the long vacation "Mars Lander" programming exercise.

        pa = pa + dt*va
        pb = pb + dt*vb
        pd = pd + dt*vd
        va = va + dt*fa/ma
        vb = vb + dt*fb/mb
        vd = vd + dt*fd/md

    # Append new positions to trajectory lists, increment iteration counter
    tra.append(pa)
    trb.append(pb)
    trd.append(pd)
    i = i + 1