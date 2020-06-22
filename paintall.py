import json
import sys
import time

import math
from PIL import ImageGrab
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton, QDoubleSpinBox, \
    QLabel, QFileDialog, QAbstractItemView, QTreeView, QListView, QDialog

from konverter import coords_global

DEBUG = False

hmi_data = {
    "wind_direction": 189.0,
    "wind_speed": 1.1,
    "tide_direction": 0,
    "tide_speed": 0,
    "swell": 1,
    "visibility": 13.0
}

settings = {
    "maneuver_calculation": {
        "priority": 0,
        "maneuver_way": 2,
        "safe_diverg_dist": 3.0,
        "minimal_speed": 3.0,
        "maximal_speed": 30.0,
        "max_course_delta": 70.0,
        "time_advance": 300,
        "can_leave_route": True,
        "max_route_deviation": 1.5,
        "forward_speed1": 3.0,
        "forward_speed2": 9.75,
        "forward_speed3": 16.5,
        "forward_speed4": 23.25,
        "forward_speed5": 30.0,
        "reverse_speed1": 15.0,
        "reverse_speed2": 30.0,
        "max_circulation_radius": 0.4,
        "min_circulation_radius": 0.4,
        "breaking_distance": 0,
        "run_out_distance": 0,
        "forecast_time": 7200
    },
    "safety_control": {
        "cpa": 2.0,
        "tcpa": 180.0,
        "min_detect_dist": 15.0,
        "last_moment_dist": 2.0,
        "safety_zone": {
            "safety_zone_type": 0,
            "radius": 1.5
        }
    }
}

constraints = {
    "type": "FeatureCollection",
    "features": []
}


