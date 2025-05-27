try:
    import sys
    import numpy as np
    import json as js
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QTabWidget, QMainWindow
    )
    from PyQt6.QtGui import QFont
    from src.GUI.inputWidget import InputWidget
    from src.GUI.plotWidgets import PlotManager
    from PyQt6.QtCore import QTimer, QThreadPool
    # Import all instrument classes here
    from src.instruments.Picoscope4000 import PS4000 as ps
    from src.instruments.DLS import DLS
    from src.instruments.SC10 import SC10
    from src.instruments.FWxC import FWxC
    from src.control.experiments import *
    from src.control.worker import Worker
    from ctypes import *
    import qdarktheme
    import datetime
except OSError as ex:
    print("Warning:", ex)


with open(r'config\systemDefaults.JSON') as f:
    defaults = js.load(f)

class MainWindow(QMainWindow):
    """
    Main window for the application.
    """

    def __init__(self):
        """
        Initialize the main window and set up the layout and widgets.
        Also creates instances of instrument classes.
        """
        super().__init__()
        self.setWindowTitle("Joyce Lab Terahertz App (JoLTA)")
        self.resize(1900, 1000)

        # TODO: Setup instrument classes. Add all instruments here.
        self.ps4000 = ps()
        self.thz_dls = DLS()
        self.pump_dls = DLS()
        self.pump_shutter = SC10()
        self.pump_shutter.list_devices()
        self.fw1 = FWxC()
        self.fw2 = FWxC()
        self.fw1.list_devices()
        self.fw2.list_devices()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_run_settings_tab(), "Run Settings")
        self.tabs.addTab(self.create_data_collection_tab(), "Data plots")
        # self.tabs.addTab(self.compare_plots_tab(), "Compare plots")
        self.tabs.addTab(self.create_infomation_tab(), "Information")

        wid = QWidget(self)
        self.setCentralWidget(wid)
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        wid.setLayout(layout)

        self.timer = QTimer()

    def create_run_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        # Pass all instrument instances to the input widget
        self.main_menu = InputWidget(self.thz_dls,
                                     self.pump_dls)
        layout.addWidget(self.main_menu)
        self.main_menu.run_exp_button.clicked.connect(
            self.start_worker)
        tab.setLayout(layout)
        return tab

    def create_data_collection_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.data_plots = PlotManager()
        layout.addWidget(self.data_plots)
        tab.setLayout(layout)
        return tab
    
    def create_infomation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        return tab

    def start_worker(self):
        """
        Start the worker thread to run the experiment protocols.   
        """
        if self.main_menu.program_list == []:
            print("No experiments queued.")
            return
        
        else:
            # Swap tabs to show the data collection tab
            self.tabs.setCurrentIndex(1)
            self.data_plots.exp_stop_button.setEnabled(True)
            self.data_plots.exp_stop_button.clicked.connect(self.
                                                            set_kill_program)
            self.data_plots.next_exp_button.clicked.connect(self.
                                                            next_experiment)
            self.data_plots.data_dropdown.setEnabled(True)

            # Set up the thread pool and start the experiment protocols
            self.threadpool = QThreadPool()

            worker = Worker(self.run_program)  # Any other args, kwargs are passed to the run function
            # worker.signals.result.connect(self.print_output)
            # worker.signals.finished.connect(self.thread_complete)
            # worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)

    def wind_down(self):
        """
        Close all instrument connections, and save data as needed.
        """
        # TODO: Save data here
        # TODO: Close all instruments here
        self.ps4000.close()
        self.thz_dls.close()
        self.pump_dls.close()
        self.pump_shutter.close()
        self.fw1.close()
        self.fw2.close()

    def run_program(self):
        """
        This function will be called via "start worker" when the "Run"
        button is clicked.
        The flow of all the data collection and processing will be done
        here

        Rough flow:
        1. Get the parameters from the input menu
        2. Set up the data collection (e.g., open COM ports,
        set up devices)
        3. Start the data collection loop
            a. Collect data and process it in real-time
            b. Update the plots with the new data
        4. Handle stopping and resetting the data collection
        6. Save the data to a file if needed
        5. Close the devices and clean up

        If new experiments introduced, this is where to add them.
        """
        if self.main_menu.program_list == []:
            print("No experiments queued.")
            return

        # Open instrument connections
        # TODO: Open all instruments here
        self.thz_dls.setup(defaults["DLS"]["THz DLS"]["serial port"])
        self.pump_dls.setup(defaults["DLS"]["Pump DLS"]["serial port"])
        self.ps4000.setup()
        self.pump_shutter.setup(defaults["SC10"]["serial port"],
                                defaults["SC10"]["baud rate"])
        self.fw1.setup(defaults["FWxC"]["fw1"]["serial port"],
                       defaults["FWxC"]["fw1"]["baud rate"])
        self.fw2.setup(defaults["FWxC"]["fw2"]["serial port"],
                       defaults["FWxC"]["fw2"]["baud rate"])

        # Save metadata to a txt file
        if self.main_menu.save_CB.isChecked():
            try:
                with open(self.main_menu.dir_path_text.text() + "/" +
                        self.main_menu.sample_text.text() + " metadata.txt",
                        "x") as f:
                    f.write("Sample name: " +
                            self.main_menu.sample_text.text() + "\n")
                    f.write("Date: " + str(datetime.datetime.now()) + "\n")
                    f.write("Experiments:\n")
                    for index in range(self.main_menu.program_widget.count()):
                        f.write(f"{str(index+1)})")
                        f.write(self.main_menu.program_widget.item(index).
                                text() + "\n")
            except FileExistsError:
                self.experiment.stop_experiment = False
                print("File already exists. Please choose a different name.")
                self.wind_down()
                return

        experiment_count = 1
        for experiment in self.main_menu.program_list:
            self.experiment = experiment
            # Ensure next experiment button is correctly configured
            if len(self.main_menu.program_list) > 1:
                self.data_plots.next_exp_button.setEnabled(True)
            else:
                self.data_plots.next_exp_button.setEnabled(False)
            if self.main_menu.save_CB.isChecked():
                self.experiment.run(self.ps4000,
                                    self.pump_shutter,
                                    self.fw1,
                                    self.fw2,
                                    self.data_plots,
                                    experiment_count,
                                    self.main_menu.dir_path_text.text(),
                                    self.main_menu.sample_text.text(),
                                    self.main_menu.file_type.currentText())
                experiment_count += 1
            else:
                self.experiment.run(self.ps4000,
                                    self.pump_shutter,
                                    self.fw1,
                                    self.fw2,
                                    self.data_plots)
            if self.experiment.stop_experiment:
                break

        # Close connections to the instruments
        self.wind_down()

    def set_kill_program(self):
        """
        Set the kill_program flag to True to stop the experiment loop.
        Also reset buttons and UI elements as needed.
        Also closes instrument connections
        """
        self.data_plots.exp_stop_button.setEnabled(False)
        self.experiment.stop_experiment = True
    
    def next_experiment(self):
        """
        Move to the next experiment in the program list.
        """
        self.experiment.next_experiment = True
        if self.main_menu.program_list[-2] == self.experiment:
            self.data_plots.next_exp_button.setEnabled(False)

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        if self.main_menu.save_CB.isChecked():
            self.experiment.waveformDP.save_data()

def main():
    app = QApplication(sys.argv)
    #app.setFont(QFont("Helvetica", 10))
    qdarktheme.setup_theme() # Apply the dark theme
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()