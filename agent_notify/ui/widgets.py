"""UI 组件 — 色板、自定义控件、托盘图标绘制。

提供 SettingsWindow 和 TrayApp 共享的：
- 色板常量（BG, ACCENT, T1 等）
- 事件类型映射（_EVENT_COLORS, _EVENT_TAGS 等）
- 自定义控件（ToggleSwitch, GlowBackground, SectionCard, StatusIndicator）
- 辅助函数（_make_icon, _shadow）
"""

import time as _time

from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from events import EventType

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
    """iOS 风格滑动开关，带平滑滑动动画和键盘焦点支持。"""

    toggled = Signal(bool)

    _TRACK_WIDTH = 40
    _TRACK_HEIGHT = 22
    _THUMB_DIAMETER = 18
    _MARGIN = 2
    _GAP = 10

    def __init__(
        self,
        text: str = "",
        parent=None,
        checked=False,
        on_color=ACCENT,
        off_color="#30363D",
    ):
        super().__init__(parent)
        self._checked = checked
        self._text = text
        self._thumb_pos = self._calc_thumb_pos()
        self._on_color = QColor(on_color) if isinstance(on_color, str) else on_color
        self._off_color = QColor(off_color) if isinstance(off_color, str) else off_color
        self._thumb_color = QColor("#FFFFFF")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.StrongFocus)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_tick)
        self._anim.finished.connect(self._on_anim_done)

    def _calc_thumb_pos(self):
        if self._checked:
            return self._TRACK_WIDTH - self._THUMB_DIAMETER - self._MARGIN
        return self._MARGIN

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val):
        if val == self._checked:
            return
        self._checked = val
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(self._calc_thumb_pos())
        self._anim.start()
        self.toggled.emit(val)

    def _on_anim_tick(self, value):
        self._thumb_pos = value
        self.update()

    def _on_anim_done(self):
        self.update()

    def _text_width(self) -> int:
        if not self._text:
            return 0
        font = self.font()
        font.setFamilies(["Microsoft YaHei UI", "Segoe UI", "sans-serif"])
        font.setPixelSize(13)
        return QFontMetrics(font).horizontalAdvance(self._text)

    def sizeHint(self):
        return QSize(self._TRACK_WIDTH + self._GAP + self._text_width() + 4, 36)

    def minimumSizeHint(self):
        return QSize(self._TRACK_WIDTH + self._GAP + self._text_width() + 4, 36)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        y = (self.height() - self._TRACK_HEIGHT) / 2

        # Track
        track_rect = QRectF(0, y, self._TRACK_WIDTH, self._TRACK_HEIGHT)
        track_color = self._on_color if self._checked else self._off_color
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(track_rect, self._TRACK_HEIGHT / 2, self._TRACK_HEIGHT / 2)

        # Thumb
        thumb_y = y + (self._TRACK_HEIGHT - self._THUMB_DIAMETER) / 2
        p.setBrush(QBrush(self._thumb_color))
        td = self._THUMB_DIAMETER
        p.drawEllipse(QRectF(self._thumb_pos, thumb_y, td, td))

        if self._text:
            p.setPen(QColor(240, 243, 246))
            font = p.font()
            font.setFamilies(["Microsoft YaHei UI", "Segoe UI", "sans-serif"])
            font.setPixelSize(13)
            p.setFont(font)
            tx = int(self._TRACK_WIDTH + self._GAP)
            ty = (self.height() + p.fontMetrics().ascent()) // 2 - 1
            p.drawText(tx, ty, self._text)
        p.end()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)


# ── 径向光晕组件 ─────────────────────────────────────────


class GlowBackground(QWidget):
    """渐变背景 + 两个径向光晕椭圆。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(13, 18, 26))
        gradient.setColorAt(0.55, QColor(18, 33, 51))
        gradient.setColorAt(1.0, QColor(46, 20, 36))
        p.fillRect(rect, QBrush(gradient))

        glow_blue = QRadialGradient(QPointF(w * 0.12, h * 0.18), max(w, h) * 0.32)
        glow_blue.setColorAt(0.0, QColor(25, 140, 255, 40))
        glow_blue.setColorAt(1.0, QColor(25, 140, 255, 0))
        p.fillRect(rect, QBrush(glow_blue))

        glow_pink = QRadialGradient(QPointF(w * 0.76, h * 0.75), max(w, h) * 0.36)
        glow_pink.setColorAt(0.0, QColor(255, 64, 115, 40))
        glow_pink.setColorAt(1.0, QColor(255, 64, 115, 0))
        p.fillRect(rect, QBrush(glow_pink))

        p.end()


# ── 托盘图标 ──────────────────────────────────────────────

_ICON_CACHE: dict[tuple, QPixmap] = {}


def _make_icon(color: str = "#58a6ff", alert: bool = False) -> QIcon:
    cache_key = (alert,)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key].copy()
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
    _ICON_CACHE[cache_key] = pm
    return QIcon(pm)


# ── 毛玻璃卡片 ────────────────────────────────────────────

GLASS_BG = "rgba(255, 255, 255, 0.06)"
GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
GLASS_HOVER = "rgba(255, 255, 255, 0.10)"

_GLASS_CARD_STYLE = f"""
    background: {GLASS_BG};
    border: 1px solid {GLASS_BORDER};
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
            "color: rgba(255,255,255,0.70); font-size: 12px; "
            "font-weight: 700; letter-spacing: 1px; border: none;"
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
        self._dot.setStyleSheet(
            "font-size: 14px; border: none; background: transparent;"
        )
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


# ── 通用横幅组件 ──────────────────────────────────────────


class BannerWidget(QFrame):
    """通用信息横幅，支持 info/warning/error 三种样式。"""

    closed = Signal()
    action_clicked = Signal()

    _STYLES = {
        "info": ("#1A3A5C", "#58A6FF", "#58A6FF"),
        "warning": ("#3D2E00", "#D29922", "#D29922"),
        "error": ("#3D1A1A", "#F85149", "#F85149"),
    }

    def __init__(self, text="", action_text="", banner_type="info", parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        bg, border, accent = self._STYLES.get(banner_type, self._STYLES["info"])
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        self._label = QLabel(text)
        self._label.setStyleSheet(f"color: {border}; font-size: 12px; border: none;")
        layout.addWidget(self._label, 1)
        if action_text:
            btn = QPushButton(action_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {accent};
                    border: 1px solid {accent};
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background: {accent}; color: #0D1117; }}
            """)
            btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(btn)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {border};"
            f" border: none; font-size: 14px; }}"
            f"QPushButton:hover {{ color: #F0F3F6; }}"
        )
        close_btn.clicked.connect(self.hide)
        close_btn.clicked.connect(self.closed.emit)
        layout.addWidget(close_btn)

    def set_text(self, text):
        self._label.setText(text)


# ── 阴影效果辅助 ──────────────────────────────────────────

_SHADOW_COLOR = QColor(0, 0, 0, 60)


def _shadow(widget, color=None, radius=12, offset_y=2):
    if color is None:
        color = _SHADOW_COLOR
    effect = QGraphicsDropShadowEffect(widget)
    effect.setColor(color)
    effect.setBlurRadius(radius)
    effect.setOffset(0, offset_y)
    widget.setGraphicsEffect(effect)
