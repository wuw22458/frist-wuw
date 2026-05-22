"""系统托盘 + 设置面板

设计参考 CodexFocus：毛玻璃卡片 + 发光状态点 + iOS 风格 Toggle 开关。
重构后支持多 Agent 动态注册，UI 由 AdapterRegistry 数据驱动。
"""

import time as _time
from pathlib import Path

from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QApplication, QFrame, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QAction, QRadialGradient, QPen,
    QLinearGradient, QBrush, QFontMetrics,
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF, QSize

from settings import load_config, save_config
from events import AgentEvent, EventType

# ── 色板 ─────────────────────────────────────────────────
BG = QColor(13, 17, 23)
BG_CARD = QColor(22, 27, 34)
BORDER_CARD = QColor(48, 54, 61)
ACCENT = QColor(88, 166, 255)
ACCENT_HOVER = QColor(121, 192, 255)
GREEN = QColor(63, 185, 80)
ORANGE = QColor(210, 153, 34)
RED = QColor(248, 81, 73)
T1 = "#f0f3f6"
T2 = "#b0b8c4"
T3 = "#6e7681"
FONT = '"Microsoft YaHei UI", "Segoe UI", sans-serif'
MONO = '"Cascadia Code", "Consolas", monospace'

# 事件类型 → 状态颜色
_EVENT_COLORS = {
    EventType.WAITING: ORANGE,
    EventType.COMPLETED: GREEN,
    EventType.ERROR: RED,
    EventType.INFO: ACCENT,
}

# 事件类型 → 标题
_EVENT_TITLES = {
    EventType.WAITING: "需要确认",
    EventType.COMPLETED: "任务完成",
    EventType.ERROR: "出错了",
    EventType.INFO: "通知",
}

# 事件类型 → 标签
_EVENT_TAGS = {
    EventType.WAITING: "确认",
    EventType.COMPLETED: "完成",
    EventType.ERROR: "错误",
    EventType.INFO: "信息",
}

# 事件类型 → 状态文本前缀
_EVENT_STATUS_PREFIX = {
    EventType.WAITING: "等待确认",
    EventType.COMPLETED: "任务完成",
    EventType.ERROR: "出错",
    EventType.INFO: "通知",
}

# ── Toggle 开关组件 ───────────────────────────────────────

class ToggleSwitch(QWidget):
    """iOS 风格滑动开关，替换原生复选框。"""

    toggled = Signal(bool)

    _track_w = 40
    _track_h = 22
    _knob_d = 18
    _gap = 10

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._checked = False
        self._text = text
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._checked = checked
        self.update()

    def _text_width(self) -> int:
        if not self._text:
            return 0
        font = self.font()
        font.setFamilies(["Microsoft YaHei UI", "Segoe UI", "sans-serif"])
        font.setPixelSize(13)
        return QFontMetrics(font).horizontalAdvance(self._text)

    def sizeHint(self):
        return QSize(self._track_w + self._gap + self._text_width() + 4, 36)

    def minimumSizeHint(self):
        return QSize(self._track_w + self._gap + self._text_width() + 4, 36)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        y = (self.height() - self._track_h) / 2

        track = QRectF(0, y, self._track_w, self._track_h)
        track_color = ACCENT if self._checked else QColor(48, 54, 61)
        p.setPen(Qt.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track, self._track_h / 2, self._track_h / 2)

        knob_x = self._track_w - self._knob_d - 2 if self._checked else 2
        knob_y = y + (self._track_h - self._knob_d) / 2
        knob = QRectF(knob_x, knob_y, self._knob_d, self._knob_d)
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(knob)

        if self._text:
            p.setPen(QColor(240, 243, 246))
            font = p.font()
            font.setFamilies(["Microsoft YaHei UI", "Segoe UI", "sans-serif"])
            font.setPixelSize(13)
            p.setFont(font)
            tx = int(self._track_w + self._gap)
            ty = (self.height() + p.fontMetrics().ascent()) // 2 - 1
            p.drawText(tx, ty, self._text)
        p.end()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.update()
            self.toggled.emit(self._checked)


# ── 径向光晕组件 ─────────────────────────────────────────

