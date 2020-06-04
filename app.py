#!/usr/bin/env python3
import os
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton, QLabel
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QSlider, QDoubleSpinBox, QWidget, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from main import prepare_file, check_type


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

        # Show velocity near ships
        self.cb1 = QCheckBox("Show vel", self)
        self.verticalLayout.addWidget(self.cb1)

        # Show dist between ships
        self.cb2 = QCheckBox("Show dist", self)
        self.verticalLayout.addWidget(self.cb2)

        # Show Global coordinates
        self.cb3 = QCheckBox("Show GC", self)
        self.verticalLayout.addWidget(self.cb3)
        self.horizontalLayout.addLayout(self.verticalLayout)

        # Safe radius select
        self.label = QLabel('Safe radius:', self)
        self.horizontalLayout.addWidget(self.label)
        self.spinBox = QDoubleSpinBox(self)
        self.spinBox.setObjectName("doubleSpinBox")
        self.horizontalLayout.addWidget(self.spinBox)


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
        self.button1 = QPushButton('Update', self)

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
        self.vel = PlotCanvas(self, width=round(6 * self.scale_x), height=round(7 * self.scale_y))
        self.loaded = False
        self.initUI()

    def initUI(self):
        # Resize signal
        self.rs_signal.connect(self.resize_app)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.widthp, self.heightp)

        self.params.move(int(0.677*self.width()), 0)
        self.params.resize(int(0.298*self.width()), 0.106*self.height())

        # Initialization of canvas
        self.m.move(0, 0)

        # Load button
        self.params.pushButton.clicked.connect(self.openFileNameDialog)

        # Slider config
        self.sl.setMinimum(0)
        self.sl.setMaximum(99)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(1)
        self.sl.setGeometry(int(50 * self.scale_x), int(840 * self.scale_y),
                            int(1100 * self.scale_x), 50)
        self.sl.valueChanged.connect(self.value_changed)

        # Update button
        self.button1.move(1200 * self.scale_x, 820 * self.scale_y)
        self.button1.resize(120, 35)
        self.button1.clicked.connect(self.reload)

        # Safe radius box
        self.params.spinBox.setRange(0, 10)
        self.params.spinBox.setValue(1.5)
        self.params.spinBox.setSingleStep(0.1)
        self.params.spinBox.valueChanged.connect(self.value_changed)

        # Show text checkbox
        self.params.cb1.move(1400 * self.scale_x, 5 * self.scale_y)
        self.params.cb1.toggle()
        self.params.cb1.stateChanged.connect(self.value_changed)

        # Show dist checkbox
        self.params.cb2.move(1400 * self.scale_x, 30 * self.scale_y)
        self.params.cb2.toggle()
        self.params.cb2.stateChanged.connect(self.value_changed)

        # Show WGS checkbox
        self.params.cb3.move(1400 * self.scale_x, 55 * self.scale_y)
        self.params.cb3.toggle()
        self.params.cb3.stateChanged.connect(self.value_changed)

        self.vel.move(1200 * self.scale_x, 120 * self.scale_y)
        self.show()

    def resize_app(self):
        """
        Scales all element positions and sizes
        :return:
        """
        self.params.move(int(0.677 * self.width()), 10)
        self.params.resize(int(0.298 * self.width()), 0.106 * self.height())
        self.m.resize(int(0.67 * self.width()), int(0.926 * self.height()))
        self.sl.setGeometry(int(0.028 * self.width()), int(0.933 * self.height()),
                            int(0.611 * self.width()), 50)
        self.button1.move(int(0.677 * self.width()), int(0.933 * self.height()))
        self.vel.move(int(0.667 * self.width()), int(0.132 * self.height()))
        self.vel.resize(int(0.298 * self.width()), 0.794 * self.height())

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
        if self.loaded:
            self.m.plot(self.filename, self.relative, self.sl.value(), self.params.spinBox.value(),
                        self.params.cb1.isChecked(), self.params.cb2.isChecked(), show_coords=self.params.cb3.isChecked(),
                        fig=self.vel, is_loaded=False)

    def value_changed(self):
        """
        Update plot onChange values
        :return:
        """
        if self.loaded:
            self.m.plot(self.filename, self.relative, self.sl.value(), self.params.spinBox.value(),
                        self.params.cb1.isChecked(), self.params.cb2.isChecked(), show_coords=self.params.cb3.isChecked(),
                        fig=self.vel, is_loaded=True)

    def update_state(self):
        """
        Used to switch between global and relative coords
        :return:
        """
        self.relative = not self.relative
        self.m.plot(self.filename, self.relative, self.sl.value(), self.params.spinBox.value(),
                    self.params.cb1.isChecked(), self.params.cb2.isChecked(), show_coords=self.params.cb3.isChecked(),
                    fig=self.vel, is_loaded=False)

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
            self.filename = filename
            self.loaded = True
            self.m.plot(self.filename, self.relative, self.sl.value(), self.params.spinBox.value(),
                        self.params.cb1.isChecked(), self.params.cb2.isChecked(), show_coords=self.params.cb3.isChecked(),
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
