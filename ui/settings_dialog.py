from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QComboBox,
)

from config import load_config, save_config


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(460, 340)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
            }
            QLabel {
                color: #1A1A1A;
            }
            QComboBox {
                background: #F5F5F7;
                border: 1px solid #DDD;
                border-radius: 6px;
                padding: 6px 12px;
                color: #1A1A1A;
                min-width: 110px;
            }
            QComboBox:hover {
                border: 1px solid #BBB;
            }
            QComboBox:drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                border: 1px solid #DDD;
                border-radius: 4px;
                color: #1A1A1A;
                selection-background-color: #E8F0FA;
                selection-color: #1A1A1A;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 28px;
            }
        """)

        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        title = QLabel("设置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #1A1A1A;")
        layout.addWidget(title)
        layout.addSpacing(4)

        label_width = 170

        # 存储期限
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        lbl1 = QLabel("存储期限")
        lbl1.setFixedWidth(label_width)
        row1.addWidget(lbl1)
        self.retention_combo = QComboBox()
        self.retention_combo.addItems(["1 天", "3 天", "5 天", "7 天", "30 天"])
        self.retention_combo.setCurrentIndex(1)
        row1.addWidget(self.retention_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 最大条数
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        lbl2 = QLabel("最大条数")
        lbl2.setFixedWidth(label_width)
        row2.addWidget(lbl2)
        self.max_combo = QComboBox()
        self.max_combo.addItems(["100", "300", "500", "1000"])
        self.max_combo.setCurrentIndex(2)
        row2.addWidget(self.max_combo)
        row2.addStretch()
        layout.addLayout(row2)

        # 自动粘贴
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        lbl3 = QLabel("点击卡片后自动粘贴")
        lbl3.setFixedWidth(label_width)
        row3.addWidget(lbl3)
        self.auto_paste_combo = QComboBox()
        self.auto_paste_combo.addItems(["开启", "关闭"])
        self.auto_paste_combo.setCurrentIndex(0)
        row3.addWidget(self.auto_paste_combo)
        row3.addStretch()
        layout.addLayout(row3)

        layout.addStretch()

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(self._btn_style("#F0F0F0", "#1A1A1A"))
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setFixedSize(88, 36)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(self._btn_style("#4A90D9", "#FFFFFF"))
        save_btn.clicked.connect(self._save)
        save_btn.setFixedSize(88, 36)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _btn_style(self, bg, color):
        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def _load_current(self):
        cfg = load_config()
        days = cfg.get("retention_days", 3)
        idx = {1: 0, 3: 1, 5: 2, 7: 3, 30: 4}.get(days, 1)
        self.retention_combo.setCurrentIndex(idx)

        max_items = cfg.get("max_items", 500)
        idx2 = {100: 0, 300: 1, 500: 2, 1000: 3}.get(max_items, 2)
        self.max_combo.setCurrentIndex(idx2)

        auto = cfg.get("auto_paste", True)
        self.auto_paste_combo.setCurrentIndex(0 if auto else 1)

    def _save(self):
        days_map = {0: 1, 1: 3, 2: 5, 3: 7, 4: 30}
        max_map = {0: 100, 1: 300, 2: 500, 3: 1000}

        cfg = load_config()
        cfg["retention_days"] = days_map[self.retention_combo.currentIndex()]
        cfg["max_items"] = max_map[self.max_combo.currentIndex()]
        cfg["auto_paste"] = self.auto_paste_combo.currentIndex() == 0
        save_config(cfg)
        self.accept()
