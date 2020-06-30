#!/usr/bin/env python3
import os
import sys

import math
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton, QLabel
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QSlider, QDoubleSpinBox, QWidget, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import plot
from paintall import DrawingApp


# For build:
# pyinstaller --onefile --icon=Icon.ico --noconsole app.py


class ParamBar(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setGeometry(QRect(500, 30, 311, 81))
        self.setObjectName("horizontalWidget")
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Load Files button
        self.pushButton = QPushButton("Load Files", self)
        self.horizontalLayout.addWidget(self.pushButton)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        # Show dist between ships
        self.cbDist = QCheckBox("Distance", self)
        self.verticalLayout.addWidget(self.cbDist)

        # Show coords
        self.cbCoords = QCheckBox("Coords", self)
        self.verticalLayout.addWidget(self.cbCoords)

        # Show Global coordinates
        self.cbGc = QCheckBox("WGS", self)
        self.verticalLayout.addWidget(self.cbGc)
        self.horizontalLayout.addLayout(self.verticalLayout)

        # Safe radius select
        self.labelRadius = QLabel('Radius:', self)
        self.horizontalLayout.addWidget(self.labelRadius)
        self.spinBoxRadius = QDoubleSpinBox(self)
        self.spinBoxRadius.setObjectName("doubleSpinBox")
        self.horizontalLayout.addWidget(self.spinBoxRadius)

        # Safe radius select
        self.labelDistance = QLabel('Distance:', self)
        self.horizontalLayout.addWidget(self.labelDistance)
        self.spinBoxDist = QDoubleSpinBox(self)
        self.spinBoxDist.setObjectName("doubleSpinBox")
        self.horizontalLayout.addWidget(self.spinBoxDist)


class App(QMainWindow):
    rs_signal = QtCore.pyqtSignal(QtCore.QSize)

    def __init__(self):
        super().__init__()
        # Time axis
        self.sl = QSlider(Qt.Horizontal, self)
        self.left = 10
        self.top = 50
        self.title = 'KTViz 1.0'
        # bar with buttons and checkbox
        self.params = ParamBar(self)
        # Update button
        self.btnUpdate = QPushButton('Reload', self)
        # KTDraw button
        self.btnKtDraw = QPushButton('KTDraw', self)

        try:
            screen_resolution = app.desktop().screenGeometry()
            width, height = screen_resolution.width(), screen_resolution.height()
            print("Screen dimensions: ({}x{})".format(width, height))
            self.widthp = round(width * 0.7)
            self.heightp = round(height * 0.7)
            if self.heightp > 1000:
                self.heightp = 1000
        except:
            self.widthp = 1280
            self.heightp = 720

        print("Window dimensions set to ({}x{})".format(self.widthp, self.heightp))
        self.scale_x = self.widthp / 1800
        self.scale_y = self.heightp / 900
        self.filename = ""
        self.relative = True
        self.m = PlotCanvas(self, width=round(12 * self.scale_x), height=round(8 * self.scale_y))
        self.vel = VelocityCanvas(self, width=round(6 * self.scale_x), height=round(7 * self.scale_y))

        self.toolbar = NavigationToolbar(self.m, self)
        self.toolbar.hide()

        # Just some button
        self.btnZoom = QPushButton('🔍︎', self)
        self.btnZoom.setToolTip('Zoom')
        self.btnZoom.clicked.connect(self.zoom)
        self.btnZoom.resize(35, 35)

        self.btnPan = QPushButton('🖐️︎', self)
        self.btnPan.setToolTip('Pan')
        self.btnPan.clicked.connect(self.pan)
        self.btnPan.resize(35, 35)

        self.btnHome = QPushButton('🏠︎', self)
        self.btnHome.setToolTip('Home')
        self.btnHome.clicked.connect(self.home)
        self.btnHome.resize(35, 35)

        self.loaded = False
        self.data = []
        self.frame = None
        self.route_file = None
        self.poly_file = None
        # Adding icon
        self.setWindowIcon(QIcon('Icon.ico'))
        self.initUI()

    def initUI(self):
        # Resize signal
        self.rs_signal.connect(self.resize_app)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.widthp, self.heightp)

        self.params.move(int(0.677 * self.width()), 0)
        self.params.resize(int(0.298 * self.width()), int(0.106 * self.height()))

        # Initialization of canvas
        self.m.move(0, 0)

        # Load button
        self.params.pushButton.clicked.connect(self.openFileNameDialog)

        # Slider config
        self.sl.setMinimum(0)
        self.sl.setMaximum(100)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.sl.setGeometry(int(50 * self.scale_x), int(840 * self.scale_y),
                            int(1100 * self.scale_x), 50)
        self.sl.valueChanged.connect(self.value_changed)

        # Update button
        self.btnUpdate.resize(120, 35)
        self.btnUpdate.clicked.connect(self.reload)

        # KTDraw button
        self.btnKtDraw.resize(80, 35)
        self.btnKtDraw.clicked.connect(self.open_drawer)

        # Safe radius box
        self.params.spinBoxRadius.setRange(0, 10)
        self.params.spinBoxRadius.setValue(1.5)
        self.params.spinBoxRadius.setSingleStep(0.1)
        self.params.spinBoxRadius.valueChanged.connect(self.value_changed)

        # Safe radius box
        self.params.spinBoxDist.setRange(0, 10)
        self.params.spinBoxDist.setValue(5)
        self.params.spinBoxDist.setSingleStep(0.1)
        self.params.spinBoxDist.valueChanged.connect(self.value_changed)

        # Show dist checkbox
        self.params.cbDist.move(int(1400 * self.scale_x), int(30 * self.scale_y))
        self.params.cbDist.toggle()
        self.params.cbDist.stateChanged.connect(self.value_changed)

        # Show coords checkbox
        self.params.cbCoords.move(int(1400 * self.scale_x), int(5 * self.scale_y))
        self.params.cbCoords.toggle()
        self.params.cbCoords.stateChanged.connect(self.show_coords_changed)

        # Show WGS checkbox
        self.params.cbGc.move(int(1400 * self.scale_x), int(55 * self.scale_y))
        self.params.cbGc.toggle()
        self.params.cbGc.stateChanged.connect(self.value_changed)

        self.vel.move(int(1200 * self.scale_x), int(120 * self.scale_y))
        self.show()

    def home(self):
        self.toolbar.home()

    def zoom(self):
        self.toolbar.zoom()

    def pan(self):
        self.toolbar.pan()

    @staticmethod
    def open_drawer():
        """
        Open KTDraw app
        :return:
        """
        dialog = DrawingApp()
        dialog.exec_()

    def resize_app(self):
        """
        Scales all element positions and sizes
        :return:
        """
        self.params.move(int(0.677 * self.width()), 10)
        self.params.resize(int(0.298 * self.width()), int(0.106 * self.height()))
        self.m.resize(int(0.67 * self.width()), int(0.926 * self.height()))
        self.sl.setGeometry(int(0.028 * self.width()), int(0.933 * self.height()),
                            int(0.611 * self.width()), 50)
        self.btnUpdate.move(int(0.677 * self.width() + 120), int(0.933 * self.height()))
        self.btnKtDraw.move(int(self.width() - 100), int(0.933 * self.height()))

        self.btnHome.move(int(0.677 * self.width()), int(0.933 * self.height()))
        self.btnPan.move(int(0.677 * self.width() + 40), int(0.933 * self.height()))
        self.btnZoom.move(int(0.677 * self.width() + 80), int(0.933 * self.height()))

        self.vel.move(int(0.67 * self.width()) + 5, int(0.132 * self.height()))
        self.vel.resize(int(0.330 * self.width()) - 5, 0.794 * self.height())

    def resizeEvent(self, event):
        """
        event onResize
        :param event:
        :return:
        """
        self.rs_signal.emit(self.size())

    def reload(self):
        """
        Updates current scenario without FileOpenDialog
        :return:
        """
        if len(self.filename) == 0:
            self.openFileNameDialog()
        else:
            self.load()

    def load(self):
        self.load_data(self.filename)
        self.m.plot_paths(self.data, self.frame, self.route_file, self.poly_file)
        self.vel.plot_paths(self.data)
        self.update_time()

    def show_coords_changed(self):
        self.params.cbGc.setEnabled(self.params.cbCoords.isChecked())
        self.value_changed()

    def value_changed(self):
        """
        Update plot onChange values
        :return:
        """
        if self.loaded:
            self.update_time()

    def load_data(self, filename):
        self.loaded = True
        self.data, self.frame = plot.prepare_file(filename)
        self.route_file = os.path.join(os.path.dirname(os.path.abspath(filename)), 'route-data.json')
        self.poly_file = os.path.join(os.path.dirname(os.path.abspath(filename)), 'poly-data.json')

    def update_time(self):
        start_time = self.data[0]['start_time']
        total_time = sum([x['duration'] for x in self.data[0]['items']])
        time = start_time + total_time * self.sl.value() * .01
        self.m.update_positions(self.data, time,
                                distance=self.params.spinBoxDist.value() if self.params.cbDist.isChecked() else 0,
                                radius=self.params.spinBoxRadius.value(),
                                coords=self.params.cbCoords.isChecked(),
                                frame=self.frame if self.params.cbGc.isChecked() else None)
        self.m.draw()

    def openFileNameDialog(self):
        """
        Select scenario file
        :return:
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileNames(self, "Open JSON Trajectory", "",
                                                   "JSON Files (*.json)", options=options)
        if filename:
            self.filename = filename[0]
            self.loaded = False
            self.reload()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=50, height=50, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor((159 / 255, 212 / 255, 251 / 255))
        self.ax1 = self.figure.add_axes(self.ax.get_position(), frameon=False)

    def plot_paths(self, path_data, frame, route_file=None, poly_data=None):
        """
        Plots paths
        :param poly_data: Name of file with polygons
        :param path_data: Loaded data
        :param frame: Frame for coordinates conversion
        :param route_file: Name of file with route
        """
        self.ax.clear()
        try:
            if route_file is not None:
                plot.plot_route(self.ax, route_file, frame)
        except FileNotFoundError:
            pass

        try:
            if poly_data is not None:
                plot.plot_limits(self.ax, poly_data, frame)
        except FileNotFoundError:
            pass

        plot.plot_maneuvers(self.ax, path_data)

        self.ax.axis('equal')
        self.ax.grid()
        self.draw()

    def update_positions(self, path_data, t, distance=5, radius=1.5, coords=False, frame=None):
        self.ax1.clear()
        positions = plot.get_positions(path_data, t)
        plot.plot_positions(self.ax1, positions, coords=coords, frame=frame, radius=radius)
        if distance > 0:
            plot.plot_distances(self.ax1, positions, distance)
        self.ax1.legend()
        self.ax1.set_ylim(self.ax.get_ylim())
        self.ax1.set_xlim(self.ax.get_xlim())
        local_time = t - path_data[0]['start_time']
        h, m, s = math.floor(local_time / 3600), math.floor(local_time % 3600 / 60), local_time % 60
        self.ax1.set_title('t=({:.0f}): {:.0f} h {:.0f} min {:.0f} sec'.format(t, h, m, s))


class VelocityCanvas(FigureCanvas):

    def __init__(self, parent=None, width=50, height=50, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.ax = self.figure.add_subplot(111)
        # self.ax1 = self.figure.add_subplot(212)
        # self.fig.tight_layout()
        # self.ax.set_facecolor((159 / 255, 212 / 255, 251 / 255))

    def plot_paths(self, path_data):
        """
        Plots speed
        :param path_data: Loaded data
        """
        self.ax.clear()
        plot.plot_speed(self.ax, path_data[0])
        self.draw()

    # def update_positions(self, path_data, t, distance=5, radius=1.5, coords=False, frame=None):
    #     self.ax1.clear()
    #     positions = plot.get_positions(path_data, t)
    #     plot.plot_positions(self.ax1, positions, coords=coords, frame=frame, radius=radius)
    #     plot.plot_distances(self.ax1, positions, distance)
    #     self.ax1.legend()
    #     self.ax1.set_ylim(self.ax.get_ylim())
    #     self.ax1.set_xlim(self.ax.get_xlim())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
