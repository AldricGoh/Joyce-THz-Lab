from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QComboBox, QLineEdit, QSizePolicy, QLabel, QGroupBox, QCheckBox
)
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg
                                               as FigureCanvas)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from src.GUI.usefulWidgets import ResizingStackedWidget ,QCheckList


# Set dark mode for matplotlib. Comment out if not needed.
plt.style.use('dark_background')
# TODO: Colour code different segments of Picoscope signals
# TODO: Rearrange buttons in the GUI
# TODO: Add heatmap plot for spot size plot
# TODO: Add checkbox to display different plots onto the same plot
# TODO: Add large plot

class LivePlot(QWidget):
    def __init__(self,
                 flag: str = None,
                 scaling: str = None,
                 xlim: float = None,
                 ylim: float = None,
                 figsize: tuple = (5, 2),
                 dpi: int = 100,
                 toolbar: bool= False,
                 extra_plots: list = None):
        super().__init__()
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.plot_type = type
        self.ax = self.figure.add_subplot(111)
        self.flag = flag
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

        self.x_data = []
        self.y_data = []

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

    def update_plot(self, data):
        match self.flag:
            case "E_off":
                self.title = "$E_{off}$"
                self.x_label = "delay (mm)"
                self.y_label = "ADC Counts"
                self.scaling = None
                if data is not None:
                    self.x_data = data["Delay (mm)"][:len(data["E_off"])]
                    self.y_data = data["E_off"]
            case "E_on":
                self.title = "$E_{on}$"
                self.x_label = "delay (mm)"
                self.y_label = "ADC Counts"
                self.scaling = None
                if data is not None:
                    self.x_data = data["Delay (mm)"][:len(data["E_on"])]
                    self.y_data = data["E_on"]
            case "DT":
                self.title = "$DT$"
                self.x_label = "delay (mm)"
                self.y_label = "ADC Counts"
                self.scaling = None
                if data is not None:
                    self.x_data = data["Delay (mm)"][:len(data["DT"])]
                    self.y_data = data["DT"]
            case "Spectra":
                self.title = "Spectra"
                self.x_label = "Frequency (THz)"
                self.y_label = "Amplitude"
                self.scaling = "semilog"
                if data is not None:
                    self.x_data = data["Frequency (THz)"][:len(
                        data["E_off_fft"])]
                    self.y_data = data["E_off_fft"]
            case "Picoscope signal":
                self.title = "Picoscope signal"
                self.x_label = "delay (ms)"
                self.y_label = "ADC Counts"
                if data is not None:
                    self.x_data = data[0]
                    self.y_data = data[1]

        self.ax.clear()
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        if self.scaling == "semilog":
            self.ax.semilogy(self.x_data, self.y_data, lw=1)
        if self.plot_type == "line":
            self.ax.plot(self.x_data, self.y_data, lw=1)
        elif self.plot_type == "scatter":
            self.ax.scatter(self.x_data, self.y_data, s=5, c='r')
        elif self.plot_type == "line+points":
            self.ax.plot(self.x_data, self.y_data, lw=1)
            self.ax.scatter(self.x_data, self.y_data, s=5, c='r')

        self.ax.relim()
        self.ax.autoscale_view(scalex=self.autoscale_y,
                               scaley=self.autoscale_y)
        self.figure.tight_layout()
        self.canvas.draw()

class PlotManager(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.plot_order = ["E_off", "E_on", "DT", "Spectra"]
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
        self.info_widget = QGroupBox("Useful Information")
        info_layout = QGridLayout()
        self.data_selection_stack = ResizingStackedWidget(self)
        self.E_on_data = QCheckList(['E_on', 'E_off', 'DT'],
                                    'Data to plot')
        self.data_selection_stack.addWidget(self.E_on_data)
        self.data_selection_stack.adjustSize()
        self.info_widget.setLayout(info_layout)
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
        
        self.saturation_value = QLabel("All good")
        self.saturation_label = QLabel("Saturation:")
        self.saturation_label.setFont(QFont("Arial", 15))
        self.saturation_value.setFont(QFont("Arial", 15))
        info_layout.addWidget(self.saturation_label, 0, 0)
        info_layout.addWidget(self.saturation_value, 0, 1)

        self.balance_label = QLabel("Balance:")
        self.balance_label.setFont(QFont("Arial", 15))
        self.balance_value = QLabel("0.0")
        self.balance_value.setFont(QFont("Arial", 15))
        info_layout.addWidget(self.balance_label, 1, 0)
        info_layout.addWidget(self.balance_value, 1, 1)

        self.max_signal_label = QLabel("Max signal:")
        self.max_signal_label.setFont(QFont("Arial", 15))
        self.max_signal_value = QLabel("0.0")
        self.max_signal_value.setFont(QFont("Arial", 15))
        info_layout.addWidget(self.max_signal_label, 2, 0)
        info_layout.addWidget(self.max_signal_value, 2, 1)

        self.min_signal_label = QLabel("Min signal:")
        self.min_signal_label.setFont(QFont("Arial", 15))
        self.min_signal_value = QLabel("0.0")
        self.min_signal_value.setFont(QFont("Arial", 15))
        info_layout.addWidget(self.min_signal_label, 3, 0)
        info_layout.addWidget(self.min_signal_value, 3, 1)

        return base
    
    def data_plots(self):
        """ Create the data plots widget """
        # Setup all the plots, 5 in total
        self.plots = [LivePlot(flag="E_off", toolbar=True),
                    #   LivePlot(flag="E_on"), LivePlot(flag="DT"),
                      LivePlot("Spectra"), LivePlot("Picoscope signal")]

        self.control_panel = self.control_panel()

        # self.layout.addWidget(self.plots[0], 0, 0, 1, 3)
        self.layout.addWidget(self.plots[0], 0, 0, 6, 4)
        # self.layout.addWidget(self.control_panel, 0, 3, 1, 1)
        self.layout.addWidget(self.control_panel, 0, 4, 4, 1)
        self.layout.setColumnMinimumWidth(0, 1300)
        self.layout.setRowMinimumHeight(0, 400)
        for i in range(len(self.plots[1:])):
            # self.layout.addWidget(self.plots[1:][i], 3, i, 1, 1)
            self.layout.addWidget(self.plots[1:][i], i+4, 4, 1, 1)

    def update_plots(self, data):
        for plot in self.plots:
            if plot.flag == "Picoscope signal":
                return
            plot.update_plot(data)
    
    def change_plot(self):
        """ Change the main plot to selected data """
        ctext = self.data_dropdown.currentText()
        current_main_flag = self.plots[0].flag
        for plot in self.plots:
            if plot.flag == ctext:
                plot.flag = current_main_flag
        self.plots[0].flag = ctext
        # match ctext:
        #     #"E_off", "E_on", "DT", "Spectra"
        #     case "Dark THz":
        #         self.experiment_stack.setCurrentIndex(0)
        #     case "Pump decay":
        #         self.experiment_stack.setCurrentIndex(1)
        #     case "OPTP":
        #         self.experiment_stack.setCurrentIndex(2)

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