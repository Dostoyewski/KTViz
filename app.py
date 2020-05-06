import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from main import prepare_file
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QSlider, QDoubleSpinBox
from PyQt5.QtCore import Qt


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        # Show dist checkbox
        self.cb2 = QCheckBox('Show dist', self)
        # Show text checkbox
        self.cb1 = QCheckBox('Show vel', self)
        # Radius selection
        self.spinBox = QDoubleSpinBox(self)
        # Time axis
        self.sl = QSlider(Qt.Horizontal, self)
        self.left = 10
        self.top = 10
        self.title = 'KTViz 1.0'
        self.width = 1800
        self.height = 900
        self.filename = ""
        self.relative = True
        self.m = PlotCanvas(self, width=12, height=8)
        self.vel = PlotCanvas(self, width=6, height=7.1)
        self.loaded = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Initialization of canvas
        self.m.move(0, 0)

        # Load button
        button = QPushButton('Load Files', self)
        button.move(1220, 20)
        button.resize(140, 50)
        button.clicked.connect(self.openFileNameDialog)

        # Checkbox with relative coordinates
        cb = QCheckBox('Relative', self)
        cb.move(1650, 32)
        cb.toggle()
        cb.stateChanged.connect(self.update_state)

        # Slider config
        self.sl.setMinimum(0)
        self.sl.setMaximum(99)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.sl.setGeometry(50, 800, 1100, 100)
        self.sl.valueChanged.connect(self.value_changed)

        self.spinBox.setRange(0, 10)
        self.spinBox.move(1530, 32)
        self.spinBox.setValue(1)
        self.spinBox.setSingleStep(0.1)
        self.spinBox.valueChanged.connect(self.value_changed)

        # Show text checkbox
        self.cb1.move(1400, 12)
        self.cb1.toggle()
        self.cb1.stateChanged.connect(self.value_changed)

        # Show dist checkbox
        self.cb2.move(1400, 50)
        self.cb2.toggle()
        self.cb2.stateChanged.connect(self.value_changed)

        self.vel.move(1200, 90)
        self.show()

    def value_changed(self):
        if self.loaded:
            self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                        self.cb1.isChecked(), self.cb2.isChecked(), fig=self.vel)

    def update_state(self):
        self.relative = not self.relative

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileNames(self, "Open JSON Trajectory", "",
                                                  "JSON Files (*.json)", options=options)
        if filename:
            self.filename = filename
            self.loaded = True
            self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                        self.cb1.isChecked(), fig=self.vel)


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=50, height=50, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self, filename, rel=False, tper=0, radius=1, text=True, show_dist=True, fig=None):
        """
        Plot function
        :param fig: figure to plot velocities
        :param show_dist: show distances values
        :param text: show velocities
        :param radius: Save radius
        :param filename: name of file to save
        :param rel: relative coords flag
        :param tper: time percent
        :return:
        """
        ax = self.figure.add_subplot(111)
        ax.clear()
        for file in filename:
            prepare_file(file, True, ax, rel, tper/100, radius, text, show_dist, fig)
            ax.set_title('Trajectory')
            ax.axis('equal')
        self.draw()
        self.fig.savefig("img/image.png")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
