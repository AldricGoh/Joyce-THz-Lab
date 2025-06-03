# TODO: make this info widget to display relevant information as experiment goes on

import sys
import json as js
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QCheckBox,
    QGroupBox, QLabel, QComboBox, QFileDialog, QLineEdit, QListWidget, 
)
from PyQt6.QtGui import QFont


with open(r"config\systemDefaults.JSON") as f:
    defaults = js.load(f)

class InfoWidgets:
    """ Widgets to display information for the main GUI """
    class WaveformInfo(QGroupBox):
        """ Widget to display waveform information """
        def __init__(self,
                     name: str = "Waveform Information",
                     columns: int = 2,
                     fontsize: int = 12):
            """ Initialize the waveform information widget """
            super().__init__(name)
            self.setStyleSheet(f""" QLabel {{
                               font-size: {fontsize}pt;
                               }} """)
            self.layout = QGridLayout()
            self.setLayout(self.layout)
            self.variables = {"Saturation": QLabel("All good"),
                              "Balance": QLabel("0.0"),
                              "E_off max": QLabel("0.0"),
                              "E_off min": QLabel("0.0"),
                              "E_on max": QLabel("0.0"),
                              "E_on min": QLabel("0.0"),
                              "DT max": QLabel("0.0"),
                              "DT min": QLabel("0.0")}

            for i, key in enumerate(self.variables.keys()):
                row = i // columns
                black_col = i % columns
                col = black_col * 2
                self.layout.addWidget(QLabel(f"{key}:"), row, col)
                self.layout.addWidget(self.variables[key], row, col+1)

        def update_info(self, data: dict):
            """ Update the waveform information widget with new data """
            if data["Saturation"]:
                self.variables["Saturation"].setText(
                    "WARNING! Channel overrange!")
            self.variables["Balance"].setText(f"{data["A"][-1]:.3f}")
            for key in ["E_off", "E_on", "DT"]:
                self.variables[f"{key} max"].setText(
                    f"{data[f"{key} max"][0]:.3f} @ "
                    f"{data[f"{key} max"][1]:.3f} mm")
                self.variables[f"{key} min"].setText(
                    f"{data[f"{key} min"][0]:.3f} @ "
                    f"{data[f"{key} min"][1]:.3f} mm")

    def __init__(self):
        self.WaveformInfo = InfoWidgets.WaveformInfo("Waveform Information")
    