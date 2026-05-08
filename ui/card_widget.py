from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from storage import toggle_pin


STYLE = """
CardWidget {
    background: #F8F8F9;
    border-radius: 10px;
    border: 1px solid #E8E8EA;
    padding: 10px;
}
CardWidget:hover {
    background: #F0F0F2;
    border: 1px solid #D8D8DA;
}
CardWidget[pinned="true"] {
    background: #F0F4FF;
    border: 1px solid #D0D8F0;
}
"""


class CardWidget(QFrame):
    clicked = Signal(int)
    pin_toggled = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, item_id, content_type, content, image_path, created_at, pinned, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.content_type = content_type
        self.content = content
        self.image_path = image_path
        self.pinned = bool(pinned)

        self.setStyleSheet(STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(72)
        self.setProperty("pinned", "true" if self.pinned else "false")

        self._build_ui(created_at)
        self._update_pin_style()

    def _build_ui(self, created_at):
        import datetime
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        dt = datetime.datetime.fromtimestamp(created_at)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #999; font-size: 11px; background: transparent; border: none;")
        time_label.setFixedHeight(16)

        if self.content_type == "image":
            preview = QLabel("[图片]")
            preview.setStyleSheet("color: #4A90D9; font-size: 13px; background: transparent; border: none;")
        else:
            text = self.content or ""
            preview_text = text.replace("\n", " ")[:80]
            if len(text) > 80:
                preview_text += "..."
            preview = QLabel(preview_text)
            preview.setStyleSheet("color: #333; font-size: 13px; background: transparent; border: none;")
            preview.setWordWrap(False)

        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        content_layout.addWidget(time_label)
        content_layout.addWidget(preview)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        pin_btn = QPushButton("📌")
        pin_btn.setFixedSize(28, 28)
        pin_btn.setStyleSheet(self._btn_style(active=self.pinned))
        pin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pin_btn.setToolTip("取消置顶" if self.pinned else "置顶")
        pin_btn.clicked.connect(self._on_pin)
        self.pin_btn = pin_btn

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet(self._btn_style())
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("删除")
        del_btn.clicked.connect(self._on_delete)

        btn_layout.addWidget(pin_btn)
        btn_layout.addWidget(del_btn)

        layout.addLayout(content_layout)
        layout.addLayout(btn_layout)

    def _btn_style(self, active=False):
        color = "#4A90D9" if active else "#BBB"
        bg = "#E8F0FA" if active else "transparent"
        return f"""
            QPushButton {{
                background: {bg}; border: none; border-radius: 6px;
                color: {color}; font-size: 13px;
            }}
            QPushButton:hover {{ background: #E0E0E0; }}
        """

    def _on_pin(self):
        toggle_pin(self.item_id)
        self.pinned = not self.pinned
        self.setProperty("pinned", "true" if self.pinned else "false")
        self._update_pin_style()
        self.pin_toggled.emit(self.item_id)

    def _on_delete(self):
        self.delete_requested.emit(self.item_id)

    def _update_pin_style(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.x() < self.width() - 70:
                self.clicked.emit(self.item_id)
        super().mousePressEvent(event)
