import sys
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QLabel, QSlider, QComboBox)

class ResizableBlurItem:
    def __init__(self, rect, style="Pixelate", opacity=220, radius=10):
        self.rect = rect
        self.style = style
        self.opacity = opacity
        self.radius = radius
        self.is_selected = False
        self.handle_size = 10

    def get_handles(self):
        r = self.rect
        s = self.handle_size
        return {
            'top_left': QRect(r.left() - s//2, r.top() - s//2, s, s),
            'top_right': QRect(r.right() - s//2, r.top() - s//2, s, s),
            'bottom_left': QRect(r.left() - s//2, r.bottom() - s//2, s, s),
            'bottom_right': QRect(r.right() - s//2, r.bottom() - s//2, s, s)
        }

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
                self.main_window.add_blur_item(final_rect)
            self.close()

class ModernCanvas(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        self.active_handle = None
        self.drag_start = QPoint()
        self.selected_item = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for item in self.main_window.blur_items:
            path = QPainterPath()
            path.addRoundedRect(item.rect, item.radius, item.radius)
            
            painter.save()
            painter.setClipPath(path)

            if item.style == "Pixelate":
                painter.fillRect(item.rect, QColor(200, 200, 200, item.opacity))
                p_size = 14
                for x in range(item.rect.left(), item.rect.right(), p_size):
                    for y in range(item.rect.top(), item.rect.bottom(), p_size):
                        shade = (x * 11 + y * 17) % 160 + 40
                        painter.fillRect(QRect(x, y, p_size, p_size), QColor(shade, shade, shade, item.opacity))
            elif item.style == "Solid":
                painter.fillRect(item.rect, QColor(0, 0, 0, item.opacity))
            elif item.style == "Soft Blur":
                painter.fillRect(item.rect, QColor(120, 120, 120, item.opacity))

            painter.restore()

            painter.setPen(QPen(QColor(0, 255, 200) if item.is_selected else QColor(255, 255, 255, 100), 2))
            painter.drawPath(path)

            if item.is_selected:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 255, 200)))
                for h_rect in item.get_handles().values():
                    painter.drawEllipse(h_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            self.selected_item = None
            self.active_handle = None

            for item in reversed(self.main_window.blur_items):
                handles = item.get_handles()
                for h_name, h_rect in handles.items():
                    if h_rect.contains(pos):
                        self.selected_item = item
                        self.active_handle = h_name
                        self.drag_start = pos
                        break
                
                if not self.active_handle and item.rect.contains(pos):
                    self.selected_item = item
                    self.active_handle = 'move'
                    self.drag_start = pos
                    break

            for item in self.main_window.blur_items:
                item.is_selected = (item == self.selected_item)

            self.update()

    def mouseMoveEvent(self, event):
        if self.selected_item and self.active_handle:
            delta = event.pos() - self.drag_start
            self.drag_start = event.pos()
            r = self.selected_item.rect

            if self.active_handle == 'move':
                self.selected_item.rect.translate(delta)
            elif self.active_handle == 'top_left':
                self.selected_item.rect.setTopLeft(r.topLeft() + delta)
            elif self.active_handle == 'bottom_right':
                self.selected_item.rect.setBottomRight(r.bottomRight() + delta)
            elif self.active_handle == 'top_right':
                self.selected_item.rect.setTopRight(r.topRight() + delta)
            elif self.active_handle == 'bottom_left':
                self.selected_item.rect.setBottomLeft(r.bottomLeft() + delta)

            self.update()

    def mouseReleaseEvent(self, event):
        self.active_handle = None

class MainControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Blur Tool Pro v2.0")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(400, 230)

        self.blur_items = []
        self.canvas = ModernCanvas(self)

        layout = QVBoxLayout(self)

        title_label = QLabel("أداة التعتيم الاحترافية Pro")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.status_label = QLabel("اختر النمط ثم اضغط تعتيم منطقة")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        options_layout = QHBoxLayout()
        
        style_label = QLabel("الشكل:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Pixelate", "Solid", "Soft Blur"])
        options_layout.addWidget(style_label)
        options_layout.addWidget(self.style_combo)

        radius_label = QLabel("الحواف:")
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(0, 40)
        self.radius_slider.setValue(10)
        options_layout.addWidget(radius_label)
        options_layout.addWidget(self.radius_slider)

        layout.addLayout(options_layout)

        btn_layout = QHBoxLayout()

        self.btn_blur = QPushButton("🟦 تعتيم منطقة")
        self.btn_blur.setStyleSheet("padding: 8px; font-weight: bold; background-color: #007bff; color: white; border-radius: 5px;")
        self.btn_blur.clicked.connect(self.start_blur_snip)
        btn_layout.addWidget(self.btn_blur)

        self.btn_auto = QPushButton("🎯 تتبع نافذة")
        self.btn_auto.setStyleSheet("padding: 8px; font-weight: bold; background-color: #28a745; color: white; border-radius: 5px;")
        self.btn_auto.clicked.connect(self.auto_target_window)
        btn_layout.addWidget(self.btn_auto)

        self.btn_clear = QPushButton("🗑️ مسح")
        self.btn_clear.setStyleSheet("padding: 8px; background-color: #6c757d; color: white; border-radius: 5px;")
        self.btn_clear.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.btn_clear)

        layout.addLayout(btn_layout)

        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("الشفافية:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(220)
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        layout.addLayout(opacity_layout)

        self.btn_exit = QPushButton("❌ خروج")
        self.btn_exit.setStyleSheet("padding: 6px; background-color: #dc3545; color: white; border-radius: 5px;")
        self.btn_exit.clicked.connect(self.close_all)
        layout.addWidget(self.btn_exit)

    def start_blur_snip(self):
        self.hide()
        QApplication.processEvents()
        self.overlay = ScreenOverlay(self)

    def auto_target_window(self):
        screen_geo = QApplication.primaryScreen().geometry()
        target_rect = QRect(screen_geo.width() // 4, screen_geo.height() // 4, screen_geo.width() // 2, screen_geo.height() // 2)
        self.add_blur_item(target_rect)
        self.status_label.setText("تم التحديد التلقائي لمنتصف الشاشة")

    def add_blur_item(self, rect):
        style = self.style_combo.currentText()
        opacity = self.opacity_slider.value()
        radius = self.radius_slider.value()
        item = ResizableBlurItem(rect, style, opacity, radius)
        self.blur_items.append(item)
        self.canvas.update()
        self.status_label.setText(f"تم إضافة منطقة تعتيم ({len(self.blur_items)})")
        self.show()

    def clear_all(self):
        self.blur_items.clear()
        self.canvas.update()
        self.status_label.setText("تم المسح بالكامل")

    def close_all(self):
        self.canvas.close()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainControlWindow()
    window.show()
    sys.exit(app.exec())