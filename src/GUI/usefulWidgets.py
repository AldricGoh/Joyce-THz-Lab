from PyQt6.QtWidgets import (
    QStackedWidget, QWidget, QGridLayout, QPushButton, QFrame,
    QGroupBox, QVBoxLayout, QCheckBox
)
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg
                                               as FigureCanvas)
from matplotlib.figure import Figure

# This file provides useful widgets for the GUI to avoid
# too much messy code in the main files.

class ResizingStackedWidget(QStackedWidget):
    def sizeHint(self):
        # Return the size hint of the current widget
        current = self.currentWidget()
        if current:
            return current.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self):
        current = self.currentWidget()
        if current:
            return current.minimumSizeHint()
        return super().minimumSizeHint()

class RowWidget(QWidget):
    def __init__(self, container, content_widget):
        super().__init__()
        self.container = container
        self.content_widget = content_widget

        grid = QGridLayout(self)
        grid.setColumnStretch(0, 1)  # Allow content to stretch

        # Add content widget (e.g. QLineEdit + label)
        grid.addWidget(content_widget, 0, 0)

        # Create vertical button stack
        button_frame = QFrame()
        button_layout = QGridLayout(button_frame)
        button_layout.setSpacing(2)

        self.btn_insert_above = QPushButton("↑")
        self.btn_delete = QPushButton("×")
        self.btn_insert_below = QPushButton("↓")

        button_layout.addWidget(self.btn_insert_above, 0, 0)
        button_layout.addWidget(self.btn_delete,       1, 0)
        button_layout.addWidget(self.btn_insert_below, 2, 0)

        grid.addWidget(button_frame, 0, 1)

        # Connect
        self.btn_insert_above.clicked.connect(self.insert_above)
        self.btn_delete.clicked.connect(self.delete_self)
        self.btn_insert_below.clicked.connect(self.insert_below)

    def insert_above(self):
        self.container.insert_row(self, position="above")

    def insert_below(self):
        self.container.insert_row(self, position="below")

    def delete_self(self):
        self.container.delete_row(self)

class RowContainer(QGroupBox):
    def __init__(self, title: str, content_factory):
        super().__init__(title)
        self.content_factory = content_factory
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.rows = []

        # Add first row
        self.insert_row(None, position="below")

    def insert_row(self, reference_row, position="below"):
        content_widget = self.content_factory()
        new_row = RowWidget(self, content_widget)

        if reference_row is None:
            index = len(self.rows)
        else:
            index = self.rows.index(reference_row)
            if position == "below":
                index += 1

        self.rows.insert(index, new_row)
        self.refresh_layout()

    def delete_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()
            self.refresh_layout()
        self.parentWidget().adjustSize()

    def refresh_layout(self):
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                self.layout.removeWidget(widget)

        # Re-add all rows
        for row_index, row in enumerate(self.rows):
            self.layout.addWidget(row, row_index, 0)
        
        # Force layout update and resize
        self.layout.invalidate()
        self.adjustSize()
        self.updateGeometry()

class QCheckList(QGroupBox):
    """
    Class to create a groupbox for a checklist of checkboxes.
    """
    def __init__(self,
                 items: list,
                 title: str = "Checklist",
                 columns: int = 1,
                 min_items: int = 1,
                 fontsize: int = 12):
        super().__init__(title)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.min_items = min_items
        self.checked_items = []

        self.checklist = {}
        row = 0
        col = 0
        item_count = 0
        for item in items:
            self.checklist[item] = QCheckBox(item)
            self.layout.addWidget(self.checklist[item], row, col)
            self.checklist[item].setFont(QFont("Arial", fontsize))
            self.checklist[item].stateChanged.connect(self.onStateChanged)
            if item_count < self.min_items:
                self.checklist[item].setChecked(True)
                self.checklist[item].setEnabled(False)
                item_count += 1
            if col < columns - 1:
                col += 1
                continue
            else:
                row += 1
                col = 0

    def onStateChanged(self):
        """ Get the items selected from the checklist. """
        self.checked_items = []
        for item in self.checklist.keys():
            if self.checklist[item].isChecked():
                self.checked_items.append(item)
        if len(self.checked_items) == self.min_items:
            for item in self.checked_items:
                self.checklist[item].setEnabled(False)
        else:
            for item in self.checked_items:
                self.checklist[item].setEnabled(True)

class TinyHisPlotWidget(QWidget):
    """
    A tiny histogram plot widget for displaying small plots in the GUI.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = Figure(figsize=(0.3, 0.3), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("off")
        self.fig.subplots_adjust(left=0.1, right=0.95, top=1, bottom=0)

        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
    
    def update_plot(self, data):
        """ Update the histogram plot with new data. """
        self.data = data
        self.ax.clear()
        self.ax.hist(self.data, bins=20, color="skyblue", edgecolor="black")
        data_min = min(self.data)
        data_max = max(self.data)
        self.ax.relim()
        self.ax.set_xticks([data_min, data_max])
        self.ax.tick_params(axis="x", direction="out", pad=-33)
        self.ax.set_xticklabels([f"{data_min:.2f}", f"{data_max:.2f}"],
                                fontsize=8)
        for label in self.ax.get_xticklabels():
            label.set_bbox(dict(facecolor="black",
                                edgecolor="none",
                                pad=1.0))
        self.ax.set_yticks([])
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.canvas.draw()