class GlowBackground(QWidget):
    """渐变背景 + 两个径向光晕椭圆。"""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(13, 18, 26))
        gradient.setColorAt(0.55, QColor(18, 33, 51))
        gradient.setColorAt(1.0, QColor(46, 20, 36))
        p.fillRect(rect, QBrush(gradient))

        glow_blue = QRadialGradient(QPointF(60, 100), 180)
        glow_blue.setColorAt(0.0, QColor(25, 140, 255, 40))
        glow_blue.setColorAt(1.0, QColor(25, 140, 255, 0))
        p.fillRect(rect, QBrush(glow_blue))

        glow_pink = QRadialGradient(QPointF(380, 420), 200)
        glow_pink.setColorAt(0.0, QColor(255, 64, 115, 40))
        glow_pink.setColorAt(1.0, QColor(255, 64, 115, 0))
        p.fillRect(rect, QBrush(glow_pink))

        p.end()


# ── 托盘图标 ──────────────────────────────────────────────

def _make_icon(color: str = "#58a6ff", alert: bool = False) -> QIcon:
    S = 64
    pm = QPixmap(S, S)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    c = QColor(color)

    for i in range(4, 0, -1):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c.red(), c.green(), c.blue(), max(3, 18 - i * 4)))
        p.drawEllipse(i, i, S - 2 * i, S - 2 * i)

    g = QRadialGradient(S / 2, S / 2, S / 2)
    g.setColorAt(0.0, c.lighter(120))
    g.setColorAt(0.7, c)
    g.setColorAt(1.0, c.darker(160))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawEllipse(14, 14, S - 28, S - 28)

    p.setBrush(QColor(255, 255, 255, 35))
    p.drawEllipse(22, 18, 10, 7)

    if alert:
        p.setBrush(QColor(RED))
        p.setPen(QPen(QColor(BG), 2))
        p.drawEllipse(S - 20, 2, 16, 16)

    p.end()
    return QIcon(pm)


# ── 毛玻璃卡片 ────────────────────────────────────────────

_GLASS_CARD_STYLE = f"""
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
"""


class SectionCard(QFrame):
    """毛玻璃风格分组卡片。"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            SectionCard {{
                {_GLASS_CARD_STYLE}
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(12)

        self._title = QLabel(title)
        self._title.setStyleSheet(
            f"color: rgba(255,255,255,0.70); font-size: 12px; "
            f"font-weight: 700; letter-spacing: 1px; border: none;"
        )
        self._layout.addWidget(self._title)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)


# ── 状态指示器 ────────────────────────────────────────────

class StatusIndicator(QWidget):
    """两行状态指示器：上行=圆点+状态+事件计数，下行=运行时长。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(16)
        self._dot.setAlignment(Qt.AlignCenter)
        self._dot.setStyleSheet("font-size: 14px; border: none; background: transparent;")
        row1.addWidget(self._dot)

        self._text = QLabel("监控中")
        self._text.setStyleSheet(
            f"color: {T1}; font-size: 13px; font-weight: 600;"
            f" border: none; background: transparent;"
        )
        row1.addWidget(self._text)
        row1.addStretch()

        self._count = QLabel("")
        self._count.setStyleSheet(
            f"color: {T3}; font-size: 11px; font-family: {MONO};"
            f" border: none; background: transparent;"
        )
        row1.addWidget(self._count)
        root.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedWidth(22)
        spacer.setStyleSheet("background: transparent;")
        row2.addWidget(spacer)

        self._runtime = QLabel("已运行 0 分钟")
        self._runtime.setStyleSheet(
            f"color: {T3}; font-size: 10px; font-family: {MONO};"
            f" border: none; background: transparent;"
        )
        row2.addWidget(self._runtime)
        row2.addStretch()
        root.addLayout(row2)

        self._start_time = _time.time()
        self.set_status("监控中", GREEN)

    def set_status(self, text: str, color: QColor = None):
        if color is None:
            color = GREEN
        self._dot.setStyleSheet(
            f"color: {color.name()}; font-size: 14px;"
            f" border: none; background: transparent;"
        )
        self._text.setText(text)

    def set_count(self, count: int):
        if count > 0:
            self._count.setText(f"捕获 {count} 个事件")
        else:
            self._count.setText("")

    def update_runtime(self):
        elapsed = int(_time.time() - self._start_time)
        if elapsed < 60:
            self._runtime.setText(f"已运行 {elapsed} 秒")
        else:
            mins = elapsed // 60
            self._runtime.setText(f"已运行 {mins} 分钟")


