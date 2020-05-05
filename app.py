import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from main import prepare_file
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QFileDialog


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.title = 'KTViz 1.0'
        self.width = 640
        self.height = 400
        self.filename = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.m = PlotCanvas(self, width=5, height=4)
        self.m.move(0, 0)

        button = QPushButton('Load File', self)
        button.move(500, 0)
        button.resize(140, 50)
        button.clicked.connect(self.openFileNameDialog)

        # button = QPushButton('Plot', self)
        # button.move(500, 200)
        # button.resize(140, 100)
        # button.clicked.connect(self.m.plot(self.filename))
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Open JSON Trajectory", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if filename:
            self.filename = filename
            print(self.filename)
            self.m.plot(self.filename)


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=15, height=10, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        # self.plot('datafiles/sample_data.json')

    def plot(self, filename):
        ax = self.figure.add_subplot(111)
        ax.clear()
        prepare_file(filename, True, ax)
        ax.set_title('Trajectory')
        ax.axis('equal')
        self.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
