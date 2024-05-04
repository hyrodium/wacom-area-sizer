import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSystemTrayIcon,
)
from PySide6.QtGui import QPainter, QColor, QPalette, QIcon, QPen, QFont
from PySide6.QtCore import Qt, QRect
import subprocess
from pathlib import Path

DISPLAY_X = 3840
DISPLAY_Y = 2160
TABLET_X = 21600
TABLET_Y = 13500
DEFAULT_OPACITY = 0.7
ID_DEVICE = 11
PATH_ICON = Path(__file__).parent / "icon.png"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Opaque by default
        self.flag_opacity = True
        # Rotation index (0,1,2,3)
        self.rotation = 0
        # Tablet size
        self.tablet_x = TABLET_X
        self.tablet_y = TABLET_Y

        self.setWindowTitle("wacom area sizer")
        self.setWindowIcon(QIcon(str(PATH_ICON)))
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255, 255))
        self.setPalette(palette)

        # System tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(PATH_ICON)))
        self.tray_icon.setVisible(True)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.resize(800, 600)
        self.setup_ui()
        self.update_info()

    def paintEvent(self, event):
        draw_area = self.rect()
        width = draw_area.width() - 20
        height = draw_area.height() - 60

        # Window vs Display
        if width * DISPLAY_Y <= height * DISPLAY_X:
            _display_y = width
            _display_x = width * DISPLAY_Y / DISPLAY_X
        else:
            _display_y = height * DISPLAY_X / DISPLAY_Y
            _display_x = height

        _display_origin_x = (width - _display_y) / 2 + 10
        _display_origin_y = (height - _display_x) / 2 + 10
        ratio = (_display_y / DISPLAY_X + _display_x / DISPLAY_Y) / 2

        frame = self.frameGeometry()
        window_origin_x = frame.x()
        window_origin_y = frame.y()
        window_x = frame.width()
        window_y = frame.height()
        _window_origin_x = _display_origin_x + window_origin_x * ratio
        _window_origin_y = _display_origin_y + window_origin_y * ratio
        _window_x = window_x * ratio
        _window_y = window_y * ratio

        # Window vs Tablet
        if self.tablet_x / self.tablet_y < window_x / window_y:
            _tablet_x = _window_x
            _tablet_y = _window_x * self.tablet_y / self.tablet_x
            delta = (_tablet_y - _window_y) / 2
            _tablet_origin_x = _window_origin_x
            _tablet_origin_y = _window_origin_y - delta
        else:
            _tablet_x = _window_y * self.tablet_x / self.tablet_y
            _tablet_y = _window_y
            delta = (_tablet_x - _window_x) / 2
            _tablet_origin_x = _window_origin_x - delta
            _tablet_origin_y = _window_origin_y

        radius = 5
        if self.rotation == 0:
            _circle_origin_x = _tablet_origin_x - radius + 2 * radius
            _circle_origin_y = _tablet_origin_y - radius + _tablet_y / 2
            _circle_x = 2 * radius
            _circle_y = 2 * radius
        elif self.rotation == 1:
            _circle_origin_x = _tablet_origin_x - radius + _tablet_x / 2
            _circle_origin_y = _tablet_origin_y - radius + _tablet_y - 2 * radius
            _circle_x = 2 * radius
            _circle_y = 2 * radius
        elif self.rotation == 2:
            _circle_origin_x = _tablet_origin_x - radius + _tablet_x - 2 * radius
            _circle_origin_y = _tablet_origin_y - radius + _tablet_y / 2
            _circle_x = 2 * radius
            _circle_y = 2 * radius
        elif self.rotation == 3:
            _circle_origin_x = _tablet_origin_x - radius + _tablet_x / 2
            _circle_origin_y = _tablet_origin_y - radius + 2 * radius
            _circle_x = 2 * radius
            _circle_y = 2 * radius

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(_display_origin_x, _display_origin_y, _display_y, _display_x)

        painter.setBrush(QColor(255, 200, 200))
        painter.drawRect(
            _window_origin_x,
            _window_origin_y,
            _window_x,
            _window_y,
        )
        painter.setPen(QPen(Qt.black, 2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            _tablet_origin_x,
            _tablet_origin_y,
            _tablet_x,
            _tablet_y,
        )

        painter.setFont(QFont("Arial", 14))
        painter.setPen(Qt.black)
        text_rect = QRect(_display_origin_x, _display_origin_y, 200, 20)
        painter.drawText(text_rect, Qt.AlignLeft, "Entire display")
        text_rect = QRect(_window_origin_x, _window_origin_y, 200, 20)
        painter.drawText(text_rect, Qt.AlignLeft, "Window")
        text_rect = QRect(_tablet_origin_x, _tablet_origin_y - 20, 200, 20)
        painter.drawText(text_rect, Qt.AlignLeft, "Tablet")

        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(
            _circle_origin_x,
            _circle_origin_y,
            _circle_x,
            _circle_y,
        )

        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_info()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.update_info()

    def setup_ui(self):
        # Add buttons
        self.button_rotate = QPushButton("Rotate")
        self.button_opacity = QPushButton("Fade / Reveal")
        self.button_hide = QPushButton("Hide")

        # Layout
        hbox = QHBoxLayout()
        hbox.addWidget(self.button_rotate)
        hbox.addWidget(self.button_opacity)
        hbox.addWidget(self.button_hide)
        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.button_rotate.clicked.connect(self.rotate_tablet)
        self.button_opacity.clicked.connect(self.toggle_opacity)
        self.button_hide.clicked.connect(self.hidewindow)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hidewindow()
            event.accept()
        else:
            super().keyPressEvent(event)

    def rotate_tablet(self):
        self.rotation = (self.rotation + 1) % 4
        if self.rotation == 0:
            self.tablet_x = TABLET_X
            self.tablet_y = TABLET_Y
        elif self.rotation == 1:
            self.tablet_x = TABLET_Y
            self.tablet_y = TABLET_X
        elif self.rotation == 2:
            self.tablet_x = TABLET_X
            self.tablet_y = TABLET_Y
        elif self.rotation == 3:
            self.tablet_x = TABLET_Y
            self.tablet_y = TABLET_X
        self.update()
        self.update_info()

    def toggle_opacity(self):
        if self.flag_opacity:
            self.setWindowOpacity(DEFAULT_OPACITY)
            self.flag_opacity = False
        else:
            self.setWindowOpacity(1.0)
            self.flag_opacity = True

    def on_tray_icon_activated(self, reason):
        # Left mouse button click
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def hidewindow(self):
        self.last_position = self.pos()
        self.hide()

    def toggle_window(self):
        if self.isVisible():
            self.hidewindow()
        else:
            x = int(self.last_position.x())
            y = int(self.last_position.y())
            # ad-hoc move. Should be like this:
            # self.move(x, y)
            # self.show()
            self.move(x + 1, y)
            self.show()
            self.move(x, y)

    def update_info(self):
        frame = self.frameGeometry()
        x = frame.x()
        y = frame.y()
        window_x = frame.width()
        window_y = frame.height()
        # fmt: off
        cmd = [
            "xinput",
            "set-prop",
            str(ID_DEVICE),
            "Coordinate Transformation Matrix",
            str(window_x / DISPLAY_X), "0", str(x / DISPLAY_X),
            "0", str(window_y / DISPLAY_Y), str(y / DISPLAY_Y),
            "0", "0", "1",
        ]
        # fmt: on
        subprocess.run(cmd)
        if self.tablet_x / self.tablet_y > window_x / window_y:
            delta = (self.tablet_x - self.tablet_y * window_x / window_y) / 2
            x_min, y_min = int(delta), 0
            x_max, y_max = self.tablet_x - int(delta), self.tablet_y
        else:
            delta = (self.tablet_y - self.tablet_x * window_y / window_x) / 2
            x_min, y_min = 0, int(delta)
            x_max, y_max = self.tablet_x, self.tablet_y - int(delta)
        if self.rotation == 0:
            cmd = [
                "xsetwacom",
                "--set",
                str(ID_DEVICE),
                "Area",
                str(x_min),
                str(y_min),
                str(x_max),
                str(y_max),
            ]
        elif self.rotation == 1:
            cmd = [
                "xsetwacom",
                "--set",
                str(ID_DEVICE),
                "Area",
                str(y_min),
                str(x_min),
                str(y_max),
                str(x_max),
            ]
        elif self.rotation == 2:
            cmd = [
                "xsetwacom",
                "--set",
                str(ID_DEVICE),
                "Area",
                str(x_min),
                str(y_min),
                str(x_max),
                str(y_max),
            ]
        elif self.rotation == 3:
            cmd = [
                "xsetwacom",
                "--set",
                str(ID_DEVICE),
                "Area",
                str(y_min),
                str(x_min),
                str(y_max),
                str(x_max),
            ]
        subprocess.run(cmd)
        if self.rotation == 0:
            rotation = "none"
        elif self.rotation == 1:
            rotation = "cw"
        elif self.rotation == 2:
            rotation = "half"
        elif self.rotation == 3:
            rotation = "ccw"
        cmd = ["xsetwacom", "--set", str(ID_DEVICE), "Rotate", rotation]
        subprocess.run(cmd)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
