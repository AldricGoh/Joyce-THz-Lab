try:
    import sys
    import numpy as np
    import json as js
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QTabWidget, QMainWindow
    )
    from src.GUI.inputWidgets import (
        InputWidget, TuningInputWidget
    )
    from src.GUI.plotWidgets import PlotManager
    from PyQt6.QtCore import QTimer, QThreadPool
    # Import all instrument classes here
    from src.instruments.Picoscope4000 import PS4000 as ps
    from src.instruments.DLS import DLS
    from src.instruments.SC10 import SC10
    from src.instruments.FWxC import FWxC
    from src.instruments.XPS import XPS
    from src.control.dataProcessing import WaveformDP
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

        self.threadpool = QThreadPool.globalInstance()

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
        self.XPS = XPS()
        # Setup XPS here
        self.XPS.setup(defaults["XPS"]["address"], defaults["XPS"]["port"])

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_run_settings_tab(), "Run Settings")
        self.tabs.addTab(self.create_data_collection_tab(), "Data plots")
        # self.tabs.addTab(self.compare_plots_tab(), "Compare plots")
        self.tabs.addTab(self.create_tuning_tab(), "Tuning")

        wid = QWidget(self)
        self.setCentralWidget(wid)
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        wid.setLayout(layout)

        # self.timer = QTimer()

    def create_run_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        # Pass all instrument instances to the input widget
        self.main_menu = InputWidget(self.thz_dls,
                                     self.pump_dls)
        layout.addWidget(self.main_menu)
        self.main_menu.run_exp_button.clicked.connect(
            self.start_exp_worker)
        self.main_menu.tuning_input_widget.run_tune_button.clicked.connect(
            self.start_tuning_worker)
        tab.setLayout(layout)
        return tab

    def create_data_collection_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.data_panel = PlotManager()
        for item in self.data_panel.THz_signal_data.checklist.keys():
            self.data_panel.THz_signal_data.checklist[
                item].stateChanged.connect(self.data_panel.update_plots)
        for item in self.data_panel.THz_spectra_data.checklist.keys():
            self.data_panel.THz_spectra_data.checklist[
                item].stateChanged.connect(self.data_panel.update_plots)
        
        # Functionality of the QWP balance buttons
        self.data_panel.balance_tuning_widget.QWP_reset_button.clicked.connect(
            self.initialise_and_home_QWP)
        self.data_panel.balance_tuning_widget.QWP_move_absolute_button.clicked.connect(
            self.move_absolute_QWP)
        self.data_panel.balance_tuning_widget.QWP_reduce_step.clicked.connect(
            self.reduce_QWP_step)
        self.data_panel.balance_tuning_widget.QWP_add_step.clicked.connect(
            self.add_QWP_step)


        xps_worker = Worker(self.XPS_data_worker)
        xps_worker.signals.processed_data.connect(self.data_panel.
                                                  balance_tuning_widget.
                                                  update_data)
        self.threadpool.start(xps_worker)
        layout.addWidget(self.data_panel)
        tab.setLayout(layout)
        return tab
    
    def create_tuning_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        # self.tuning_widget = TuningManager()
        # layout.addWidget(self.tuning_widget)
        tab.setLayout(layout)
        return tab

    def XPS_data_worker(self, emit):
        """
        This function will be called to acquire data from the XPS.
        It will run in a separate thread.
        """
        while self.XPS.is_open:
            self.XPS.get_command(emit, "status data", defaults["XPS"]["QWP"])

    def start_exp_worker(self):
        """
        Start the worker thread to run the experiment protocols.   
        """
        if self.main_menu.program_list == []:
            print("No experiments queued.")
            return
        
        else:
            # Swap tabs to show the data collection tab
            self.tabs.setCurrentIndex(1)
            self.data_panel.exp_stop_button.setEnabled(True)
            self.data_panel.exp_stop_button.clicked.connect(self.
                                                            set_kill_program)
            self.data_panel.next_exp_button.clicked.connect(self.
                                                            next_experiment)
            self.data_panel.data_dropdown.setEnabled(True)
            # Reset the saturation warning
            self.data_panel.info_widget.variables["Saturation"].setText(
                "All good")

            # Any other args, kwargs are passed to the run function
            worker = Worker(self.run_program)
            worker.signals.processed_data.connect(self.data_panel.
                                                  update_plots)
            processing_worker = Worker(self.)
            # worker.signals.finished.connect(self.thread_complete)
            # worker.signals.progress.connect(self.progress_fn)
            # Execute
            self.threadpool.start(worker)

    def start_tuning_worker(self):
        """
        Start the worker thread to run the tuning protocols.
        """
        #TODO: Include checks for inputs
        
        # Swap tabs to show the data collection tab
        self.tabs.setCurrentIndex(1)
        self.data_panel.exp_stop_button.setEnabled(True)
        self.data_panel.exp_stop_button.clicked.connect(self.
                                                        set_stop_tune)
        self.data_panel.data_dropdown.setEnabled(True)
        # Reset the saturation warning
        self.data_panel.info_widget.variables["Saturation"].setText(
            "All good")

        # Any other args, kwargs are passed to the run function
        match self.main_menu.tuning_input_widget.tune_selection.currentText():
            case "Amplitude":
                worker = Worker(self.tune_setup_amplitude)
        worker.signals.processed_data.connect(self.data_panel.
                                                update_plots)
        # worker.signals.finished.connect(self.thread_complete)
        # worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def open_instruments(self):
        """
        Set up all the instruments and equipment needed for the experiment.
        This function is called when the "Run" button is clicked.
        """
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

    def run_program(self, emit):
        """
        This function will be called via "start_exp_worker" when the
        "Run" button is clicked.
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
        """
        if self.main_menu.program_list == []:
            print("No experiments queued.")
            return

        self.open_instruments()

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
                self.experiment.stop_task = False
                print("File already exists. Please choose a different name.")
                self.wind_down()
                return

        experiment_count = 1
        for experiment in self.main_menu.program_list:
            self.experiment = experiment
            # Ensure next experiment button is correctly configured
            if len(self.main_menu.program_list) > 1:
                self.data_panel.next_exp_button.setEnabled(True)
            else:
                self.data_panel.next_exp_button.setEnabled(False)
            if self.main_menu.save_CB.isChecked():
                self.experiment.run(emit,
                                    self.ps4000,
                                    self.pump_shutter,
                                    self.fw1,
                                    self.fw2,
                                    experiment_count,
                                    self.main_menu.dir_path_text.text(),
                                    self.main_menu.sample_text.text(),
                                    self.main_menu.file_type.currentText())
                experiment_count += 1
            else:
                self.experiment.run(emit,
                                    self.ps4000,
                                    self.pump_shutter,
                                    self.fw1,
                                    self.fw2)
            if self.experiment.stop_task:
                self.experiment.stop_task = False
                break

        # Close connections to the instruments
        self.wind_down()
        self.data_panel.exp_stop_button.setEnabled(False)
        return

    def process_data(self, ps_raw_output: np.ndarray):
        """
        Process the raw data from the PicoScope.
        """
        pass

    def tune_setup_amplitude(self, emit):
        # TODO: Complete tuning amplitude program
        self.open_instruments()

        self.main_menu.tuning_input_widget.tune_amplitude.run(emit,
                                                            self.ps4000)
        
        self.wind_down()
        self.data_panel.exp_stop_button.setEnabled(False)
        return

    def tune_setup_bandwidth(self, emit):
        # TODO: Complete tuning bandwidth program
        pass

    def knife_edge(self, emit):
        # TODO: Complete knife edge program
        pass

    def update_plots(self, data):
        """
        Update the plots with new data.
        This function is called by the worker thread when new data is available.
        """
        self.data_panel.update_plots(data)

    def set_kill_program(self):
        """
        Set the kill_program flag to True to stop the experiment loop.
        Also reset buttons and UI elements as needed.
        Also closes instrument connections
        """
        self.data_panel.exp_stop_button.setEnabled(False)
        self.experiment.stop_task = True
    
    def set_stop_tune(self):
        """
        Set the kill_program flag to True to stop the tuning loop.
        Also reset buttons and UI elements as needed.
        Also closes instrument connections
        """
        self.data_panel.exp_stop_button.setEnabled(False)
        self.main_menu.tuning_input_widget.tune_amplitude.stop_task = True
    
    def next_experiment(self):
        """
        Move to the next experiment in the program list.
        """
        self.experiment.next_task = True
        if self.main_menu.program_list[-2] == self.experiment:
            self.data_panel.next_exp_button.setEnabled(False)

    # These are functions to control the QWP
    # TODO: There might be a need to shift these into threads to avoid GUI from hanging
    def initialise_and_home_QWP(self):
        """ Initialize and home the QWP stage. """
        self.XPS.set_command("initialize & home", defaults["XPS"]["QWP"])

    def move_absolute_QWP(self):
        """ Move the QWP to an absolute position. """
        self.XPS.set_command("move absolute", defaults["XPS"]["QWP"],
                              position=float(
                                  self.data_panel.balance_tuning_widget.QWP_move_absolute_position.text()))
        
    def reduce_QWP_step(self):
        """ Reduce the QWP position by a relative step. """
        self.XPS.set_command("move relative", defaults["XPS"]["QWP"],
                             step=-float(
                                 self.data_panel.balance_tuning_widget.QWP_move_relative_step.text()))

    def add_QWP_step(self):
        """ Add the QWP position by a relative step """
        self.XPS.set_command("move relative", defaults["XPS"]["QWP"],
                                 step=float(
                                     self.data_panel.balance_tuning_widget.QWP_move_relative_step.text()))

    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        # TODO: Handle closing the main window, ensuring all data is
        # saved and instruments are closed properly.
        if self.main_menu.save_CB.isChecked():
            self.experiment.waveformDP.save_data()
        self.XPS.close()

def main():
    app = QApplication(sys.argv)
    #app.setFont(QFont("Helvetica", 10))
    qdarktheme.setup_theme() # Apply the dark theme
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()