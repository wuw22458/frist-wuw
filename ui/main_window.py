from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QPixmap, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

from config import load_config
from storage import get_items, get_item_by_id, delete_item, cleanup_expired
from .card_widget import CardWidget
from .settings_dialog import SettingsDialog


class MainPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板历史")
        self.setMinimumSize(380, 480)
        self.resize(400, 600)
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            #container {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #E0E0E3;
            }
        """)
        self.setCentralWidget(container)

        self._show_grace = False
        self._build_ui(container)
        self._load_items()

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.hide)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._load_items)

        self.installEventFilter(self)

    def _build_ui(self, container):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet("background: #FFFFFF; border-radius: 14px 14px 0px 0px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("剪贴板历史")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A1A;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; border-radius: 6px;
                color: #999; font-size: 16px;
            }
            QPushButton:hover { background: #F0F0F2; color: #333; }
        """)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        header_layout.addWidget(settings_btn)

        # 搜索栏
        search_widget = QWidget()
        search_widget.setStyleSheet("background: #FFFFFF;")
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(14, 0, 14, 10)

        search_box = QWidget()
        search_box.setObjectName("searchBox")
        search_box.setStyleSheet("""
            QWidget#searchBox {
                background: #F5F5F7; border: 1px solid #E8E8EA; border-radius: 8px;
            }
        """)
        search_box_layout = QHBoxLayout(search_box)
        search_box_layout.setContentsMargins(10, 0, 8, 0)
        search_box_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 14px; background: transparent;")
        search_box_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索历史内容...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none; color: #333;
                font-size: 13px; padding: 8px 0;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        search_box_layout.addWidget(self.search_input)

        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(22, 22)
        clear_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #BBB; font-size: 12px; }
            QPushButton:hover { color: #666; }
        """)
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_box_layout.addWidget(clear_btn)
        search_layout.addWidget(search_box)

        # 卡片列表
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: #FFFFFF; }
            QScrollBar:vertical { background: transparent; width: 6px; }
            QScrollBar::handle:vertical { background: #DDD; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: #FFFFFF;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(14, 0, 14, 14)
        self.list_layout.setSpacing(6)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.list_container)

        self.empty_label = QLabel("还没有复制内容\n按 Ctrl+C 复制文字或图片吧")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #BBB; font-size: 14px; padding: 60px 0;")
        self.empty_label.setWordWrap(True)

        # 底部状态栏
        footer = QWidget()
        footer.setFixedHeight(36)
        footer.setStyleSheet("background: #FFFFFF; border-radius: 0 0 14px 14px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)
        self.count_label = QLabel("共 0 条")
        self.count_label.setStyleSheet("color: #999; font-size: 11px;")
        footer_layout.addWidget(self.count_label)

        layout.addWidget(header)
        layout.addWidget(search_widget)
        layout.addWidget(scroll_area, 1)
        layout.addWidget(footer)

    def _load_items(self):
        cleanup_expired()
        text = self.search_input.text().strip()
        items = get_items(search_text=text if text else None)

        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            self.list_layout.addWidget(self.empty_label)
            self.count_label.setText("共 0 条")
            return

        for row in items:
            item_id, content_type, content, image_path, created_at, is_pinned = row
            card = CardWidget(item_id, content_type, content, image_path, created_at, is_pinned)
            card.clicked.connect(self._on_item_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.delete_requested.connect(self._on_delete)
            self.list_layout.addWidget(card)

        self.count_label.setText(f"共 {len(items)} 条")

    def _on_item_clicked(self, item_id):
        row = get_item_by_id(item_id)
        if not row:
            return
        _, content_type, content, image_path, _created_at, _is_pinned = row

        clipboard = QApplication.clipboard()
        if content_type == "text":
            clipboard.setText(content)
        elif content_type == "image" and image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                clipboard.setPixmap(pixmap)

        self.hide()

        cfg = load_config()
        if cfg.get("auto_paste", True):
            QTimer.singleShot(150, self._do_paste)

    def _do_paste(self):
        import pyautogui
        pyautogui.hotkey("ctrl", "v")

    def _on_pin_toggled(self, _item_id):
        self._refresh_timer.start(100)

    def _on_delete(self, item_id):
        delete_item(item_id)
        self._load_items()

    def _on_search(self, _text):
        self._load_items()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            cleanup_expired()
            self._load_items()

    def _focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.WindowDeactivate and not self._show_grace:
            QTimer.singleShot(100, self._check_hide)
        return super().eventFilter(obj, event)

    def _check_hide(self):
        if not self.isActiveWindow() and not self.search_input.hasFocus():
            self.hide()

    def show_at_cursor(self):
        self._show_grace = True
        self._load_items()
        self.search_input.clear()

        pos = QCursor.pos()
        sw = self.screen().availableGeometry()
        x = pos.x()
        y = pos.y()
        if x + self.width() > sw.right():
            x = sw.right() - self.width()
        if y + self.height() > sw.bottom():
            y = sw.bottom() - self.height()
        if x < sw.left():
            x = sw.left()
        if y < sw.top():
            y = sw.top()
        self.move(x, y)
        self.show()
        self.activateWindow()
        self.search_input.setFocus()
        QTimer.singleShot(500, lambda: setattr(self, "_show_grace", False))
