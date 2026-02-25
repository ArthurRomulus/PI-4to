import sys;

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton;



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();
        self.setWindowTitle("My app");
        button = QPushButton("Press me");
        button.setFixedSize(200, 100)
        self.setFixedSize(QSize(1000, 600))
        self.setCentralWidget(button)

app = QApplication(sys.argv);

w1 = MainWindow();
w1.show();

app.exec();