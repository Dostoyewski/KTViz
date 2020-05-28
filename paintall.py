import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QDoubleSpinBox
from konverter import coords_global
import math
import json


class Widget(QWidget):

    def __init__(self):
        super(Widget, self).__init__()
        self.layout = QVBoxLayout()
        # Latitude selection
        self.spinBox1 = QDoubleSpinBox(self)
        # Longitude selection
        self.spinBox2 = QDoubleSpinBox(self)
        self.keepDraw = False
        self.start = QPoint()
        self.end = QPoint()
        self.resize(600, 600)
        self.move(100, 100)
        self.setWindowTitle("Scenario drawer")
        self.type = 'our'
        self.image = []
        self.index = []
        # Scale: pixels in nm
        self.scale = 10
        self.initUI()

    def initUI(self):
        imageSize = QtCore.QSize(1366, 768)
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB32)
        self.image.fill(QtGui.qRgb(255, 255, 255))

        # Clear button
        button = QPushButton('Clear field', self)
        button.move(0, 0)
        button.resize(140, 50)
        button.clicked.connect(self.clear_window)

        # Convert button
        button1 = QPushButton('Convert', self)
        button1.move(140, 0)
        button1.resize(140, 50)
        button1.clicked.connect(self.convert_file)

        self.spinBox1.setRange(0, 360)
        self.spinBox1.move(280, 0)
        self.spinBox1.setValue(60)
        self.spinBox1.setSingleStep(0.01)

        self.spinBox2.setRange(0, 360)
        self.spinBox2.move(280, 25)
        self.spinBox2.setValue(30)
        self.spinBox2.setSingleStep(0.01)

    def clear_window(self):
        self.image.fill(QtGui.qRgb(255, 255, 255))
        self.type = 'our'
        self.index = []
        self.update()

    def convert_file(self):
        try:
            ship = [item for item in self.index if item['type'] == 'our'][0]
            targets = [item for item in self.index if item['type'] != 'our']
        except IndexError:
            print("Add ships first!")
            return
        data = []
        for target in targets:
            coords = coords_global(target['end'][0] - ship['end'][0],
                                   target['end'][1] - ship['end'][1],
                                   self.spinBox1.value(),
                                   self.spinBox2.value())
            data.append({'id': 'target',
                         'cat': 0,
                         'lat': coords[0],
                         'lon': coords[1],
                         'SOG': 14,
                         'COG': math.degrees(math.atan2(target['start'][1] - target['end'][1],
                                           target['start'][0] - target['end'][0])) + 90})
        with open("targets_file.json", "w") as fp:
            json.dump(data, fp)

        with open("our_file.json", "w") as fp:
            json.dump({'cat': 0,
                       'lat': self.spinBox1.value(),
                       'lon': self.spinBox2.value(),
                       'SOG': 14,
                       'COG': math.degrees(math.atan2(ship['start'][1] - ship['end'][1],
                                           ship['start'][0] - ship['end'][0])) + 90}, fp)

    def closeEvent(self, event):
        print("Closed")

    def paintEvent(self, event, type='circle'):
        painter = QPainter(self)
        cur_size = QRect(0, 0, self.width(), self.height())
        temp = self.image.copy(cur_size)
        painter.drawImage(event.rect(), temp)
        # painter.drawLine(self.start, self.end)
        if self.type == 'our':
            painter.setPen(QtCore.Qt.red)
            painter.drawLine(self.start, self.end)
            painter.drawEllipse(self.end, 10, 10)
        elif self.type == 'foreign':
            painter.setPen(QtCore.Qt.black)
            painter.drawLine(self.start, self.end)
            painter.drawEllipse(self.end, 10, 10)


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.keepDraw = True
            self.start = self.end = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.keepDraw:
            painter = QPainter(self.image)
            if self.type == 'our':
                painter.setPen(QtCore.Qt.red)
                painter.drawLine(self.start, self.end)
                painter.drawEllipse(self.end, 10, 10)
                self.index.append({'type': self.type,
                                   'start': [self.start.x(), self.start.y()],
                                   'end': [self.end.x(), self.end.y()]})
                self.type = 'foreign'
            elif self.type == 'foreign':
                painter.setPen(QtCore.Qt.black)
                painter.drawLine(self.start, self.end)
                painter.drawEllipse(self.end, 10, 10)
                self.index.append({'type': self.type,
                                   'start': [self.start.x(), self.start.y()],
                                   'end': [self.end.x(), self.end.y()]})
            self.update()
            self.keepDraw = False
            # Append new obj to array

    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.LeftButton) and self.keepDraw:
            self.end = event.pos()
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Widget()
    form.show()
    app.exec_()