# ── 阴影效果辅助 ──────────────────────────────────────────

def _shadow(widget, color=QColor(0, 0, 0, 60), radius=12, offset_y=2):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setColor(color)
    effect.setBlurRadius(radius)
    effect.setOffset(0, offset_y)
    widget.setGraphicsEffect(effect)


# ── 设置面板 ──────────────────────────────────────────────

class SettingsWindow(QWidget):
    config_changed = Signal()
    pause_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agent Notify")
        self.setMinimumSize(470, 560)
        self.resize(500, 700)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        self.setWindowIcon(_make_icon())
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._config = load_config()
        self._is_paused = False
        self._history: list[dict] = []

        # adapter 显示名映射（由 TrayApp 通过 set_adapter_info 注入）
        self._adapter_display_names: dict[str, str] = {}

        # ── 根布局 ──
        self._glow = GlowBackground(self)
        self._glow.setGeometry(0, 0, self.width(), self.height())

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── 标题区 ──
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        icon_label = QLabel("◆")
        icon_label.setStyleSheet("color: #58a6ff; font-size: 18px; border: none;")
        title_row.addWidget(icon_label)

        title = QLabel("Agent Notify")
        title.setStyleSheet(f"color: {T1}; font-size: 18px; font-weight: 700; border: none;")
        title_row.addWidget(title)
        title_row.addStretch()
        root.addLayout(title_row)

        desc = QLabel("当 AI agent 需要确认或任务完成时通知你")
        desc.setStyleSheet(f"color: rgba(255,255,255,0.50); font-size: 12px; border: none;")
        desc.setWordWrap(True)
        root.addWidget(desc)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08); border: none;")
        root.addWidget(sep)

        # ── 状态卡片 ──
        status_card = QFrame()
        status_card.setAttribute(Qt.WA_StyledBackground, True)
        status_card.setStyleSheet(f"QFrame {{ {_GLASS_CARD_STYLE} }}")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(8)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self._status = StatusIndicator()
        status_row.addWidget(self._status)
        status_row.addStretch()

        self._pause_btn = QPushButton("暂停")
        self._pause_btn.setFixedSize(90, 36)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.clicked.connect(self.toggle_pause)
        self._pause_btn.setStyleSheet(self._btn_primary())
        _shadow(self._pause_btn)
        self._pause_btn.setToolTip("暂停或恢复监控")
        status_row.addWidget(self._pause_btn)
        status_layout.addLayout(status_row)

        self._runtime_timer = QTimer(self)
        self._runtime_timer.timeout.connect(self._status.update_runtime)
        self._runtime_timer.start(30000)

        root.addWidget(status_card)

        # ── 监控来源卡片（动态生成，由 adapter 注册表驱动）──
        self._sources_card = SectionCard("监控来源")
        self._source_switches: dict[str, ToggleSwitch] = {}
        # source switches 会在 set_adapter_info 中动态创建
        root.addWidget(self._sources_card)

        # ── 通知选项卡片 ──
        notif_card = SectionCard("通知")

        check_row = QHBoxLayout()
        check_row.setSpacing(20)

        self._sound_sw = self._make_toggle("播放提示音")
        self._sound_sw.setChecked(self._config.get("sound_enabled", True))
        self._sound_sw.toggled.connect(self._on_sound_toggled)
        self._sound_sw.setToolTip("收到通知时播放提示音")
        check_row.addWidget(self._sound_sw)

        self._toast_sw = self._make_toggle("显示系统通知")
        self._toast_sw.setChecked(self._config.get("toast_enabled", True))
        self._toast_sw.toggled.connect(self._save)
        self._toast_sw.setToolTip("收到通知时弹出 Windows Toast")
        check_row.addWidget(self._toast_sw)

        notif_card.add_layout(check_row)

        # 提示音路径行
        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self._sound_icon = QLabel("♪")
        self._sound_icon.setFixedWidth(16)
        self._sound_icon.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 12px; border: none;")

        self._sound_label = QLabel(self._sound_display_path())
        self._sound_label.setStyleSheet(
            f"color: rgba(255,255,255,0.38); font-size: 10px; "
            f"font-family: {MONO}; border: none;"
        )
        self._sound_label.setToolTip(self._sound_full_path())
        path_row.addWidget(self._sound_icon)
        path_row.addWidget(self._sound_label)
        path_row.addStretch()
        notif_card.add_layout(path_row)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._sound_btn = QPushButton("更换")
        self._sound_btn.setFixedHeight(30)
        self._sound_btn.setCursor(Qt.PointingHandCursor)
        self._sound_btn.clicked.connect(self._pick_sound)
        self._sound_btn.setStyleSheet(self._btn_ghost())
        self._sound_btn.setToolTip("选择自定义提示音文件")
        btn_row.addWidget(self._sound_btn)

        self._reset_btn = QPushButton("恢复默认")
        self._reset_btn.setFixedHeight(30)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset_sound)
        self._reset_btn.setStyleSheet(self._btn_ghost())
        self._reset_btn.setVisible(bool(self._config.get("custom_sound")))
        self._reset_btn.setToolTip("恢复为内置默认提示音")
        btn_row.addWidget(self._reset_btn)

        self._preview_btn = QPushButton("试听")
        self._preview_btn.setFixedHeight(30)
        self._preview_btn.setCursor(Qt.PointingHandCursor)
        self._preview_btn.clicked.connect(self._preview_sound)
        self._preview_btn.setStyleSheet(self._btn_ghost())
        self._preview_btn.setToolTip("试听当前提示音")
        btn_row.addWidget(self._preview_btn)

        btn_row.addStretch()

        self._test_btn = QPushButton("测试通知")
        self._test_btn.setFixedHeight(30)
        self._test_btn.setCursor(Qt.PointingHandCursor)
        self._test_btn.clicked.connect(self._send_test_notification)
        self._test_btn.setStyleSheet(self._btn_ghost())
        self._test_btn.setToolTip("立即发送一条测试通知")
        btn_row.addWidget(self._test_btn)

        notif_card.add_layout(btn_row)

        self._update_sound_controls(self._sound_sw.isChecked())
        root.addWidget(notif_card)

        # ── 最近通知卡片 ──
        history_card = SectionCard("最近通知")
        history_card.setMinimumHeight(100)

        self._history_list = QListWidget()
        self._history_list.setStyleSheet(f"""
            QListWidget {{
                background: rgba(0,0,0,0.20);
                border: none;
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                color: rgba(255,255,255,0.65);
                font-size: 11px;
                padding: 5px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
            QListWidget::item:last {{
                border-bottom: none;
            }}
        """)
        self._history_list.setMaximumHeight(160)
        self._history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._history_list.setToolTip("最近收到的通知记录")

        history_card.add_widget(self._history_list)

        self._empty_label = QLabel("暂无通知")
        self._empty_label.setStyleSheet(
            "color: rgba(255,255,255,0.25); font-size: 12px; border: none;"
        )
        self._empty_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        history_card.add_widget(self._empty_label)

        root.addWidget(history_card, stretch=1)
        self._refresh_history()

    # ── Adapter 信息注入 ────────────────────────────────────

    def set_adapter_info(self, adapters: list) -> None:
        """由 TrayApp 调用，注入 adapter 信息并动态创建 source switches。"""
        self._adapter_display_names = {a.agent_id: a.display_name for a in adapters}

        # 清除旧的 source switches
        for sw in self._source_switches.values():
            sw.setParent(None)
            sw.deleteLater()
        self._source_switches.clear()

        # 动态创建
        for adapter in adapters:
            key = f"source_{adapter.agent_id}"
            sw = self._make_toggle(adapter.display_name)
            sw.setChecked(self._config.get(key, True))
            sw.toggled.connect(self._save)
            sw.setToolTip(adapter.description)
            self._source_switches[key] = sw
            self._sources_card.add_widget(sw)

    # ── 控件工厂 ──────────────────────────────────────────

    def _make_toggle(self, text: str) -> ToggleSwitch:
        return ToggleSwitch(text, self)

    def _btn_primary(self) -> str:
        return f"""
            QPushButton {{
                background: #1e6ff0;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
                font-family: {FONT};
            }}
            QPushButton:hover {{ background: #3892ff; }}
            QPushButton:pressed {{ background: #1a5fcc; }}
        """

    def _btn_ghost(self) -> str:
        return f"""
            QPushButton {{
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.75);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 15px;
                padding: 5px 16px;
                font-size: 12px;
                font-family: {FONT};
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.14);
                border-color: rgba(255,255,255,0.28);
                color: white;
            }}
            QPushButton:disabled {{
                background: rgba(255,255,255,0.04);
                color: rgba(255,255,255,0.22);
                border-color: rgba(255,255,255,0.06);
            }}
        """

    def _btn_danger(self) -> str:
        return f"""
            QPushButton {{
                background: rgba(248,81,73,0.18);
                color: #f85149;
                border: 1px solid rgba(248,81,73,0.35);
                border-radius: 18px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
                font-family: {FONT};
            }}
            QPushButton:hover {{ background: rgba(248,81,73,0.30); }}
        """

    # ── 公开方法 ──────────────────────────────────────────

    def set_status(self, text: str, color: QColor = None):
        self._status.set_status(text, color)

    def set_notif_count(self, count: int):
        self._status.set_count(count)

    def show_last_notification(self, event: AgentEvent):
        """从 AgentEvent 添加历史记录。"""
        self._history.append({
            "time": _time.strftime("%H:%M:%S"),
            "event_type": event.event_type,
            "message": event.message,
            "agent_id": event.agent_id,
        })
        max_history = self._config.get("max_history", 200)
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]
        self._refresh_history()

    # ── 内部方法 ──────────────────────────────────────────

    def _refresh_history(self):
        self._history_list.clear()
        if not self._history:
            self._history_list.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._history_list.show()

        for entry in reversed(self._history):
            agent_id = entry.get("agent_id", "")
            source_display = self._adapter_display_names.get(agent_id, agent_id or "?")

            event_type = entry.get("event_type", "info")
            event_tag = _EVENT_TAGS.get(event_type, "信息")
            text = f"{entry['time']}  [{event_tag}]  {entry['message']}"
            item = QListWidgetItem(text)
            item.setToolTip(f"来源: {source_display}")
            self._history_list.addItem(item)

        self._history_list.scrollToBottom()

    def _sound_display_path(self) -> str:
        custom = self._config.get("custom_sound", "")
        if custom:
            name = Path(custom).name
        else:
            from notification import _default_sound
            d = _default_sound()
            name = d.name if d else "—"
        return f"提示音: {name}"

    def _sound_full_path(self) -> str:
        custom = self._config.get("custom_sound", "")
        if custom:
            return custom
        from notification import _default_sound
        d = _default_sound()
        return str(d) if d else ""

    def _update_sound_controls(self, enabled: bool):
        self._sound_btn.setEnabled(enabled)
        self._reset_btn.setEnabled(enabled)
        self._preview_btn.setEnabled(enabled)
        self._sound_icon.setVisible(enabled)
        self._sound_label.setVisible(enabled)

    def _on_sound_toggled(self, checked: bool):
        self._update_sound_controls(checked)
        self._save()

    def _pick_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择提示音", "",
            "音频文件 (*.wav *.mp3);;WAV 文件 (*.wav);;MP3 文件 (*.mp3);;所有文件 (*)"
        )
        if path:
            self._config["custom_sound"] = path
            save_config(self._config)
            self.config_changed.emit()
            self._sound_label.setText(self._sound_display_path())
            self._sound_label.setToolTip(path)
            self._reset_btn.setVisible(True)

    def _reset_sound(self):
        self._config.pop("custom_sound", None)
        save_config(self._config)
        self.config_changed.emit()
        self._sound_label.setText(self._sound_display_path())
        self._sound_label.setToolTip(self._sound_full_path())
        self._reset_btn.setVisible(False)

    def _preview_sound(self):
        from notification import play_sound
        play_sound(self._config.get("custom_sound", ""))

    def _send_test_notification(self):
        test_msg = "这是一条测试通知，设置已生效"
        test_event = AgentEvent(
            agent_id="test",
            event_type=EventType.INFO,
            message=test_msg,
        )
        self.show_last_notification(test_event)
        if self._toast_sw.isChecked():
            notify(
                "Agent Notify 测试", test_msg,
                sound=self._sound_sw.isChecked(),
                source="test",
                sound_path=self._config.get("custom_sound", ""),
            )

    def toggle_pause(self):
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.setText("继续")
            self._pause_btn.setStyleSheet(self._btn_danger())
            self.set_status("已暂停", ORANGE)
        else:
            self._pause_btn.setText("暂停")
            self._pause_btn.setStyleSheet(self._btn_primary())
            self.set_status("监控中", GREEN)
        self.pause_toggled.emit(self._is_paused)

    def _save(self):
        self._config["sound_enabled"] = self._sound_sw.isChecked()
        self._config["toast_enabled"] = self._toast_sw.isChecked()
        for key, sw in self._source_switches.items():
            self._config[key] = sw.isChecked()
        save_config(self._config)
        self.config_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._glow.setGeometry(0, 0, self.width(), self.height())

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    @property
    def is_paused(self) -> bool:
        return self._is_paused


