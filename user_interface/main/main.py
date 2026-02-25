import sys;

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton;

buttons = {
    "login" : {
        "name" : "login",
        "color" : (255, 255, 255),
    },
    
}



input = {
    "username" : {
        "name" : "username",
        "type" : "text",
    },

    "password" : {
        "name" : "password",
        "type" : "passwordtext",
    }
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();
        self.setWindowTitle("My app");
        button = QPushButton("Press me");
        button.setFixedSize(200, 100)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgb(255,255,255);
                color: rgb(45, 45, 45);
                border-color: rgb(45, 45, 45);
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(235, 235, 235);
                border-color: rgb(45, 45, 45);
            }
        """)
        self.setFixedSize(QSize(1000, 600))
        self.setCentralWidget(button)

app = QApplication(sys.argv);

w1 = MainWindow();
w1.show();

app.exec();