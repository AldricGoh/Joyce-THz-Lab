from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QComboBox, QLabel, QGroupBox,
)
import pyqtgraph as pg
from src.GUI.usefulWidgets import ResizingStackedWidget ,QCheckList
from src.GUI.infoWidget import InfoWidgets
import numpy as np

# TODO: Colour code different segments of Picoscope signals
# TODO: Add heatmap plot for spot size plot

colors = ["b", "r", "g"]

class LivePlot(QWidget):
    def __init__(self,
                 flag: str = None,
                 is_main: bool = False,
                 toolbar: bool= False):
        super().__init__()
        self.previous_flag = None
        self.flag = flag
        self.is_main = is_main
        self.plot_type = "line"
        self.data = None
        self.legend = None

        # Initailise the plot widget
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.setTitle(flag)
        # This lines ensures entire plot widget is visible
        self.plotWidget.getPlotItem().layout.setContentsMargins(
            10, 10, 10, 10)
            # Add a legend if it is the main widget
        if self.is_main:
            self.plotWidget.addLegend()

        # This dictionary holds the information that can be plotted
        # for the given flag
        self.dataplots = {"THz Signals": {"E_off": None,
                                          "E_on": None,
                                          "DT": None,
                                          "x_axis": "Delay (mm)"},
                          "THz Spectra" :{"E_off Spectrum": None,
                                          "E_on Spectrum": None,
                                          "DT Spectrum": None,
                                          "x_axis": "Frequency (THz)"},
                          "Picoscope signal": {"signal": None,
                                               "x_axis": "time"}}

        # If enabled, the toolbar will be added to the plot
        if toolbar:
            self.dropdown = QComboBox()
            self.dropdown.addItems(["Line", "Scatter", "Line + Points"])
            self.dropdown.currentTextChanged.connect(self.change_plot_type)
            controls_layout = QGridLayout()
            controls_layout.addWidget(self.dropdown, 0, 0)

        layout = QVBoxLayout()
        layout.addWidget(self.plotWidget)
        if toolbar:
            layout.addLayout(controls_layout)
        self.setLayout(layout)

    def _update_plot_axes(self):
        """
        Internal method to update the plot axes based on the flag
        """
        match self.flag:
            case "THz Signals":
                self.plotWidget.setLabel("left", "ADC Counts")
                self.plotWidget.setLabel("bottom", "Delay (mm)")
                self.plotWidget.showGrid(x=False, y=False)
                self.plotWidget.setLogMode(False, False)
                # Remove plots of THz spectra if any
                for key in self.dataplots["THz Spectra"].keys():
                    if (self.dataplots["THz Spectra"][key] is None or
                        key == "x_axis"):
                        # If the plot is None or x_axis, skip it
                        continue
                    else:
                        self.plotWidget.removeItem(
                            self.dataplots["THz Spectra"][key])
                        self.dataplots["THz Spectra"][key] = None
            case "THz Spectra":
                self.plotWidget.setLabel("left", "Amplitude")
                self.plotWidget.setLabel("bottom", "Frequency (THz)")
                self.plotWidget.showGrid(x=True, y=True)
                self.plotWidget.setLogMode(False, True)
                # Remove plots of THz signal if any
                for key in self.dataplots["THz Signals"].keys():
                    if (self.dataplots["THz Signals"][key] is None or
                        key == "x_axis"):
                        # If the plot is None or x_axis, skip it
                        continue
                    else:
                        self.plotWidget.removeItem(
                            self.dataplots["THz Signals"][key])
                        self.dataplots["THz Signals"][key] = None
            case "Picoscope signal":
                self.plotWidget.setLabel("left", "ADC Counts")
                self.plotWidget.setLabel("bottom", "Time (ms)")
        
        for i, key in enumerate(self.dataplots[self.flag].keys()):
            if self.dataplots[self.flag][key] is not None:
                continue
            self.dataplots[self.flag][key] = self.plotWidget.plot(
                [], [], name=key, pen=pg.mkPen(color=colors[i%3],
                                               width = 2))
            if "Spectrum" in key:
                self.dataplots[self.flag][key].setLogMode(xState=False,
                                                     yState=True)

    def change_plot_type(self, text):
        self.plot_type = text.lower().replace(" + points", "+points")
        self.plotWidget.clear()
        for plot in self.dataplots[self.flag].keys():
            if plot == "x_axis":
                continue
            if self.dataplots[self.flag][plot] is None:
                print(f"Plot {plot} not found in {self.flag}")
                continue
            match self.plot_type:
                case "line":
                    self.dataplots[self.flag][plot] = self.plotWidget.plot(
                        [], [], name=plot,
                        pen=pg.mkPen(color=colors[[*self.dataplots
                                                  [self.flag]].
                                                  index(plot)%3],
                                                  width=2))
                case "scatter":
                    self.dataplots[self.flag][plot] = self.plotWidget.plot(
                        [], [], name=plot,
                        pen=None,
                        symbol='o',
                        symbolSize=8,
                        symbolBrush=colors[[*self.dataplots[self.flag]].
                                                  index(plot)%3]
                    )
                case "line+points":
                    self.dataplots[self.flag][plot] = self.plotWidget.plot(
                        [], [], name=plot, symbol='o', symbolSize=8,
                        symbolBrush=colors[[*self.dataplots[self.flag]].
                                                  index(plot)%3],
                        pen=pg.mkPen(color=colors[[*self.dataplots
                                                  [self.flag]].
                                                  index(plot)%3],
                                                  width=2))

        self.update_plot()

    def update_plot(self,
                    data=None,
                    data_selection: list = ["signal"]):
        """
        Update the plot with new data.
        The main plotting logic is all here
        """
        # If data is provided, cache the data
        if type(data) is dict:
            self.data = data
        #Cache the data selection if provided
        if data_selection is not None:
            self.data_selection = data_selection
        # Check if flag has been changed or not. if yes, cache the
        # latest flag and update the plot title and labels
        if self.previous_flag != self.flag:
            self.plotWidget.setTitle(self.flag)
            self.previous_flag = self.flag
            self._update_plot_axes()

        # Just simply plot the data, no need to change anything
        for plot in self.dataplots[self.flag].keys():
            if plot == "x_axis":
                continue
            if self.dataplots[self.flag][plot] is None:
                print(f"Plot {plot} not found in {self.flag}")
                continue  # Skip invalid plots
            y_data = self.data[plot]
            x_data = self.data[self.dataplots[self.flag]["x_axis"]][:len(
                                    self.data[plot])]
            if data_selection is not None and plot in self.data_selection:
                self.dataplots[self.flag][plot].setVisible(True)
            else:
                self.dataplots[self.flag][plot].setVisible(False)

            if np.iscomplexobj(y_data):
                print(f"Plot {plot} contains complex data,"
                      f" getting absolute value.")
                y_data = np.abs(y_data)
            self.dataplots[self.flag][plot].setData(x_data, y_data)

