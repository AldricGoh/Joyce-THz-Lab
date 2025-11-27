import json as js
from src.instruments.MCM3000 import MCM3000
import numpy as np

# -------------------- Setup --------------------
x_pos = 12.2591
y_pos = 28.5
# -----------------------------------------------

with open(r"config/systemDefaults.json") as f:
    defaults = js.load(f)

MCM3000 = MCM3000("MCM3000")

# x mid point = 14.8
# y mid point = 15.5

MCM3000.setup(defaults["MCM3000"]["serial port"])
print(MCM3000.get_command("current x position"))
print(MCM3000.get_command("current y position"))

MCM3000.set_command("move absolute x position", value = x_pos)
print("X position:", MCM3000.get_command("current x position"))
MCM3000.set_command("move absolute y position", value = y_pos)
print("Y position:", MCM3000.get_command("current y position"))