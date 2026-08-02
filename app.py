 import sys
from PySide6.QtCore import Qt, QRect, QPoint, QSize, Property, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QGuiApplication, QIcon, QPalette
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, 
                             QLabel, QFrame, QGraphicsDropShadowEffect, QSlider, QSizePolicy)

class ModernButton(QPushButton):
    def __init__(self, text, icon_text, is_danger=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.is_danger = is_danger
        self.setMinimumHeight(45)
        self.setIcon(QIcon(icon_text))
        
        # Base style sheet
        bg_color = "#dc3545" if is_danger else "#3498db"
        hover_color = "#c82333" if is_danger else "#2980b9"
        
        self.setStyleSheet(f"""
            ModernButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 22px;
                padding-left: 15px;
                padding-right: 15px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }}
            ModernButton:hover {{
                background-color: {hover_color};
            }}
            ModernButton:pressed {{
                margin-top: 7px;
                margin-bottom: 3px;
                background-color: #2c3e50;
            }}
        """)
        
        # Add a subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setXOffset(1)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # The main style: white, semi-transparent background, rounded corners
        self.setStyleSheet("""
            GlassFrame {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 30px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(3)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

class ScreenOverlay(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor) # Sniper crosshair cursor

        self.start_point = QPoint()
        self.end_point = QPoint()
        self.snipping_rect = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Paint a full-screen semi-transparent dim layer
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        # 2. If snipping, carve out the rectangle to make it clear
        if self.snipping_rect and not self.snipping_rect.isEmpty():
            # Source-over compositing will make this region clear
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.snipping_rect, QColor(0,0,0,255))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # Draw a bright border for the selection
            painter.setPen(QPen(QColor(255, 255, 255), 2))
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
            self.close() # Close the snipping window and restore the main window
            self.main_window.overlay = None

class ModernCanvas(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.showFullScreen()
        
        self.blur_opacity = 200 # Initial opacity

    def set_blur_opacity(self, value):
        self.blur_opacity = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for rect in self.main_window.blur_rects:
            painter.fillRect(rect, QColor(0, 0, 0, self.blur_opacity))
            
            # Subtle dash border
            painter.setPen(QPen(QColor(0, 255, 200, 100), 1, Qt.DashLine))
            painter.drawRect(rect)

class MainControlWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("أداة التعتيم الاحترافية Pro")
        
        # Transparent background for the window, will be filled by GlassFrame
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.resize(QSize(420, 220))

        self.blur_rects = []
        self.overlay = None
        
        self.canvas = ModernCanvas(self)

        # Root layout to manage the GlassFrame
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        
        # The main content frame with glass effect
        self.main_frame = GlassFrame(self)
        root_layout.addWidget(self.main_frame)

        # Layout inside the frame
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(25, 20, 25, 20)
        frame_layout.setSpacing(10)

        # Title Label
        title_label = QLabel("لوحة التحكم بالبث المباشر")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)

        # Status Label
        self.status_label = QLabel("اختر منطقة لتعتيمها على الفور")
        self.status_label.setStyleSheet("font-size: 12px; color: #777; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.status_label)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("border: 1px solid rgba(0,0,0,15);")
        frame_layout.addWidget(divider)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # Modernized Buttons
        self.btn_blur = ModernButton("🟦 تعتيم المنطقة", "None", False, self)
        self.btn_blur.clicked.connect(self.start_blur_snip)
        btn_layout.addWidget(self.btn_blur)

        self.btn_clear = ModernButton("🗑️ مسح", "None", False, self)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_clear.setEnabled(False)
        btn_layout.addWidget(self.btn_clear)

        self.btn_exit = ModernButton("❌ خروج", "None", True, self)
        self.btn_exit.clicked.connect(self.close_and_canvas)
        btn_layout.addWidget(self.btn_exit)

        frame_layout.addLayout(btn_layout)

        # Blur Opacity Slider
        slider_layout = QHBoxLayout()
        slider_label = QLabel("شدة التعتيم: ")
        slider_label.setStyleSheet("color: #555;")
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(50, 255) # Lower limit is semi-transparent
        self.blur_slider.setValue(self.canvas.blur_opacity)
        self.blur_slider.valueChanged.connect(self.update_blur_opacity)
        self.blur_slider.setFixedWidth(200)
        self.blur_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid rgba(0,0,0,20);
                height: 8px;
                background: rgba(255,255,255,100);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)

        slider_layout.addStretch()
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.blur_slider)
        slider_layout.addStretch()
        frame_layout.addLayout(slider_layout)
        
        # Center the window initially
        self.move(QGuiApplication.primaryScreen().availableGeometry().center() - self.rect().center())

    def start_blur_snip(self):
        self.hide() # Hide control panel like snipping tool
        QApplication.processEvents() # Ensure the hide is processed before overlay creation
        self.overlay = ScreenOverlay(self)

    def final_selection(self, rect):
        # We now use the selection for blur instead of pen
        self.blur_rects.append(rect)
        self.canvas.update()
        self.status_label.setText(f"تمت إضافة منطقة تعتيم ({len(self.blur_rects)})")
        self.btn_clear.setEnabled(True)
        self.show() # Bring control panel back

    def clear_all(self):
        self.blur_rects.clear()
        self.canvas.update()
        self.status_label.setText("تم مسح جميع المناطق")
        self.btn_clear.setEnabled(False)

    def update_blur_opacity(self):
        self.canvas.set_blur_opacity(self.blur_slider.value())

    def close_and_canvas(self):
        self.canvas.close()
        self.close()

    # Make the entire GlassFrame draggable
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Modern styling for QLabels
    app.setStyleSheet("QLabel { font-family: 'Segoe UI', Arial; }")
    
    window = MainControlWindow()
    window.show()
    sys.exit(app.exec())