# ── 托盘应用 ──────────────────────────────────────────────

class TrayApp(QSystemTrayIcon):

    pause_toggled = Signal(bool)

    def __init__(self, event_bus=None, parent=None):
        super().__init__(parent)
        self._bus = event_bus
        self._config = load_config()
        self._settings = SettingsWindow()
        self._settings.config_changed.connect(self._reload_config)
        self._settings.pause_toggled.connect(self._on_pause_toggled)
        self._pulse_on = False
        self._paused = False
        self._notif_count = 0

        # 注入 adapter 信息到 SettingsWindow（延迟到 main.py 中 adapters 创建后）
        self._adapters = []

        self.setIcon(_make_icon())
        self.setToolTip("Agent Notify")

        self._pt = QTimer(self)
        self._pt.timeout.connect(self._pulse)

        self._pulse_stop_timer = QTimer(self)
        self._pulse_stop_timer.setSingleShot(True)
        self._pulse_stop_timer.timeout.connect(self._pulse_stop)

        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background: #161b22;
                color: {T1};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                font-size: 12px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: rgba(88,166,255,0.20);
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: rgba(255,255,255,0.08);
                margin: 3px 8px;
            }}
        """)

        a1 = QAction("设置...", menu)
        a1.triggered.connect(self._show_settings)
        menu.addAction(a1)
        menu.addSeparator()

        self._pause_act = QAction("暂停", menu)
        self._pause_act.triggered.connect(self.toggle_pause_from_menu)
        menu.addAction(self._pause_act)
        menu.addSeparator()

        q = QAction("退出", menu)
        q.triggered.connect(QApplication.quit)
        menu.addAction(q)

        self.setContextMenu(menu)
        self.activated.connect(self._click)

        # 连接 EventBus
        if self._bus:
            self._bus.event_received.connect(self.handle_event)

    def set_adapters(self, adapters: list) -> None:
        """注入 adapter 列表，用于 SettingsWindow 动态生成 source switches。"""
        self._adapters = adapters
        self._settings.set_adapter_info(adapters)

    def _reload_config(self):
        self._config = load_config()

    def _on_pause_toggled(self, is_paused: bool):
        self._paused = is_paused
        if is_paused:
            self._pause_act.setText("继续")
            self.setIcon(_make_icon("#d29922"))
            self.setToolTip("Agent Notify — 已暂停")
            self._pt.stop()
        else:
            self._pause_act.setText("暂停")
            self.setIcon(_make_icon())
            self.setToolTip("Agent Notify")
        self.pause_toggled.emit(is_paused)

    def _click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._show_settings()

    def _show_settings(self):
        if self._settings.isVisible():
            self._settings.raise_()
            self._settings.activateWindow()
        else:
            self._settings.show()

    def toggle_pause_from_menu(self):
        self._settings.toggle_pause()

    def _pulse(self):
        self._pulse_on = not self._pulse_on
        self.setIcon(_make_icon("#58a6ff", self._pulse_on))

    def _pulse_stop(self):
        self._pt.stop()
        self._pulse_stop_timer.stop()
        self.setIcon(_make_icon())
        self._notif_count = 0

    def handle_event(self, event: AgentEvent):
        """处理来自 EventBus 的 AgentEvent（替代原 handle_signal）。"""
        if self._paused:
            return

        self._notif_count += 1
        self._settings.set_notif_count(self._notif_count)

        # 状态文本
        prefix = _EVENT_STATUS_PREFIX.get(event.event_type, "通知")
        color = _EVENT_COLORS.get(event.event_type, ACCENT)
        self._settings.set_status(f"{prefix} — {event.message}", color)

        # 历史记录
        self._settings.show_last_notification(event)

        # 脉冲动画
        self._pt.start(350)
        self._pulse_stop_timer.start(3500)

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def panel(self):
        return self._settings
