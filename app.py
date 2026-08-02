import sys
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel

class ScreenOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        self.drawing = False
        self.mode = "blur"
        self.start_point = QPoint()
        self.end_point = QPoint()
        
        self.blur_rects = []
        self.lines = []

    def set_mode(self, mode):
        self.mode = mode

    def clear_all(self):
        self.blur_rects.clear()
        self.lines.clear()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
        elif event.key() == Qt.Key_B:
            self.mode = "blur"
        elif event.key() == Qt.Key_P:
            self.mode = "pen"
        elif event.key() == Qt.Key_C:
            self.clear_all()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            if self.mode == "pen":
                self.lines.append((self.start_point, self.end_point))
                self.start_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.mode == "blur":
                rect = QRect(self.start_point, self.end_point).normalized()
                self.blur_rects.append(rect)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for rect in self.blur_rects:
            painter.fillRect(rect, QColor(0, 0, 0, 200))
            painter.setPen(QPen(QColor(0, 255, 200, 150), 1, Qt.DashLine))
            painter.drawRect(rect)

        if self.drawing and self.mode == "blur":
            current_rect = QRect(self.start_point, self.end_point).normalized()
            painter.fillRect(current_rect, QColor(0, 0, 0, 120))
            painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.DashLine))
            painter.drawRect(current_rect)

        painter.setPen(QPen(QColor(255, 50, 50), 3))
        for line in self.lines:
            painter.drawLine(line[0], line[1])


class ControlPanel(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        
        self.setWindowTitle("أداة التعتيم والتحكم")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100, 300, 100)

        layout = QVBoxLayout()

        self.status_label = QLabel("الوضع الحالي: تعتيم (Blur)")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()

        btn_blur = QPushButton("🟦 تعتيم")
        btn_blur.clicked.connect(self.set_blur_mode)
        btn_layout.addWidget(btn_blur)

        btn_pen = QPushButton("✏️ قلم")
        btn_pen.clicked.connect(self.set_pen_mode)
        btn_layout.addWidget(btn_pen)

        btn_clear = QPushButton("🗑️ مسح")
        btn_clear.clicked.connect(self.overlay.clear_all)
        btn_layout.addWidget(btn_clear)

        btn_exit = QPushButton("❌ خروج")
        btn_exit.clicked.connect(QApplication.quit)
        btn_layout.addWidget(btn_exit)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def set_blur_mode(self):
        self.overlay.set_mode("blur")
        self.status_label.setText("الوضع الحالي: تعتيم (Blur)")

    def set_pen_mode(self):
        self.overlay.set_mode("pen")
        self.status_label.setText("الوضع الحالي: رسم بقلم (Pen)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ScreenOverlay()
    panel = ControlPanel(overlay)
    panel.show()
    sys.exit(app.exec())