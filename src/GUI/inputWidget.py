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

class InputWidget(QWidget):
    """ Widget to handle user inputs for the main GUI """
    
    def __init__(self, thz_dls: DLS , pump_dls: DLS):
        super().__init__()
        self.program_list = []
        self.thz_dls = thz_dls
        self.pump_dls = pump_dls
        self.layout = QGridLayout()
        self.layout.setRowStretch(0|1|2|3|4|5, 1)
        self.setLayout(self.layout)
        self.main_menu()

    def main_menu(self):
        """ Create the main input menu for the GUI """

        self.dir_path_text = QLineEdit()
        self.dir_path_text.setPlaceholderText("Enter folder path")

        select_dir_button = QPushButton("Browse")
        select_dir_button.clicked.connect(self.selectDirectoryDialog)

        self.sample_text = QLineEdit()
        self.sample_text.setPlaceholderText("Enter sample name")

        self.save_CB = QCheckBox("Save data as")
        self.save_CB.setChecked(False)

        self.file_type = QComboBox()
        self.file_type.addItems(["txt", "json", "hdf5"])
        self.file_type.setCurrentText("txt")

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

        self.is_ref = QCheckBox("Is reference sample?")
        self.is_ref.setChecked(False)
        self.layout.addWidget(self.is_ref, 2, 8)

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

    def select_experiment_type(self):
        """
        Show the input menu for the selected experiment
        TODO: Add new experiment input widget here for switching.
        """
        ctext = self.experiments.currentText()
        match ctext:
            case "Dark THz":
                self.experiment_stack.setCurrentIndex(0)
            case "Pump decay":
                self.experiment_stack.setCurrentIndex(1)
            case "OPTP":
                self.experiment_stack.setCurrentIndex(2)

    def selectDirectoryDialog(self):
        """ Open a file dialog to select a directory """
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Directory")
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)

        if file_dialog.exec():
            self.dir_path_text.setText(str(file_dialog.selectedFiles()[0]))

    def add_experiment(self):
        """
        Add the settings for the selected experiment to the list
        TODO: Add new experiment log into here. Follow the templates.
        Be careful about the DLS instance parsed into the
        set_experiment_parameters method. Active DLS first before the
        inactive one.
        """
        experiment = self.experiments.currentText()
        if experiment == "":
            print("No experiment selected")
        else:
            display_string = f" {experiment}\n    "
            match experiment:
                case "Dark THz":
                    self.program_list.append(self.darkTHz_widget.
                                             set_experiment_parameters(
                                                self.thz_dls
                                             ))
                    settings = self.darkTHz_widget.settings
                    display_string += (f"DLS125: "
                        f"{settings['active_DLS_initial']} mm to "
                        f"{settings['active_DLS_final']} mm, "
                        f"{settings['active_DLS_steps']} steps, "
                        f"{settings['repeats']} repeats\n")
                    self.program_widget.addItem(display_string)
                case "Pump decay":
                    self.program_list.append(self.PD_widget.
                                             set_experiment_parameters(
                                                self.pump_dls,
                                                self.thz_dls
                                             ))
                    settings = self.PD_widget.settings
                    display_string += (f"DLS125: "
                            f"{settings['DLS125_position']} mm; fw1: "
                            f"{settings['fw1']}, fw2: {settings['fw2']}\n"
                            f"    DLS325: {settings['DLS325_repeats']} "
                            f"repeats\n")
                    for i in range(len(settings["DLS325_initial"])):
                        display_string += (f"        - "
                            f"{settings['DLS325_initial'][i]} mm to "
                            f"{settings['DLS325_final'][i]} mm, "
                            f"{settings['DLS325_steps'][i]} steps, "
                            f"{settings["sampling_mode"][i]} sampling\n")
                    self.program_widget.addItem(display_string)
                case "OPTP":
                    self.program_list.append(self.OPTP_widget.
                                             set_experiment_parameters(
                                                 self.thz_dls,
                                                 self.pump_dls
                                             ))
                    settings = self.OPTP_widget.settings
                    display_string += ("DLS325: "
                        f"{settings['DLS325_position']} mm; fw1: "
                        f"{settings['fw1']}, fw2: {settings['fw2']}\n"
                        f"    DLS125: {settings['DLS125_initial']} mm to "
                        f"{settings['DLS125_final']} mm, "
                        f"{settings['DLS125_steps']} steps, "
                        f"{settings['DLS125_repeats']} repeats\n")
                    self.program_widget.addItem(display_string)

    def remove_experiment(self):
        """ Remove the selected experiment from list """
        selected_items = self.program_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            del self.program_list[self.program_widget.row(item)]
            self.program_widget.takeItem(self.program_widget.row(item))

    def check_file_exists(self, file_path: str):
        """
        Check if the file already exists and ask to overwrite the file
        """
        if os.path.exists(file_path):
            return True
        else:
            return False

def main():
   app = QApplication(sys.argv)
   window = InputWidget()
   window.show()
   sys.exit(app.exec())

if __name__ == "__main__":
   main()