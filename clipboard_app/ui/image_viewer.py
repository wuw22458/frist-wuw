from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout


class ImageViewer(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片预览")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background: #FFFFFF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            screen = QApplication.primaryScreen()
            if screen:
                sw = screen.size().width()
                sh = screen.size().height()
            else:
                sw, sh = 1200, 800
            max_w = int(sw * 0.7)
            max_h = int(sh * 0.7)
            if pixmap.width() > max_w or pixmap.height() > max_h:
                pixmap = pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
