import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
import pyqtgraph as pg

class CustomLegendItem(pg.LegendItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []  # store tuples of (sample, label, item)

    def addItem(self, item, name):
        super().addItem(item, name)
        row = self.layout.rowCount() - 1
        # Safely get items, checking they exist
        sample = self.layout.itemAt(row, 0)
        label = self.layout.itemAt(row, 1)
        self.items.append((sample, label, item))

    def mousePressEvent(self, event):
        pos = event.pos()
        for sample, label, item in self.items:
            if sample is not None:
                sample_rect = sample.graphicsItem().boundingRect().translated(sample.graphicsItem().pos())
            else:
                continue  # skip if no sample

            if label is not None:
                label_rect = label.graphicsItem().boundingRect().translated(label.graphicsItem().pos())
            else:
                continue  # skip if no label

            if sample_rect.contains(pos) or label_rect.contains(pos):
                current_vis = item.isVisible()
                visible_count = sum(i.isVisible() for _, _, i in self.items)
                if current_vis and visible_count == 1:
                    return  # Don't allow all plots to be hidden
                else:
                    item.setVisible(not current_vis)
                    alpha = 1.0 if not current_vis else 0.3
                    sample.graphicsItem().setOpacity(alpha)
                    label.graphicsItem().setOpacity(alpha)
                break
        super().mousePressEvent(event)

class PlotWidgetWithLegend(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Legend Toggle Example")

        self.plot_widget = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        self.legend = CustomLegendItem(offset=(30, 30))
        self.legend.setParentItem(self.plot_widget.getPlotItem())

        self.add_sample_plot([1, 2, 3, 4], [1, 4, 9, 16], 'Plot 1', 'r')
        self.add_sample_plot([1, 2, 3, 4], [2, 3, 5, 7], 'Plot 2', 'g')
        self.add_sample_plot([1, 2, 3, 4], [5, 3, 2, 1], 'Plot 3', 'b')

    def add_sample_plot(self, x, y, name, color):
        curve = self.plot_widget.plot(x, y, pen=pg.mkPen(color=color, width=2), name=name)
        self.legend.addItem(curve, name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlotWidgetWithLegend()
    window.show()
    sys.exit(app.exec())