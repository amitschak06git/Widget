import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont, QAction

class ClockWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Remove window frame and keep on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Make background transparent/semi-transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Time Label
        self.label = QLabel()
        self.label.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); border-radius: 10px; padding: 10px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Timer to update time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()
        
        # Position (Top right corner approx)
        self.setGeometry(100, 100, 300, 100)

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.label.setText(current_time)

    def mousePressEvent(self, event):
        # Allow dragging the window
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def contextMenuEvent(self, event):
        # Right click to close
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ClockWidget()
    widget.show()
    sys.exit(app.exec())
