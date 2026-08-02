import sys
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QGuiApplication
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QLabel, QFrame, QSlider)

class ScreenOverlay(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)

        self.start_point = QPoint()
        self.end_point = QPoint()
        self.snipping_rect = QRect()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        if not self.snipping_rect.isEmpty():
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.snipping_rect, QColor(0, 0, 0, 255))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            painter.setPen(QPen(QColor(0, 255, 200), 2))
            painter.drawRect(self.snipping_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.snipping_rect = QRect()
            self.update()

    def mouseMoveEvent(self, event):
        self.end_point = event.pos()
        self.snipping_rect = QRect(self.start_point, self.end_point).normalized()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            final_rect = QRect(self.start_point, self.end_point).normalized()
            if final_rect.isValid() and final_rect.width() > 10 and final_rect.height() > 10:
                self.main_window.final_selection(final_rect)
            self.close()

class ModernCanvas(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.showFullScreen()
        self.blur_opacity = 220

    def paintEvent(self, event):
        painter = QPainter(self)
        for rect in self.main_window.blur_rects:
            painter.fillRect(rect, QColor(0, 0, 0, self.blur_opacity))
            painter.setPen(QPen(QColor(0, 255, 200, 100), 1, Qt.DashLine))
            painter.drawRect(rect)

class MainControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Blur Tool Pro")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(380, 180)

        self.blur_rects = []
        self.canvas = ModernCanvas(self)

        layout = QVBoxLayout(self)

        title_label = QLabel("أداة التعتيم الاحترافية")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.status_label = QLabel("جاهز للتحديد")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()

        self.btn_blur = QPushButton("🟦 تعتيم منطقة")
        self.btn_blur.setStyleSheet("padding: 8px; font-weight: bold; background-color: #007bff; color: white; border-radius: 5px;")
        self.btn_blur.clicked.connect(self.start_blur_snip)
        btn_layout.addWidget(self.btn_blur)

        self.btn_clear = QPushButton("🗑️ مسح")
        self.btn_clear.setStyleSheet("padding: 8px; background-color: #6c757d; color: white; border-radius: 5px;")
        self.btn_clear.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.btn_clear)

        self.btn_exit = QPushButton("❌ خروج")
        self.btn_exit.setStyleSheet("padding: 8px; background-color: #dc3545; color: white; border-radius: 5px;")
        self.btn_exit.clicked.connect(self.close_all)
        btn_layout.addWidget(self.btn_exit)

        layout.addLayout(btn_layout)

        slider_layout = QHBoxLayout()
        slider_label = QLabel("درجة التعتيم:")
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(50, 255)
        self.blur_slider.setValue(220)
        self.blur_slider.valueChanged.connect(self.update_opacity)
        
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.blur_slider)
        layout.addLayout(slider_layout)

    def start_blur_snip(self):
        self.hide()
        QApplication.processEvents()
        self.overlay = ScreenOverlay(self)

    def final_selection(self, rect):
        self.blur_rects.append(rect)
        self.canvas.update()
        self.status_label.setText(f"تم إضافة منطقة ({len(self.blur_rects)})")
        self.show()

    def clear_all(self):
        self.blur_rects.clear()
        self.canvas.update()
        self.status_label.setText("تم المسح")

    def update_opacity(self):
        self.canvas.blur_opacity = self.blur_slider.value()
        self.canvas.update()

    def close_all(self):
        self.canvas.close()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainControlWindow()
    window.show()
    sys.exit(app.exec())