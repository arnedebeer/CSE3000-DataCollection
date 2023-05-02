from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton, QScrollArea, QWidget, QVBoxLayout, \
    QCheckBox, QComboBox
import sys
import matplotlib.pyplot as plt
import pickle
from PyQt5.QtCore import Qt
import glob


class MyWindow(QMainWindow):
    """Class used for viewing and editing dataset.

    The desired candidate number must be selected and the path to the dataset should be chosen.
    Once run, there is a dropdown at the top that allows which gesture to view.
    The buttons with numbers correspond to a gesture and when clicked, a graph of the gesture will be plotted.
    To remove gestures from a file, uncheck the checkboxes and click the "update file" button.
    Gestures can be moved between files by unchecking the checkbox of the desired gestures and clicking the "move file" gesture
    The file to move to can be changed with the variable path_move.
    """

    def __init__(self):
        super(MyWindow,self).__init__()

        # The candidate number to view
        self.candidate_no = 1

        # Getting all of the base paths in the dataset folder
        self.base_paths = []
        for filename in glob.iglob("./final_dataset/" + '**/**/*_hand', recursive=True):
            self.base_paths.append(filename)

        # Uncomment to view the control files
        # for filename in glob.iglob("./final_dataset/" + '**/**/control', recursive=True):
        #     self.base_paths.append(filename)

        self.base_path = self.base_paths[0]

        # Initialize UI
        self.initUI()

    def display_gesture(self):
        # Display the graph of a gesture
        index = self.sender().text()
        plt.plot(self.unpickled[int(index)])
        plt.xlabel('Time')
        plt.ylabel('Photodiode Reading')
        plt.title(f'Photodiode Reading for Candidate {self.candidate_no}')
        plt.show()

    def update_file(self):
        # Update a file by removing gestures
        with open(self.path, "wb") as file:
            for data, checkbox in zip(self.unpickled, self.checkboxes):
                if checkbox.isChecked():
                    pickle.dump(data, file)

        print("UPDATED FILE")

    def move_file(self):
        # Move a gesture from one pickled file to another
        with open(self.path, "wb") as file:
            for data, checkbox in zip(self.unpickled, self.checkboxes):
                if checkbox.isChecked():
                    pickle.dump(data, file)

        with open(self.path_move, "ab") as file:
            for data, checkbox in zip(self.unpickled, self.checkboxes):
                if not checkbox.isChecked():
                    pickle.dump(data, file)

        print("MOVED TO: ", self.path_move)

    def selectionchange(self, i):
        self.base_path = self.base_paths[i]
        self.clearUI()

    def clearUI(self):
        for i in reversed(range(self.vbox.count())):
            self.vbox.itemAt(i).widget().setParent(None)
        self.addUI()

    def addUI(self):
        self.path = f"{self.base_path}/candidate_{self.candidate_no}.pickle"

        # Change path to select the file to move a gesture to
        self.path_move = f"{self.base_path}/candidate_{self.candidate_no}.pickle"


        self.vbox.addWidget(self.cb)
        self.vbox.addWidget(self.b)
        self.vbox.addWidget(self.b2)
        self.buttons = []
        self.checkboxes = []
        index = 0

        with open(self.path, 'rb') as f:
            self.unpickled = []
            while True:
                try:
                    self.unpickled.append(pickle.load(f))
                    button = QPushButton(self)
                    button.setText(f"{index}")
                    button.clicked.connect(self.display_gesture)
                    self.buttons.append(button)

                    checkbox = QCheckBox(f"{index}")
                    checkbox.setChecked(True)
                    self.checkboxes.append(checkbox)

                    index += 1
                except EOFError:
                    break
        for button, checkbox in zip(self.buttons, self.checkboxes):
            self.vbox.addWidget(button)
            self.vbox.addWidget(checkbox, 1)

    def initUI(self):
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        self.cb = QComboBox()
        self.cb.addItems(self.base_paths)
        self.cb.currentIndexChanged.connect(self.selectionchange)

        w = QtWidgets.QWidget()
        self.scroll = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget()  # Widget that contains the collection of Vertical Box
        self.vbox = QVBoxLayout()

        self.b = QPushButton(self)
        self.b.setText("UPDATE FILE")
        self.b.clicked.connect(self.update_file)

        self.b2 = QPushButton(self)
        self.b2.setText("MOVE FILE")
        self.b2.clicked.connect(self.move_file)

        self.widget.setLayout(self.vbox)

        # Scroll Area Properties
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.setCentralWidget(self.scroll)

        self.setGeometry(100, 100, 1000, 900)
        self.setWindowTitle('Data Editor')
        self.show()

        self.addUI()

        return

    def closeEvent(self, event):
        event.accept()








def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

window()