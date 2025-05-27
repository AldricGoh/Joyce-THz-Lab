# TODO: make this info widget to display relevant information as experiment goes on

import sys
import json as js
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QCheckBox,
    QLabel, QComboBox, QFileDialog, QLineEdit, QListWidget
)
from src.GUI.usefulWidgets import ResizingStackedWidget
from src.instruments.DLS import DLS
# Import experiment classes here
from src.control.experiments import (
    darkTHz, OPTP, pumpDecay
)
import os


with open(r'config\systemDefaults.JSON') as f:
    defaults = js.load(f)

class InfoWidget(QWidget):
    """ Widget to display information for the main GUI """
    
    def __init__(self, thz_dls: DLS , pump_dls: DLS):
        super().__init__()
        self.program_list = []
        self.thz_dls = thz_dls
        self.pump_dls = pump_dls
        self.layout = QGridLayout()
        self.layout.setRowStretch(0|1|2|3|4|5, 1)
        self.setLayout(self.layout)
        self.info_menu()

    def info_menu(self):
        """ Create the main input menu for the GUI """

        self.dir_path_text = QLineEdit()
        self.dir_path_text.setPlaceholderText("Enter folder path")

        select_dir_button = QPushButton("Browse")
        select_dir_button.clicked.connect(self.selectDirectoryDialog)

        self.sample_text = QLineEdit()
        self.sample_text.setPlaceholderText("Enter sample name")

        self.save_CB = QCheckBox("Save data as")
        self.save_CB.setChecked(True)

        self.file_type = QComboBox()
        self.file_type.addItems(["txt", "json", "hdf5"])
        self.file_type.setCurrentText("hdf5")

        self.experiments = QComboBox()
        self.experiments.addItems(defaults["experiments"].keys())
        self.experiments.activated.connect(self.select_experiment_type)

        self.program_widget = QListWidget()
        self.add_experiment_button = QPushButton("Add\nexperiment")
        self.add_experiment_button.clicked.connect(self.add_experiment)
        self.remove_experiment_button = QPushButton("Remove\nexperiment")
        self.remove_experiment_button.clicked.connect(
            self.remove_experiment)

        self.run_exp_button = QPushButton("Run experiments")
        
        self.layout.addWidget(QLabel('Folder:'), 0, 0)
        self.layout.addWidget(self.dir_path_text, 0, 1, 1, 10)
        self.layout.addWidget(select_dir_button, 0, 11)

        self.layout.addWidget(QLabel('Experiment Name:'), 1, 0)
        self.layout.addWidget(self.sample_text, 1, 1, 1, 9)
        self.layout.addWidget(self.save_CB, 1, 10)
        self.layout.addWidget(self.file_type, 1, 11)

        self.layout.addWidget(self.run_exp_button, 2, 0)
        self.layout.addWidget(QLabel('Sampling Mode:'), 2, 6)
        self.layout.addWidget(self.experiments, 2, 7)

        self.layout.addWidget(self.program_widget, 3, 0, 5, 5)
        self.layout.addWidget(self.add_experiment_button, 3, 5)
        self.layout.addWidget(self.remove_experiment_button, 4, 5)
        
        # TODO: Add new experiment input widget here. Follow the templates.
        self.experiment_stack = ResizingStackedWidget(self)
        self.darkTHz_widget = darkTHz.input_widget()
        self.OPTP_widget = OPTP.input_widget()
        self.PD_widget = pumpDecay.input_widget()
        self.layout.addWidget(self.experiment_stack, 3, 6, 3, 5)
        self.experiment_stack.addWidget(self.darkTHz_widget.GUI)
        self.experiment_stack.addWidget(self.PD_widget.GUI)
        self.experiment_stack.addWidget(self.OPTP_widget.GUI)
        self.experiment_stack.adjustSize()