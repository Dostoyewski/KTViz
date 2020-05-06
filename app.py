import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from main import prepare_file
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QSlider
from PyQt5.QtCore import Qt


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.sl = QSlider(Qt.Horizontal, self)
        self.left = 10
        self.top = 10
        self.title = 'KTViz 1.0'
        self.width = 1200
        self.height = 900
        self.filename = ""
        self.relative = True
        self.m = PlotCanvas(self, width=12, height=8)
        self.loaded = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Initialization of canvas
        self.m.move(0, 0)

        # Load button
        button = QPushButton('Load Files', self)
        button.move(1000, 20)
        button.resize(140, 50)
        button.clicked.connect(self.openFileNameDialog)

        # Checkbox with relative coordinates
        cb = QCheckBox('Relative\n coords', self)
        cb.move(20, 20)
        cb.toggle()
        cb.stateChanged.connect(self.update_state)

        # Slider config
        self.sl.setMinimum(0)
        self.sl.setMaximum(99)
        self.sl.setValue(25)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.sl.setGeometry(50, 800, 1100, 100)
        self.sl.valueChanged.connect(self.value_change)

        self.show()

    def value_change(self):
        print(self.sl.value())
        if self.loaded:
            self.m.plot(self.filename, self.relative, self.sl.value())

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
            self.m.plot(self.filename, self.relative, self.sl.value())


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

    def plot(self, filename, rel=False, tper=0):
        """
        Plot function
        :param filename: name of file to save
        :param rel: relative coords flag
        :param tper: time percent
        :return:
        """
        ax = self.figure.add_subplot(111)
        ax.clear()
        for file in filename:
            prepare_file(file, True, ax, rel, tper/100)
            ax.set_title('Trajectory')
            ax.axis('equal')
        self.draw()
        self.fig.savefig("img/image.png")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
