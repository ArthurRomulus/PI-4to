import sys, cv2 as cv;
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QLabel;
from PyQt6.QtGui import QImage, QPixmap

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

        cap = cv.VideoCapture(0)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout);
        self.cameralabel = QLabel();
        self.cameralabel.setAlignment(Qt.AlignmentFlag.AlignHCenter);
        self.cameralabel.setFixedSize(400, 500);
        self.layout.addWidget(self.cameralabel);
        self.cap  = cv.VideoCapture(0);

        self.timer = QTimer();

        def update_frame(self):
            ret, frame = self.cap.read();
            if ret:
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB);
                h,w,ch = frame.shape;
                bpl = ch * w;

                qt_image = QImage(frame.data, w,h, bpl, QImage.Format.Format_RGB888)

                self.cameralabel.setPixmap(QPixmap.fromImage(qt_image))
        

        self.timer.timeout.connect(update_frame(self));
        self.timer.start(30);

        self.setWindowTitle("My app");
        button = QPushButton("Press me");
        button.setFixedSize(100, 50)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgb(255,255,255);
                color: rgb(45, 45, 45);
                border-color: rgb(45, 45, 45);
                border-radius: 10px;
                padding: 10px;
                font-size: 11px;
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