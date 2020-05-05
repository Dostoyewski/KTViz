import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from main import prepare_file
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QCheckBox


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.title = 'KTViz 1.0'
        self.width = 1200
        self.height = 800
        self.filename = ""
        self.relative = True
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.m = PlotCanvas(self, width=12, height=8)
        self.m.move(0, 0)

        button = QPushButton('Load Files', self)
        button.move(1000, 20)
        button.resize(140, 50)
        button.clicked.connect(self.openFileNameDialog)

        cb = QCheckBox('Relative coords', self)
        cb.move(20, 20)
        cb.toggle()
        cb.stateChanged.connect(self.update_state)
        self.show()

    def update_state(self):
        self.relative = not self.relative
        print(self.relative)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileNames(self, "Open JSON Trajectory", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if filename:
            self.filename = filename
            self.m.plot(self.filename, self.relative)


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

    def plot(self, filename, rel=False):
        ax = self.figure.add_subplot(111)
        ax.clear()
        for file in filename:
            prepare_file(file, True, ax, rel)
            ax.set_title('Trajectory')
            ax.axis('equal')
        self.draw()
        self.fig.savefig("img/image.png")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
