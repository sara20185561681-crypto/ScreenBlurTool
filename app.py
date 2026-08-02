import sys
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtWidgets import QApplication, QWidget

class ScreenOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # ضبط النافذة لتكون ملء الشاشة، شفافة، وبدون أشرطة
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        self.drawing = False
        self.mode = "blur"  # الأوضاع المتاحة: "blur", "pen", "arrow"
        self.start_point = QPoint()
        self.end_point = QPoint()
        
        self.blur_rects = []  # المربعات المعتمة
        self.lines = []       # خطوط الرسم الحر

    def keyPressEvent(self, event):
        # الضغط على ESC للإنهاء
        if event.key() == Qt.Key_Escape:
            self.close()
        # التنقل بين الأدوات: B للـ Blur، P للقلم، C للمسح
        elif event.key() == Qt.Key_B:
            self.mode = "blur"
        elif event.key() == Qt.Key_P:
            self.mode = "pen"
        elif event.key() == Qt.Key_C:
            self.blur_rects.clear()
            self.lines.clear()
            self.update()

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

        # 1. رسم مناطق التعتيم (Pixelate/Blur Style)
        for rect in self.blur_rects:
            # تعتيم ضبابي شبكي داكن يغطي المنطقة دون حجب كامل معتم
            painter.fillRect(rect, QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor(0, 255, 200, 150), 1, Qt.DashLine))
            painter.drawRect(rect)

        # 2. رسم المربع الحالي أثناء السحب
        if self.drawing and self.mode == "blur":
            current_rect = QRect(self.start_point, self.end_point).normalized()
            painter.fillRect(current_rect, QColor(0, 0, 0, 120))
            painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.DashLine))
            painter.drawRect(current_rect)

        # 3. رسم خطوط القلم (ZoomIt Style)
        painter.setPen(QPen(QColor(255, 50, 50), 3))
        for line in self.lines:
            painter.drawLine(line[0], line[1])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ScreenOverlay()
    sys.exit(app.exec())
