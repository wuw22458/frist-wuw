"""Startup splash screen with logo animation."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QSplashScreen, QVBoxLayout, QWidget


class AnimatedSplash(QWidget):
    """Frameless splash screen with fade-in logo and version text."""

    def __init__(self, version: str = '0.1.0'):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 200)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Logo
        self._logo = QLabel('\u25c6')
        self._logo.setAlignment(Qt.AlignCenter)
        self._logo.setStyleSheet(
            'font-size: 48px; color: #58a6ff; background: transparent;'
        )
        layout.addWidget(self._logo)

        # App name
        self._name = QLabel('Agent Notify')
        self._name.setAlignment(Qt.AlignCenter)
        self._name.setStyleSheet(
            'color: #e6edf3; font-size: 20px; font-weight: 700;'
            ' background: transparent;'
        )
        layout.addWidget(self._name)

        # Version
        self._ver = QLabel(f'v{version}')
        self._ver.setAlignment(Qt.AlignCenter)
        self._ver.setStyleSheet(
            'color: #8b949e; font-size: 12px; background: transparent;'
        )
        layout.addWidget(self._ver)

        # Fade in
        self.setWindowOpacity(0.0)
        self._fade_in = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade_in.setDuration(400)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutQuart)

    def show_animated(self, auto_close_ms=1500):
        """Show splash with fade-in, auto-close after delay."""
        self.show()
        self._fade_in.start()
        QTimer.singleShot(auto_close_ms, self._close_animated)

    def _close_animated(self):
        """Fade out and close."""
        self._fade_out = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._fade_out.finished.connect(self.close)
        self._fade_out.start()

    def paintEvent(self, event):
        """Draw rounded dark background."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(13, 17, 23, 240))
        p.setPen(QColor(48, 54, 61, 200))
        p.drawRoundedRect(self.rect(), 12, 12)