class PlotManager(QWidget):
    """ Class for the main tab to record and display results. """
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.plot_order = ["THz Signals", "THz Spectra"]
        self.current_data = None
        self.setLayout(self.layout)
        self.data_plots()

    def control_panel(self):
        """ Create the information widget for the plots """
        base = QWidget()
        overall_layout = QGridLayout()
        base.setLayout(overall_layout)
        self.control_widget = QGroupBox("Control Panel")
        control_layout = QGridLayout()
        self.control_widget.setLayout(control_layout)
        self.info_widget = InfoWidgets.WaveformInfo("Waveform Information")
        self.data_selection_stack = ResizingStackedWidget(self)
        self.THz_signal_data = QCheckList(['E_off', 'E_on', 'DT'],
                                    'Data to plot', 1)
        self.THz_spectra_data = QCheckList(['E_off Spectrum',
                                            'E_on Spectrum',
                                            'DT Spectrum'],
                                            'Data to plot', 1)
        self.data_selection_stack.addWidget(self.THz_signal_data)
        self.data_selection_stack.addWidget(self.THz_spectra_data)
        self.data_selection_stack.adjustSize()
        overall_layout.addWidget(self.control_widget, 0, 0, 2, 4)
        overall_layout.addWidget(self.info_widget, 3, 0, 4, 4)
        overall_layout.addWidget(self.data_selection_stack, 8, 0, 4, 4)
        overall_layout.setRowStretch(0|1|2|3|4|5, 1)

        self.data_dropdown = QComboBox()
        self.data_dropdown.addItems(self.plot_order)
        self.data_dropdown.setEnabled(False)
        self.data_dropdown.currentTextChanged.connect(self.change_plot)
        self.exp_stop_button = QPushButton("Stop")
        self.exp_stop_button.setEnabled(False)
        self.next_exp_button = QPushButton("Next experiment")
        self.next_exp_button.setEnabled(False)
        control_layout.addWidget(self.data_dropdown, 0, 0)
        control_layout.addWidget(self.exp_stop_button, 1, 0)
        control_layout.addWidget(self.next_exp_button, 1, 1)

        return base

    def data_plots(self):
        """ Create the data plots widget """
        # Setup all the plots, 3 in total
        self.plots = [LivePlot(flag="THz Signals",
                               is_main=True,
                               toolbar=True),
                      LivePlot("THz Spectra"),
                      LivePlot("Picoscope signal")]

        self.control_panel = self.control_panel()
        self.layout.addWidget(self.plots[0], 0, 0, 6, 4)
        self.layout.addWidget(self.control_panel, 0, 4, 4, 1)
        self.layout.setColumnMinimumWidth(0, 1300)
        self.layout.setRowMinimumHeight(0, 400)
        for i in range(len(self.plots[1:])):
            self.layout.addWidget(self.plots[1:][i], i+4, 4, 1, 1)

    def update_plots(self,
                     data: dict = None):
        """ Update the plots with new data """
        if type(data) is dict and "signal" not in data.keys():
            self.current_data = data
        # Update information variables
        if self.current_data is not None:
            self.info_widget.update_info(self.current_data)
        for plot in self.plots:
            match plot.flag:
                case "Picoscope signal":
                    if type(data) is dict and "signal" in data.keys():
                        plot.update_plot(data)
                        return
                case "THz Signals":
                    if self.current_data is not None:
                        plot.update_plot(self.current_data,
                                    self.THz_signal_data.checked_items)
                case "THz Spectra":
                    if self.current_data is not None:
                        plot.update_plot(self.current_data,
                                     self.THz_spectra_data.checked_items)

    def change_plot(self):
        """ Change the main plot to selected data """
        ctext = self.data_dropdown.currentText()
        current_main_flag = self.plots[0].flag

        # Find the plot corresponding to the selected flag
        for i, plot in enumerate(self.plots):
            if plot.flag == ctext:
                self.plots[0].flag = ctext
                plot.flag = current_main_flag

        # Update the dropdown and data selection stack
        match ctext:
            case "THz Signals":
                self.data_selection_stack.setCurrentIndex(0)
            case "THz Spectra":
                self.data_selection_stack.setCurrentIndex(1)

        # Update the plots
        self.update_plots()
        return

# Class for tuning window
class TuningWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tuning Window")
        self.resize(400, 200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tuning_label = QLabel("Tuning Window")
        self.layout.addWidget(self.tuning_label)

        # Add tuning controls here
        # Example: self.tuning_slider = QSlider(Qt.Horizontal)