import hashlib
import os
import time

from PySide6.QtCore import QBuffer, QIODevice, QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from config import get_app_dir, load_config
from storage import add_item


class ClipboardMonitor(QObject):
    content_recorded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_text_hash = ""
        self._last_image_hash = ""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_clipboard)
        self._prev_text = ""
        self._prev_image_data = None

    def start(self):
        cfg = load_config()
        interval = cfg.get("poll_interval_ms", 500)
        self._timer.start(interval)
        self._check_clipboard()

    def stop(self):
        self._timer.stop()

    def _check_clipboard(self):
        app = QApplication.instance()
        if not app:
            return
        clipboard = app.clipboard()

        # 检查图片
        image = clipboard.image()
        if not image.isNull():
            image_bytes = self._image_to_bytes(image)
            if image_bytes:
                h = hashlib.md5(image_bytes).hexdigest()
                if h != self._last_image_hash:
                    self._last_image_hash = h
                    self._save_image(image)
            return

        # 检查文字
        text = clipboard.text()
        if text and text != self._prev_text:
            self._prev_text = text
            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            if h != self._last_text_hash:
                self._last_text_hash = h
                self._record_text(text)

    def _record_text(self, text):
        cfg = load_config()
        max_len = cfg.get("max_text_length", 5000)
        if len(text) > max_len:
            text_preview = text[:max_len] + "..."
        else:
            text_preview = text
        add_item("text", content=text_preview)
        self.content_recorded.emit()

    def _image_to_bytes(self, image):
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        return bytes(buffer.data())

    def _save_image(self, image):
        images_dir = os.path.join(get_app_dir(), "images")
        ts = int(time.time() * 1000)
        filename = f"clip_{ts}.png"
        filepath = os.path.join(images_dir, filename)
        image.save(filepath, "PNG")
        add_item("image", image_path=filepath)
        self.content_recorded.emit()
