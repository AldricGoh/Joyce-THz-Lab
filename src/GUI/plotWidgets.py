import distinctipy
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QComboBox, QLineEdit, QSizePolicy, QLabel, QGroupBox, QCheckBox
)
import numpy as np
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg
                                               as FigureCanvas)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from src.GUI.usefulWidgets import ResizingStackedWidget ,QCheckList
from src.GUI.infoWidget import InfoWidgets

# Set dark mode for matplotlib. Comment out if not needed.
plt.style.use('dark_background')
# TODO: Colour code different segments of Picoscope signals
# TODO: Add heatmap plot for spot size plot
# TODO: Add checkbox to display different plots onto the same plot
# TODO: Add large plot

colors = distinctipy.get_colors(4, pastel_factor=0.7)

def plain_format(x, pos):
    return f"{x:g}"  # or f"{x:.2e}" for scientific notation

class LivePlot(QWidget):
    def __init__(self,
                 flag: str = None,
                 scaling: str = None,
                 xlim: float = None,
                 ylim: float = None,
                 figsize: tuple = (5, 2),
                 dpi: int = 100,
                 toolbar: bool= False):
        super().__init__()
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.plot_type = type
        self.ax = self.figure.add_subplot(111)
        self.flag = flag
        self.is_main = False
        if xlim != None:
            self.ax.set_xlim(xlim)
            self.autoscale_x = False
        else:
            self.autoscale_x = True
        if ylim != None:
            self.ax.set_ylim(ylim)
            self.autoscale_y = False
        else:
            self.autoscale_y = True
        self.plot_type = "line"
        self.scaling = scaling
        self.colors = colors

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Expanding)

        # If enabled, the toolbar will be added to the plot
        if toolbar:
            self.toolbar = NavigationToolbar2QT(self.canvas, self)

            self.dropdown = QComboBox()
            self.dropdown.addItems(["Line", "Scatter", "Line + Points"])
            self.dropdown.currentTextChanged.connect(self.change_plot_type)

            self.xminlim_entry = QLineEdit()
            self.xminlim_entry.setPlaceholderText("x min")
            self.xmaxlim_entry = QLineEdit()
            self.xmaxlim_entry.setPlaceholderText("x max")
            self.yminlim_entry = QLineEdit()
            self.yminlim_entry.setPlaceholderText("y min")
            self.ymaxlim_entry = QLineEdit()
            self.ymaxlim_entry.setPlaceholderText("y max")
            self.set_axes_button = QPushButton("Set Axes Limits")
            self.set_axes_button.clicked.connect(self.set_axes_limits)

            controls_layout = QGridLayout()
            controls_layout.addWidget(self.dropdown, 0, 0)
            controls_layout.addWidget(self.xminlim_entry, 0, 1)
            controls_layout.addWidget(self.xmaxlim_entry, 0, 2)
            controls_layout.addWidget(self.yminlim_entry, 1, 1)
            controls_layout.addWidget(self.ymaxlim_entry, 1, 2)
            controls_layout.addWidget(self.set_axes_button, 0, 3, 2, 1)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        if toolbar:
            layout.addWidget(self.toolbar)
            layout.addLayout(controls_layout)
        self.setLayout(layout)

    def change_plot_type(self, text):
        self.plot_type = text.lower().replace(" + points", "+points")
        self.update_plot()

    def set_axes_limits(self):
        try:
            xlim = tuple(map(float, self.xlim_entry.text().split(',')))
            ylim = tuple(map(float, self.ylim_entry.text().split(',')))
            if len(xlim) == 2:
                self.ax.set_xlim(xlim)
            if len(ylim) == 2:
                self.ax.set_ylim(ylim)
            self.canvas.draw()
        except ValueError:
            print("Invalid axis limits input.")

    def plot_data(self,
                  x_data: list,
                  y_data: list,
                  label: str = None):
        """ Function to plot data based on various variables. """
        
        if label is None:
            color = self.colors[3]
        elif "E_on" in label:
            color = self.colors[0]
        elif "E_off" in label:
            color = self.colors[1]
        elif "DT" in label:
            color = self.colors[2]
        else:
            color = self.colors[3]

        if self.scaling == "semilog":
            self.ax.semilogy(x_data, y_data, lw=1, color=color)
            self.ax.relim()
        if self.plot_type == "line":
            self.ax.plot(x_data, y_data, lw=1, color=color, label=label)
            self.ax.relim()
        elif self.plot_type == "scatter":
            sc = self.ax.scatter(x_data, y_data, s=10, color=color,
                                 label=label)
            self.ax.update_datalim(sc.get_offsets())
        elif self.plot_type == "line+points":
            self.ax.plot(x_data, y_data, marker = 'o',
                         lw=1, color=color, label=label)
            self.ax.relim()

    def update_plot(self,
                    data=None,
                    data_selection: list = None):
        self.ax.clear()
        if data is not None and type(data) is dict:
            self.data = data
        if data_selection is not None:
            self.data_selection = data_selection
        match self.flag:
            case "THz Signals":
                self.title = "THz Signals"
                self.x_label = "Delay (mm)"
                self.y_label = "ADC Counts"
                self.scaling = None
                for selection in self.data_selection:
                    x_data = self.data["Delay (mm)"][:len(
                            self.data[selection])]
                    y_data = self.data[selection]
                    self.plot_data(x_data, y_data, selection)
            case "THz Spectra":
                self.title = "THz Spectra"
                self.x_label = "Frequency (THz)"
                self.y_label = "Amplitude"
                self.scaling = "semilog"
                for selection in self.data_selection:
                    x_data = self.data["Frequency (THz)"][:len(
                        self.data[selection])]
                    y_data = self.data[selection]
                    self.plot_data(x_data, y_data, selection)
            case "Picoscope signal":
                self.title = "Picoscope signal"
                self.x_label = "Time (ms)"
                self.y_label = "ADC Counts"
                self.plot_data(data[0], data[1])

        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        self.ax.yaxis.set_major_formatter(FuncFormatter(plain_format))
        if self.is_main:
            self.ax.legend(loc=1)
        self.ax.autoscale_view(scalex=self.autoscale_y,
                               scaley=self.autoscale_y)
        self.figure.tight_layout()
        self.canvas.draw()

class PlotManager(QWidget):
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
        self.THz_spectra_data = QCheckList(['E_off Sprectrum',
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
        self.plots = [LivePlot(flag="THz Signals", toolbar=True),
                      LivePlot("THz Spectra"), LivePlot("Picoscope signal")]
        self.plots[0].is_main = True

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
        if type(data) is dict:
            self.current_data = data
        # Update information variables
        if self.current_data is not None:
            self.info_widget.update_info(self.current_data)
        for plot in self.plots:
            match plot.flag:
                case "Picoscope signal":
                    return
                case "THz Signals":
                    plot.update_plot(self.current_data,
                                    self.THz_signal_data.checked_items)
                case "THz Spectra":
                    plot.update_plot(self.current_data,
                                     self.THz_spectra_data.checked_items)
    
    def change_plot(self):
        """ Change the main plot to selected data """
        ctext = self.data_dropdown.currentText()
        current_main_flag = self.plots[0].flag
        for plot in self.plots:
            if plot.flag == ctext:
                plot.flag = current_main_flag
        self.plots[0].flag = ctext
        self.plots[0].is_main = True
        match ctext:
            case "THz Signals":
                self.data_selection_stack.setCurrentIndex(0)
            case "THz Spectra":
                self.data_selection_stack.setCurrentIndex(1)
        # self.update_plots()

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