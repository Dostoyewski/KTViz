import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QSlider, QDoubleSpinBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from main import prepare_file, check_type


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        # Show dist checkbox
        self.cb2 = QCheckBox('Show dist', self)
        # Show text checkbox
        self.cb1 = QCheckBox('Show vel', self)
        # Show global coords
        self.cb3 = QCheckBox('Show GC', self)
        # Radius selection
        self.spinBox = QDoubleSpinBox(self)
        # Time axis
        self.sl = QSlider(Qt.Horizontal, self)
        self.left = 10
        self.top = 50
        self.title = 'KTViz 1.0'
        try:
            screen_resolution = app.desktop().screenGeometry()
            width, height = screen_resolution.width(), screen_resolution.height()
            print("Screen dimensions: ({}x{})".format(width, height))
            self.width = round(width * 0.7)
            self.height = round(height * 0.7)
            if self.height > 1000:
                self.height = 1000
        except:
            self.width = 1280
            self.height = 720
        self.setFixedSize(self.width, self.height)
        print("Window dimensions set to ({}x{})".format(self.width, self.height))
        self.scale_x = self.width / 1800
        self.scale_y = self.height / 900
        self.filename = ""
        self.relative = True
        self.m = PlotCanvas(self, width=round(12 * self.scale_x), height=round(8 * self.scale_y))
        self.vel = PlotCanvas(self, width=round(6 * self.scale_x), height=round(7 * self.scale_y))
        self.loaded = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Initialization of canvas
        self.m.move(0, 0)

        # Load button
        button = QPushButton('Load Files', self)
        button.move(1220 * self.scale_x, 20 * self.scale_y)
        button.resize(140 * self.scale_x, 50 * self.scale_y)
        button.clicked.connect(self.openFileNameDialog)

        # Slider config
        self.sl.setMinimum(0)
        self.sl.setMaximum(99)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.sl.setGeometry(50 * self.scale_x, 800 * self.scale_y, 1100 * self.scale_x, 100)
        self.sl.valueChanged.connect(self.value_changed)

        # Update button
        button1 = QPushButton('Update', self)
        button1.move(1200 * self.scale_x, 820 * self.scale_y)
        button1.resize(140 * self.scale_x, 50 * self.scale_y)
        button1.clicked.connect(self.reload)

        # Safe radius box
        self.spinBox.setRange(0, 10)
        self.spinBox.move(1530 * self.scale_x, 32 * self.scale_y)
        self.spinBox.setValue(1.5)
        self.spinBox.setSingleStep(0.1)
        self.spinBox.valueChanged.connect(self.value_changed)

        # Show text checkbox
        self.cb1.move(1400 * self.scale_x, 5 * self.scale_y)
        self.cb1.toggle()
        self.cb1.stateChanged.connect(self.value_changed)

        # Show dist checkbox
        self.cb2.move(1400 * self.scale_x, 30 * self.scale_y)
        self.cb2.toggle()
        self.cb2.stateChanged.connect(self.value_changed)

        # Show WGS checkbox
        self.cb3.move(1400 * self.scale_x, 55 * self.scale_y)
        self.cb3.toggle()
        self.cb3.stateChanged.connect(self.value_changed)

        self.vel.move(1200 * self.scale_x, 90 * self.scale_y)
        self.show()

    def reload(self):
        self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                    self.cb1.isChecked(), self.cb2.isChecked(), show_coords=self.cb3.isChecked(),
                    fig=self.vel, is_loaded=False)

    def value_changed(self):
        if self.loaded:
            self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                        self.cb1.isChecked(), self.cb2.isChecked(), show_coords=self.cb3.isChecked(),
                        fig=self.vel, is_loaded=True)

    def update_state(self):
        self.relative = not self.relative
        self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                    self.cb1.isChecked(), self.cb2.isChecked(), show_coords=self.cb3.isChecked(),
                    fig=self.vel, is_loaded=False)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileNames(self, "Open JSON Trajectory", "",
                                                   "JSON Files (*.json)", options=options)
        if filename:
            self.filename = filename
            self.loaded = True
            self.m.plot(self.filename, self.relative, self.sl.value(), self.spinBox.value(),
                        self.cb1.isChecked(), self.cb2.isChecked(), show_coords=self.cb3.isChecked(),
                        fig=self.vel, is_loaded=False)


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

    def plot(self, filename, rel=False, tper=0, radius=1, text=True, show_dist=True, show_coords=True,
             fig=None, is_loaded=False):
        """
        Plot function
        :param show_coords: Show global coords in WGS84
        :param is_loaded: flag if file is in memory
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
        directory = ""
        for i in range(len(filename)):
            if check_type(filename[i]) == 'poly':
                filename[i], filename[-1] = filename[-1], filename[i]
        for file in filename:
            prepare_file(file, True, ax, rel, tper / 100, radius, text, show_dist, show_coords, fig, is_loaded)
            ax.set_title('Trajectory')
            ax.axis('equal')
            directory = os.path.dirname(file)
        self.draw()
        try:
            self.fig.savefig("img/image.png")
        except FileNotFoundError:
            self.fig.savefig(directory + "/image.png")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