class Vector2(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __abs__(self):
        return (self.x**2 + self.y**2)**0.5

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __mul__(self, other):
        if type(other) == Vector2:
            return self.x * other.x + self.y * other.y
        elif type(other) == int or type(other) == float:
            return Vector2(self.x * other, self.y * other)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self


def det(a, b):
    """
    Pseudoscalar multiply of vectors
    :param a: 2D vector
    :param b: 2D vector
    :return: pseudoscalar multiply
    """
    return a.x * b.y - b.x * a.y


class CreateShipDialog(QDialog):
    """
    Creating new ship dialog
    """
    def __init__(self):
        super(CreateShipDialog, self).__init__()
        self.vel = QDoubleSpinBox(self)
        self.heading = QDoubleSpinBox(self)
        self.clsBtn = QPushButton('OK', self)
        self.resize(325, 100)
        self.setWindowTitle("Creating new ship")
        self.initUI()

    def initUI(self):
        # Velocity field
        lbe1 = QLabel(self)
        lbe1.setText('Velocity, knt:')
        lbe1.move(50, 5)
        self.vel.setRange(0, 100)
        self.vel.move(150, 0)
        self.vel.setValue(10)
        self.vel.setSingleStep(0.1)

        # Heading field
        lbe2 = QLabel(self)
        lbe2.setText('Heading, dgr:')
        lbe2.move(50, 30)
        self.heading.setRange(0, 360)
        self.heading.move(150, 30)
        self.heading.setValue(0)
        self.heading.setSingleStep(0.01)

        self.clsBtn.move(50, 60)
        self.clsBtn.clicked.connect(self.close)

    def exec_(self):
        """
        Custom exec function with vel and heading return
        :return:
        """
        super(CreateShipDialog, self).exec_()
        return self.vel.value(), self.heading.value()


class DrawingApp(QDialog):
    rs_signal = QtCore.pyqtSignal(QtCore.QSize)

    def __init__(self):
        super(DrawingApp, self).__init__()
        self.layout = QVBoxLayout()
        # Latitude selection
        self.spinBox1 = QDoubleSpinBox(self)
        # Longitude selection
        self.spinBox2 = QDoubleSpinBox(self)
        # Time horizont selection
        self.spinBox3 = QDoubleSpinBox(self)
        # Scaling spinBox
        self.spinBox4 = QDoubleSpinBox(self)
        self.keepDraw = False
        self.start = QPoint()
        self.end = QPoint()
        self.resize(900, 700)
        self.move(100, 100)
        self.setWindowTitle("Scenario drawer")
        self.type = 'our'
        self.image = []
        self.index = []
        # Scale: pixels in nm
        self.scale = 10
        # Preferred number of lines in grid
        self.n_line_x = 10
        self.n_line_y = 10
        # Time horizon
        self.time_horizon = 2
        # Flag if output dir is select
        # Default state is returned in clear_window()
        self.dir_select = False
        # Path to output dir
        self.path = ''
        # Flag if new ship is entered
        self.proc_draw = False
        # Ship params from dialog
        self.vel = 0
        self.heading = 0
        # Velocity of our ship
        self.v0 = Vector2(0, 0)
        # Some hotfix flag
        self.first = True
        self.initUI()

    def initUI(self):
        imageSize = QtCore.QSize(1366, 768)
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB32)
        self.image.fill(QtGui.qRgb(255, 255, 255))

        # Resize signal
        self.rs_signal.connect(self.resize_grid)

        # Clear button
        button = QPushButton('Clear field', self)
        button.move(0, 0)
        button.resize(140, 50)
        button.clicked.connect(self.clear_window)

        # Convert button
        button1 = QPushButton('Convert', self)
        button1.move(140, 0)
        button1.resize(140, 50)
        button1.clicked.connect(self.open_or_create_directory)

        # Latitude spinbox
        lbe = QLabel(self)
        lbe.setText('Start Latitude:')
        lbe.move(280, 5)
        self.spinBox1.setRange(0, 360)
        self.spinBox1.move(400, 0)
        self.spinBox1.setValue(60)
        self.spinBox1.setSingleStep(0.01)

        # Longitude spinbox
        lbe1 = QLabel(self)
        lbe1.setText('Start Longitude:')
        lbe1.move(280, 30)
        self.spinBox2.setRange(0, 360)
        self.spinBox2.move(400, 25)
        self.spinBox2.setValue(30)
        self.spinBox2.setSingleStep(0.01)

        # save to Viz format file
        if DEBUG:
            self.viz = QPushButton('Save to Viz', self)
            self.viz.move(610, 15)
            self.viz.resize(140, 50)
            self.viz.clicked.connect(self.save_to_viz)

        self.viz = QPushButton('Create new ship', self)
        self.viz.move(500, 0)
        self.viz.resize(140, 50)
        self.viz.clicked.connect(self.create_ship)

        # Time horizon values
        lbe3 = QLabel(self)
        lbe3.setText('Time horizon:')
        lbe3.move(650, 5)
        self.spinBox3.setRange(0, 10)
        self.spinBox3.move(765, 0)
        self.spinBox3.setValue(2)
        self.spinBox3.setSingleStep(0.01)

        # Scaling params
        lbe4 = QLabel(self)
        lbe4.setText('Scale, px in nm:')
        lbe4.move(650, 30)
        self.spinBox4.setRange(0.01, 1000)
        self.spinBox4.move(765, 25)
        self.spinBox4.setValue(10)
        self.spinBox4.setSingleStep(0.1)
        self.spinBox4.valueChanged.connect(self.update_scale)

        self.draw_grid()

    def update_scale(self):
        self.scale = self.spinBox4.value()
        self.clear_window()
        self.draw_grid()

    def create_ship(self):
        updateDialog = CreateShipDialog()
        self.vel, self.heading = updateDialog.exec_()
        self.proc_draw = True
        self.keepDraw = True

    def open_or_create_directory(self):
        """
        Creates dialog with output directory selection
        :return:
        """
        img = ImageGrab.grab()
        if not self.dir_select:
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.DontUseNativeDialog, True)

            l = dialog.findChild(QListView, "listView")
            if l is not None:
                l.setSelectionMode(QAbstractItemView.MultiSelection)
            t = dialog.findChild(QTreeView)
            if t is not None:
                t.setSelectionMode(QAbstractItemView.MultiSelection)

            nMode = dialog.exec_()
            self.path = dialog.selectedFiles()[0]
            self.dir_select = True

        img.save(self.path + "/scenario.jpeg", "JPEG")
        self.convert_file(self.path)
        
    def update_values(self):
        """
        Updating drawing params
        :return:
        """
        self.time_horizon = self.spinBox3.value()
        print(self.time_horizon)

    def resizeEvent(self, event):
        """
        event onResize
        :param event:
        :return:
        """
        self.rs_signal.emit(self.size())

    def resize_grid(self):
        """
        re-draws grid for new size
        :return:
        """
        self.clear_window(True)
        self.draw_grid()
        self.plot_all_targets()

    def clear_window(self, upd=False):
        """
        Cleares window and sets some flags to default
        :param upd: flag to recreate self.index
        :return:
        """
        self.image.fill(QtGui.qRgb(255, 255, 255))
        if not upd:
            self.type = 'our'
            self.index = []
        self.update()
        self.draw_grid()
        self.dir_select = False

    def draw_grid(self):
        """
        This function draws nm grid
        :return:
        """
        painter = QPainter(self.image)
        # Optimal step — 60 pixels
        optimal_step = 60
        self.n_line_x = round(self.width() / optimal_step)
        self.n_line_y = round(self.height() / optimal_step)
        stepw = self.width() / self.n_line_x
        steph = self.height() / self.n_line_y
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        pen.setStyle(Qt.DashDotDotLine)
        painter.setPen(pen)
        for i in range(self.n_line_x+1):
            painter.drawLine(i*stepw, 0, i*stepw, self.height())
            painter.drawText(i*stepw, self.n_line_y*steph - 10,
                             str(round(i*stepw / self.scale, 2)))
        for i in range(self.n_line_y + 1):
            painter.drawLine(0, i * steph, self.width(), i * steph)
            painter.drawText(self.n_line_x * stepw - 40, self.height() - i * steph,
                             str(round(i * steph / self.scale, 2)))

    def convert_file(self, path):
        """
        Makes JSON scenario files
        :param path: path to directory with out files
        :return:
        """
        try:
            ship = [item for item in self.index if item['type'] == 'our'][0]
            targets = [item for item in self.index if item['type'] != 'our']
        except IndexError:
            print("Add ships first!")
            return
        timestamp = int(time.time())
        data = []
        for target in targets:
            coords = coords_global(-(target['end'][1] - ship['end'][1]) / self.scale,
                                   (target['end'][0] - ship['end'][0]) / self.scale,
                                   self.spinBox1.value(),
                                   self.spinBox2.value())
            data.append({'id': 'target' + str(targets.index(target)),
                         'cat': 0,
                         'lat': coords[0],
                         'lon': coords[1],
                         'SOG': target['vel'],
                         'COG': target['heading'],
                         "first_detect_dist": 5.0,
                         "cross_dist": 0,
                         "timestamp": timestamp
                         })
        with open(path + "/target-data.json", "w") as fp:
            json.dump(data, fp)

        with open(path + "/nav-data.json", "w") as fp:
            route_item = {
                'begin_angle': ship['heading'],
                'curve': 0,
                'duration': self.spinBox3.value() * 3600,
                'lat': self.spinBox1.value(),
                'lon': self.spinBox2.value(),
                'length': self.spinBox3.value() * ship['vel'],
                "port_dev": 2,
                "starboard_dev": 2
            }

            with open(path + "/route-data.json", "w") as fr:
                json.dump({"items": [
                    route_item
                ],
                    'start_time': timestamp}, fr)

            json.dump({'cat': 0,
                       'lat': self.spinBox1.value(),
                       'lon': self.spinBox2.value(),
                       'SOG': ship['vel'],
                       'STW': ship['vel'],
                       'COG': ship['heading'],
                       'heading': ship['heading'],
                       "width": 16.0,
                       "length": 100.0,
                       "width_offset": 10.0,
                       "length_offset": 15.0,
                       'timestamp': timestamp}, fp)

        with open(path + "/constraints.json", "w") as fp:
            json.dump(constraints, fp)

        with open(path + "/hmi-data.json", "w") as fp:
            json.dump(hmi_data, fp)

        with open(path + "/settings.json", "w") as fp:
            json.dump(settings, fp)

        print('Success')

    def save_to_viz(self):
        """
        Saves all data to KTViz format
        :return:
        """
        try:
            ship = [item for item in self.index if item['type'] == 'our'][0]
            targets = [item for item in self.index if item['type'] != 'our']
        except IndexError:
            print("Add ships first!")
            return
        data = []
        for target in self.index:
            coords = coords_global(-(target['end'][1] - ship['end'][1]) / self.scale,
                                   (target['end'][0] - ship['end'][0]) / self.scale,
                                   self.spinBox1.value(),
                                   self.spinBox2.value())
            data.append({"items": [
                {
                    "lat": coords[0], "lon": coords[1],
                    "begin_angle": target['heading'],
                    "curve": 0.0,
                    "duration": 3140.0,
                    "length": 13.083333333333334,
                    "port_dev": 0.0,
                    "starboard_dev": 0.0
                }
            ],
                "start_time": 1588154400})
        with open("temp.json", "w") as fp:
            json.dump(data, fp)

    def closeEvent(self, event):
        print("Closed")

    def plot_all_targets(self):
        """
        This function plots all obj in self.index after resize
        :return:
        """
        painter = QPainter(self.image)
        for obj in self.index:
            if obj['type'] == 'our':
                pen = QPen(Qt.red, 2, Qt.SolidLine)
                painter.setPen(pen)
            else:
                pen = QPen(Qt.blue, 2, Qt.SolidLine)
                painter.setPen(pen)
            start = QPoint(obj['start'][0], obj['start'][1])
            end = QPoint(obj['end'][0], obj['end'][1])
            painter.drawLine(start, end)
            painter.drawEllipse(end, 10, 10)

    def paintEvent(self, event, type='circle'):
        """
        Event handler for painter
        :param event:
        :param type:
        :return:
        """
        painter = QPainter(self)
        cur_size = QRect(0, 0, self.width(), self.height())
        temp = self.image.copy(cur_size)
        painter.drawImage(event.rect(), temp)
        # painter.drawLine(self.start, self.end)
        if self.type == 'our' or self.first:
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.start, self.end)
            painter.drawEllipse(self.end, 10, 10)
            self.first = False
        elif self.type == 'foreign':
            pen = QPen(Qt.blue, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(self.start, self.end)
            painter.drawEllipse(self.end, 10, 10)
            # Draw dist between target ship and our
            pen = QPen(Qt.green, 2, Qt.SolidLine)
            painter.setPen(pen)
            our_pose = QPoint(self.index[0]['end'][0], self.index[0]['end'][1])
            painter.drawLine(self.end, our_pose)
            mid_x = (self.end.x() + our_pose.x()) / 2
            mid_y = (self.end.y() + our_pose.y()) / 2
            dist = ((self.end.x() - our_pose.x())**2 + (self.end.y() - our_pose.y())**2)**0.5
            v = Vector2(self.vel * math.cos(math.radians(self.heading)),
                              self.vel * math.sin(math.radians(self.heading)))
            R = Vector2(-(self.end.y() - our_pose.y()) / self.scale,
                        (self.end.x() - our_pose.x()) / self.scale)
            try:
                pen = QPen(Qt.black, 2, Qt.SolidLine)
                painter.setPen(pen)
                cpa, tcpa = self.calc_cpa_params(v, self.v0, R)
                min_pose = v * tcpa
                min_pose_o = self.v0 * tcpa
                mpd_point = QPoint()
                mpd_point_o = QPoint()
                # Our min dist point
                mpd_point.setX(self.end.x() + min_pose.y * self.scale)
                mpd_point.setY(self.end.y() - min_pose.x * self.scale)
                # Target min dist point
                mpd_point_o.setX(our_pose.x() + min_pose_o.y * self.scale)
                mpd_point_o.setY(our_pose.y() - min_pose_o.x * self.scale)
                painter.drawText(mid_x, mid_y, str(round(dist / self.scale, 2)))
                if tcpa > 0:
                    painter.drawText(mid_x, mid_y + 20, 'CPA: ' + str(round(cpa, 2)))
                    painter.drawText(mid_x, mid_y + 40, 'tCPA: ' + str(round(tcpa, 2)))
                    pen = QPen(Qt.blue, 2, Qt.SolidLine)
                    painter.setPen(pen)
                    painter.drawEllipse(mpd_point, 4, 4)
                    pen = QPen(Qt.red, 2, Qt.SolidLine)
                    painter.setPen(pen)
                    painter.drawEllipse(mpd_point_o, 4, 4)
                else:
                    painter.drawText(mid_x, mid_y + 40, 'tCPA: ' + '0')
            except ZeroDivisionError:
                painter.drawText(mid_x, mid_y, str(dist / self.scale))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.proc_draw:
            self.keepDraw = True
            self.end = event.pos()
            self.start.setX(self.end.x() + 30*math.cos(math.radians(self.heading - 90)))
            self.start.setY(self.end.y() + 30*math.sin(math.radians(self.heading - 90)))

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.keepDraw:
            painter = QPainter(self.image)
            if self.type == 'our':
                pen = QPen(Qt.red, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(self.start, self.end)
                painter.drawEllipse(self.end, 10, 10)
                self.index.append({'type': self.type,
                                   'vel': self.vel,
                                   'heading': self.heading,
                                   'start': [self.start.x(), self.start.y()],
                                   'end': [self.end.x(), self.end.y()]})
                self.v0 = Vector2(self.vel * math.cos(math.radians(self.heading)),
                                  self.vel * math.sin(math.radians(self.heading)))
                self.type = 'foreign'
            elif self.type == 'foreign':
                pen = QPen(Qt.blue, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(self.start, self.end)
                painter.drawEllipse(self.end, 10, 10)
                self.index.append({'type': self.type,
                                   'vel': self.vel,
                                   'heading': self.heading,
                                   'start': [self.start.x(), self.start.y()],
                                   'end': [self.end.x(), self.end.y()]})
            self.update()
            self.keepDraw = False
            self.proc_draw = False

    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.LeftButton) and self.keepDraw and self.proc_draw:
            self.end = event.pos()
            self.start.setX(self.end.x() + 30*math.cos(math.radians(self.heading - 90)))
            self.start.setY(self.end.y() + 30*math.sin(math.radians(self.heading - 90)))
        self.update()

    @staticmethod
    def calc_cpa_params(v, v0, R):
        """
        Calculating of CPA and tCPA criterions
        :param v: target speed, vector
        :param v0: our speed, vector
        :param R: relative position, vector
        :return:
        """
        w = v - v0
        cpa = abs(det(R, w) / abs(w))
        tcpa = - (R * w) / (w * w)
        return cpa, tcpa


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = DrawingApp()
    form.show()
    app.exec_()
