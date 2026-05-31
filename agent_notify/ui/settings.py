"""设置面板 — SettingsWindow。"""

import json
import time as _time
from pathlib import Path

from constants import HISTORY_FILE, __version__
from log import get_logger

logger = get_logger("settings")
from events import AgentEvent, EventType
from PySide6.QtCore import (
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRegularExpression,
    QSettings,
    QSize,
    Qt,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import QColor, QDesktopServices, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from settings import load_config, save_config

from ui.widgets import (
    _EVENT_TAGS,
    _GLASS_CARD_STYLE,
    ACCENT,
    FONT,
    GREEN,
    MONO,
    ORANGE,
    T1,
    T2,
    T3,
    BannerWidget,
    GlowBackground,
    SectionCard,
    StatusIndicator,
    ToggleSwitch,
    _make_icon,
    _shadow,
)
from ui.style import SCROLLBAR_STYLE


def _relative_time(ts: float) -> str:
    """Convert timestamp to relative time string."""
    import time as _t
    diff = int(_t.time() - ts)
    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        return f"{diff // 60} 分钟前"
    elif diff < 86400:
        return f"{diff // 3600} 小时前"
    else:
        return f"{diff // 86400} 天前"


class SettingsWindow(QWidget):
    config_changed = Signal()
    pause_toggled = Signal(bool)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agent Notify")
        self.setMinimumSize(470, 560)
        self.resize(500, 700)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        self.setWindowIcon(_make_icon())
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._config = config if config is not None else load_config()
        self._is_paused = False
        self._history: list[dict] = self._load_history()
        self._animatable_cards: list[QWidget] = []
        self._animations_played = False
        self._hero_start_time = _time.time()
        self._last_notif_summary = "等待来自 AI agent 的通知..."

        # adapter 显示名映射（由 TrayApp 通过 set_adapter_info 注入）
        self._adapter_display_names: dict[str, str] = {}

        # ── 根布局 ──
        self._glow = GlowBackground(self)
        self._glow.setGeometry(0, 0, self.width(), self.height())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        scroll = self._scroll
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            + SCROLLBAR_STYLE
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── 标题区 ──
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        icon_label = QLabel("◆")
        icon_label.setStyleSheet("color: #58a6ff; font-size: 18px; border: none;")
        title_row.addWidget(icon_label)

        title = QLabel(f"Agent Notify v{__version__}")
        title.setStyleSheet(
            f"color: {T1}; font-size: 18px; font-weight: 700; border: none;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        root.addLayout(title_row)

        desc = QLabel("当 AI agent 需要确认或任务完成时通知你")
        desc.setStyleSheet(
            "color: rgba(255,255,255,0.50); font-size: 12px; border: none;"
        )
        desc.setWordWrap(True)
        root.addWidget(desc)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08); border: none;")
        root.addWidget(sep)

        # ── 更新提示横幅（默认隐藏）──
        self._update_bar = BannerWidget("", action_text="下载更新", banner_type="info")
        self._update_bar.setVisible(False)
        self._update_bar.action_clicked.connect(self._open_download)
        self._update_url = ""
        root.addWidget(self._update_bar)

        # ── 崩溃提示横幅（默认隐藏）──
        self._crash_bar = BannerWidget("", action_text="清除", banner_type="error")
        self._crash_bar.setVisible(False)
        self._crash_bar.action_clicked.connect(self._dismiss_crash)
        self._crash_bar.closed.connect(self._dismiss_crash)
        root.addWidget(self._crash_bar)

        # 检测崩溃日志
        from crash_reporter import has_crash_report, read_crash_report

        if has_crash_report():
            crash_text = read_crash_report()
            summary = "上次运行异常退出"
            if crash_text:
                for line in crash_text.splitlines():
                    if line.startswith("崩溃时间:"):
                        summary = f"上次崩溃: {line.split(':', 1)[1].strip()}"
                        break
            self._crash_bar.set_text(f"{summary}，日志已记录到 crash.log")
            self._crash_bar.setVisible(True)

        # ── Hero Status 卡片 ──
        hero_card = QFrame()
        hero_card.setFixedHeight(80)
        hero_card.setAttribute(Qt.WA_StyledBackground, True)
        hero_card.setObjectName("hero-card")
        hero_card.setStyleSheet(
            "QFrame#hero-card {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 rgba(30, 45, 65, 0.85),"
            "    stop:1 rgba(22, 27, 34, 0.95));"
            "  border: 1px solid rgba(255, 255, 255, 0.08);"
            "  border-radius: 8px;"
            "}"
        )
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(16, 0, 16, 0)
        hero_layout.setSpacing(14)

        # 左侧大状态图标
        self._hero_icon = QLabel("●")
        self._hero_icon.setFixedSize(32, 32)
        self._hero_icon.setAlignment(Qt.AlignCenter)
        self._hero_icon.setStyleSheet(
            "font-size: 24px; color: #3fb950;"
            " background: transparent; border: none;"
        )
        hero_layout.addWidget(self._hero_icon)

        # 中间状态文字列
        hero_text_col = QVBoxLayout()
        hero_text_col.setSpacing(2)
        self._hero_status_text = QLabel("正在监听")
        self._hero_status_text.setStyleSheet(
            f"color: {T1}; font-size: 15px; font-weight: 700;"
            " background: transparent; border: none;"
        )
        hero_text_col.addWidget(self._hero_status_text)
        self._hero_summary = QLabel(self._last_notif_summary)
        self._hero_summary.setStyleSheet(
            f"color: {T3}; font-size: 11px;"
            " background: transparent; border: none;"
        )
        hero_text_col.addWidget(self._hero_summary)
        hero_layout.addLayout(hero_text_col, 1)

        # 右侧: 暂停按钮 + 运行时长
        hero_right_col = QVBoxLayout()
        hero_right_col.setSpacing(4)
        hero_right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._pause_btn = QPushButton("暂停")
        self._pause_btn.setFixedSize(90, 32)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.clicked.connect(self.toggle_pause)
        self._pause_btn.setStyleSheet(self._btn_primary())
        _shadow(self._pause_btn)
        self._pause_btn.setToolTip("暂停或恢复监控")
        hero_right_col.addWidget(self._pause_btn)

        self._hero_runtime = QLabel("已运行 0 分钟")
        self._hero_runtime.setStyleSheet(
            f"color: {T3}; font-size: 10px; font-family: {MONO};"
            " background: transparent; border: none;"
        )
        self._hero_runtime.setAlignment(Qt.AlignRight)
        hero_right_col.addWidget(self._hero_runtime)

        hero_layout.addLayout(hero_right_col)
        self._animatable_cards.append(hero_card)
        root.addWidget(hero_card)

        # StatusIndicator kept hidden for internal API compat
        self._status = StatusIndicator()
        self._status.hide()

        self._runtime_timer = QTimer(self)
        self._runtime_timer.timeout.connect(self._update_hero_runtime)
        self._runtime_timer.start(30000)

        # ── 今日概览卡片 ──
        stats_card = SectionCard("今日概览")
        stats_inner = QHBoxLayout()
        stats_inner.setSpacing(24)

        self._stat_today = self._make_stat_item("0", "条通知")
        stats_inner.addWidget(self._stat_today[0])

        self._stat_waiting = self._make_stat_item("0", "等待中")
        stats_inner.addWidget(self._stat_waiting[0])

        self._stat_errors = self._make_stat_item("0", "错误")
        stats_inner.addWidget(self._stat_errors[0])

        stats_card.add_layout(stats_inner)
        root.addWidget(stats_card)
        self._animatable_cards.append(stats_card)
        self._stats_card = stats_card

        # ── 监控来源卡片（动态生成，由 adapter 注册表驱动）──
        self._sources_card = SectionCard("监控来源")
        self._source_switches: dict[str, ToggleSwitch] = {}
        # source switches 会在 set_adapter_info 中动态创建
        root.addWidget(self._sources_card)
        self._animatable_cards.append(self._sources_card)

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

        # 音量滑块行
        vol_row = QHBoxLayout()
        vol_row.setSpacing(10)
        vol_label = QLabel("🔊")
        vol_label.setFixedWidth(20)
        vol_label.setStyleSheet(f"color: {T2}; font-size: 14px; border: none;")
        vol_row.addWidget(vol_label)

        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(self._config.get("sound_volume", 70))
        self._vol_slider.setFixedHeight(24)
        self._vol_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                border: 2px solid rgba(255,255,255,0.2);
            }}
            QSlider::handle:horizontal:hover {{
                background: #79bbff;
                border-color: rgba(255,255,255,0.35);
            }}
            QSlider::sub-page:horizontal {{
                background: {ACCENT};
                border-radius: 3px;
            }}
            QSlider::add-page:horizontal {{
                background: rgba(255,255,255,0.06);
                border-radius: 3px;
            }}
        """)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        vol_row.addWidget(self._vol_slider, 1)

        self._vol_value = QLabel(f'{self._config.get("sound_volume", 70)}%')
        self._vol_value.setFixedWidth(35)
        self._vol_value.setAlignment(Qt.AlignRight)
        self._vol_value.setStyleSheet(
            f"color: {T3}; font-size: 11px; font-family: {MONO}; border: none;"
        )
        vol_row.addWidget(self._vol_value)

        self._vol_container = QWidget()
        self._vol_container.setStyleSheet("background: transparent;")
        self._vol_container.setLayout(vol_row)
        self._vol_container.setVisible(self._sound_sw.isChecked())
        notif_card.add_widget(self._vol_container)

        # 开机自启开关
        autostart_row = QHBoxLayout()
        autostart_row.setSpacing(20)
        self._autostart_sw = self._make_toggle("开机自启")
        from autostart import is_autostart_enabled

        self._autostart_sw.setChecked(is_autostart_enabled())
        self._autostart_sw.toggled.connect(self._on_autostart_toggled)
        self._autostart_sw.setToolTip("开机时自动启动 Agent Notify")
        autostart_row.addWidget(self._autostart_sw)
        autostart_row.addStretch()
        notif_card.add_layout(autostart_row)

        # 提示音路径行
        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self._sound_icon = QLabel("♪")
        self._sound_icon.setFixedWidth(16)
        self._sound_icon.setStyleSheet(
            "color: rgba(255,255,255,0.35); font-size: 12px; border: none;"
        )

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
        self._animatable_cards.append(notif_card)

        # ── 免打扰卡片 ──
        dnd_card = SectionCard("免打扰")

        self._dnd_sw = self._make_toggle("启用免打扰时段")
        self._dnd_sw.setChecked(self._config.get("dnd_enabled", False))
        self._dnd_sw.toggled.connect(self._on_dnd_toggled)
        self._dnd_sw.setToolTip("在指定时段内静音所有通知")
        dnd_card.add_widget(self._dnd_sw)

        dnd_time_row = QHBoxLayout()
        dnd_time_row.setSpacing(8)

        dnd_time_row.addWidget(self._make_label("从"))
        _time_re = QRegularExpression(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
        _time_validator = QRegularExpressionValidator(_time_re)

        self._dnd_start_input = QLineEdit(self._config.get("dnd_start", "22:00"))
        self._dnd_start_input.setFixedWidth(60)
        self._dnd_start_input.setMaxLength(5)
        self._dnd_start_input.setValidator(_time_validator)
        self._dnd_start_input.setStyleSheet(self._input_style())
        self._dnd_start_input.editingFinished.connect(self._save_dnd_times)
        self._dnd_start_input.setPlaceholderText("HH:MM")
        dnd_time_row.addWidget(self._dnd_start_input)

        dnd_time_row.addWidget(self._make_label("到"))
        self._dnd_end_input = QLineEdit(self._config.get("dnd_end", "08:00"))
        self._dnd_end_input.setFixedWidth(60)
        self._dnd_end_input.setMaxLength(5)
        self._dnd_end_input.setValidator(_time_validator)
        self._dnd_end_input.setStyleSheet(self._input_style())
        self._dnd_end_input.editingFinished.connect(self._save_dnd_times)
        self._dnd_end_input.setPlaceholderText("HH:MM")
        dnd_time_row.addWidget(self._dnd_end_input)

        dnd_time_row.addStretch()
        dnd_card.add_layout(dnd_time_row)

        self._update_dnd_controls(self._dnd_sw.isChecked())
        root.addWidget(dnd_card)
        self._animatable_cards.append(dnd_card)

        # ── 最近通知卡片 ──
        history_card = SectionCard("最近通知")
        history_card.setMinimumHeight(100)

        self._history_list = QListWidget()
        self._history_list.setStyleSheet("""
            QListWidget {
                background: rgba(0,0,0,0.20);
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                color: rgba(255,255,255,0.65);
                font-size: 11px;
                padding: 5px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """ + SCROLLBAR_STYLE)
        self._history_list.setMaximumHeight(160)
        self._history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._history_list.setToolTip("最近收到的通知记录")

        history_card.add_widget(self._history_list)

        # 筛选标签
        self._history_filter = "all"
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self._filter_btns = {}
        for key, label in [
            ("all", "全部"), ("waiting", "等待"), ("running", "运行"),
            ("error", "错误"), ("success", "完成"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(24)
            btn.clicked.connect(lambda checked, k=key: self._set_history_filter(k))
            btn.setStyleSheet(self._filter_btn_style(key == "all"))
            self._filter_btns[key] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        history_card.add_layout(filter_row)

        self._empty_label = QLabel("暂无通知")
        self._empty_label.setStyleSheet(
            "color: rgba(255,255,255,0.25); font-size: 12px; border: none;"
        )
        self._empty_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        history_card.add_widget(self._empty_label)

        btn_row_hist = QHBoxLayout()
        btn_row_hist.setSpacing(8)

        clear_btn = QPushButton("🗑 清除历史")
        clear_btn.setFixedHeight(30)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(self._btn_danger())
        clear_btn.setToolTip("清空所有通知记录")
        clear_btn.clicked.connect(self._clear_history)
        btn_row_hist.addWidget(clear_btn)
        log_btn = QPushButton("📂 查看日志")
        log_btn.setFixedHeight(30)
        log_btn.setCursor(Qt.PointingHandCursor)
        log_btn.setStyleSheet(self._btn_ghost())
        log_btn.setToolTip("打开日志文件夹")
        log_btn.clicked.connect(self._open_log_folder)
        btn_row_hist.addWidget(log_btn)

        btn_row_hist.addStretch()
        history_card.add_layout(btn_row_hist)

        root.addWidget(history_card, stretch=1)
        self._animatable_cards.append(history_card)
        self._refresh_history()

        # ── QScrollArea 包裹 ──
        self._setup_animations()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def sizeHint(self):
        return QSize(500, 700)

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

    def _btn_success(self) -> str:
        return f"""
            QPushButton {{
                background: rgba(63,185,80,0.18);
                color: #3fb950;
                border: 1px solid rgba(63,185,80,0.35);
                border-radius: 18px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
                font-family: {FONT};
            }}
            QPushButton:hover {{ background: rgba(63,185,80,0.30); }}
        """

    # ── 公开方法 ──────────────────────────────────────────

    def set_status(self, text: str, color: QColor = None):
        self._status.set_status(text, color)
        # Update hero card
        self._hero_status_text.setText(text)
        if color is not None:
            self._hero_icon.setStyleSheet(
                f"font-size: 24px; color: {color.name()};"
                " background: transparent; border: none;"
            )

    def set_notif_count(self, count: int):
        self._status.set_count(count)
        if count > 0:
            self._hero_summary.setText(f"已捕获 {count} 个事件")

    def show_last_notification(self, event: AgentEvent):
        """从 AgentEvent 添加历史记录。"""
        self._history.append(
            {
                "time": _time.strftime("%H:%M:%S"),
                "timestamp": _time.time(),
                "event_type": event.event_type,
                "message": event.message,
                "agent_id": event.agent_id,
            }
        )
        max_history = self._config.get("max_history", 200)
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]
        self._save_history()
        self._refresh_history()
        self._update_hero_summary(event)
        self._update_stats()

    # ── 内部方法 ──────────────────────────────────────────

    def _load_history(self) -> list[dict]:
        """从磁盘加载通知历史。"""
        try:
            if HISTORY_FILE.exists():
                return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def _save_history(self) -> None:
        """将通知历史写入磁盘。"""
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(
                json.dumps(self._history, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _clear_history(self) -> None:
        """清空通知历史。"""
        self._history.clear()
        self._save_history()
        self._refresh_history()

    def _dismiss_crash(self) -> None:
        """关闭崩溃横幅并清除崩溃报告。"""
        from crash_reporter import clear_crash_report

        clear_crash_report()
        self._crash_bar.hide()

    def _set_history_filter(self, key: str):
        self._history_filter = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._filter_btn_style(k == key))
        self._refresh_history()

    @staticmethod
    def _filter_btn_style(active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: rgba(88, 166, 255, 0.2);
                    color: #58a6ff;
                    border: 1px solid rgba(88, 166, 255, 0.3);
                    border-radius: 12px;
                    padding: 0 10px;
                    font-size: 11px;
                }
            """
        return """
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.5);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 0 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                border-color: rgba(255,255,255,0.2);
            }
        """

    def _open_log_folder(self) -> None:
        """打开日志文件夹。"""
        from constants import SIGNAL_DIR

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(SIGNAL_DIR)))

    def _refresh_history(self):
        self._history_list.clear()
        filtered = self._history
        if hasattr(self, "_history_filter") and self._history_filter != "all":
            filtered = [
                e for e in self._history
                if e.get("event_type") == self._history_filter
            ]
        if not filtered:
            self._history_list.hide()
            self._empty_label.show()
            return

        self._empty_label.hide()
        self._history_list.show()

        for entry in reversed(filtered):
            agent_id = entry.get("agent_id", "")
            source_display = self._adapter_display_names.get(agent_id, agent_id or "?")

            event_type = entry.get("event_type", "info")
            event_tag = _EVENT_TAGS.get(event_type, "信息")
            rel = _relative_time(entry.get("timestamp", 0))
            text = f"{rel}  [{event_tag}]  {entry['message']}"
            item = QListWidgetItem(text)
            item.setToolTip(f"来源: {source_display}\n时间: {entry.get('time', '')}")
            self._history_list.addItem(item)

        self._history_list.scrollToBottom()

    def set_update_info(self, info) -> None:
        """显示更新提示横幅。由 TrayApp 调用。"""
        self._update_bar.set_text(
            f"新版本 {info.latest_version} 可用（当前 v{__version__}）"
        )
        self._update_url = info.download_url or info.html_url
        self._update_bar.setVisible(True)

    def _open_download(self):
        if self._update_url:
            QDesktopServices.openUrl(QUrl(self._update_url))

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
        if hasattr(self, "_vol_container"):
            self._vol_container.setVisible(checked)
        self._save()

    def _on_volume_changed(self, value: int):
        if hasattr(self, "_vol_value"):
            self._vol_value.setText(f"{value}%")
        self._save()

    def _on_autostart_toggled(self, checked: bool):
        from autostart import set_autostart

        set_autostart(checked)

    def _pick_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择提示音",
            "",
            "音频文件 (*.wav *.mp3);;WAV 文件 (*.wav);;MP3 文件 (*.mp3);;所有文件 (*)",
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

        vol = self._vol_slider.value() if hasattr(self, "_vol_slider") else 70
        play_sound(self._config.get("custom_sound", ""), volume=vol)

    def _send_test_notification(self):
        """发送测试通知并显示结果。"""
        test_msg = "这是一条测试通知，设置已生效"
        test_event = AgentEvent(
            agent_id="test",
            event_type=EventType.INFO,
            message=test_msg,
        )
        self.show_last_notification(test_event)

        success = True
        error_msg = ""

        if self._toast_sw.isChecked():
            try:
                from notification import notify

                notify(
                    "Agent Notify 测试",
                    test_msg,
                    sound=self._sound_sw.isChecked(),
                    source="test",
                    sound_path=self._config.get("custom_sound", ""),
                )
            except Exception as e:
                success = False
                error_msg = str(e)

        # 显示测试结果
        if success:
            self._test_btn.setText("✓ 已发送")
            self._test_btn.setStyleSheet(self._btn_success())
        else:
            self._test_btn.setText("✗ 失败")
            self._test_btn.setStyleSheet(self._btn_danger())
            logger.warning("测试通知发送失败: %s", error_msg)

        # 2 秒后恢复按钮状态
        QTimer.singleShot(2000, self._reset_test_btn)

    def _reset_test_btn(self):
        """重置测试通知按钮状态。"""
        self._test_btn.setText("测试通知")
        self._test_btn.setStyleSheet(self._btn_ghost())

    def toggle_pause(self):
        from ui.widgets import apply_pause_filter

        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.setText("继续")
            self._pause_btn.setStyleSheet(self._btn_danger())
            self.set_status("已暂停", ORANGE)
            self._hero_summary.setText("监控已暂停，不会接收新通知")
        else:
            self._pause_btn.setText("暂停")
            self._pause_btn.setStyleSheet(self._btn_primary())
            self.set_status("监控中", GREEN)
            self._hero_summary.setText(self._last_notif_summary)
        apply_pause_filter(self._scroll, self._is_paused)
        self.pause_toggled.emit(self._is_paused)

    def _save(self):
        self._config["sound_enabled"] = self._sound_sw.isChecked()
        self._config["toast_enabled"] = self._toast_sw.isChecked()
        if hasattr(self, "_vol_slider"):
            self._config["sound_volume"] = self._vol_slider.value()
        for key, sw in self._source_switches.items():
            self._config[key] = sw.isChecked()
        save_config(self._config)
        self.config_changed.emit()

    def _make_stat_item(self, num: str, label: str) -> tuple:
        """Create a stat display widget (number + label). Returns (widget, num_label)."""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        num_lbl = QLabel(num)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(
            f"color: {T1}; font-size: 22px; font-weight: 700; border: none;"
        )
        layout.addWidget(num_lbl)

        desc = QLabel(label)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {T3}; font-size: 11px; border: none;")
        layout.addWidget(desc)

        return (w, num_lbl)

    def _update_stats(self):
        """Update the stats card numbers from history."""
        if not hasattr(self, "_stat_today"):
            return
        import time as _t
        now = _t.time()
        today_start = now - (now % 86400)
        today_entries = [e for e in self._history if e.get("timestamp", 0) >= today_start]
        waiting = sum(1 for e in today_entries if e.get("event_type") == "waiting")
        errors = sum(1 for e in today_entries if e.get("event_type") == "error")
        self._stat_today[1].setText(str(len(today_entries)))
        self._stat_waiting[1].setText(str(waiting))
        self._stat_errors[1].setText(str(errors))

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {T2}; font-size: 12px; border: none;")
        return lbl

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background: rgba(0,0,0,0.25);
                color: {T1};
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                font-family: {MONO};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT.name()};
            }}
        """

    def _on_dnd_toggled(self, checked: bool):
        self._config["dnd_enabled"] = checked
        save_config(self._config)
        self.config_changed.emit()
        self._update_dnd_controls(checked)

    def _update_dnd_controls(self, enabled: bool):
        self._dnd_start_input.setEnabled(enabled)
        self._dnd_end_input.setEnabled(enabled)

    def _save_dnd_times(self):
        start = self._dnd_start_input.text().strip()
        end = self._dnd_end_input.text().strip()
        # 只保存合法的 HH:MM 格式
        import re

        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start):
            start = "22:00"
            self._dnd_start_input.setText(start)
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end):
            end = "08:00"
            self._dnd_end_input.setText(end)
        self._config["dnd_start"] = start
        self._config["dnd_end"] = end
        save_config(self._config)
        self.config_changed.emit()

    def showEvent(self, event):
        super().showEvent(event)
        # 恢复窗口几何（仅首次）
        if not getattr(self, "_geometry_restored", False):
            self._geometry_restored = True
            s = QSettings("AgentNotify", "SettingsWindow")
            geo = s.value("geometry")
            if geo:
                self.restoreGeometry(geo)
            else:
                self.resize(500, 700)
        self.layout().activate()
        QTimer.singleShot(0, self._sync_glow)
        # Play entrance animations on first show
        if not self._animations_played:
            self._animations_played = True
            QTimer.singleShot(80, self._play_entrance_animations)

    def _sync_glow(self):
        self._glow.setGeometry(0, 0, self.width(), self.height())

    # ── 动画方法 ──────────────────────────────────────────

    def _setup_animations(self):
        """Pre-configure entrance animations: set all cards to invisible."""
        for card in self._animatable_cards:
            eff = QGraphicsOpacityEffect(card)
            eff.setOpacity(0.0)
            card.setGraphicsEffect(eff)

    def _play_entrance_animations(self):
        """Play staggered fade-in + slide-up for all cards."""
        self._running_anims: list = []
        for i, card in enumerate(self._animatable_cards):
            delay = i * 60  # ANIM_STAGGER = 60ms
            QTimer.singleShot(
                delay,
                lambda c=card, idx=i: self._animate_single_card(c, idx),
            )

    def _animate_single_card(self, card: QWidget, index: int):
        """Animate a single card: fade-in + slide-up."""
        from PySide6.QtCore import QPoint, QEasingCurve

        duration = 250  # ANIM_NORMAL
        slide_offset = 20  # pixels
        ease = QEasingCurve.Type.OutQuart

        original_pos = card.pos()
        start_pos = QPoint(int(original_pos.x()), int(original_pos.y()) + slide_offset)

        group = QParallelAnimationGroup(self)

        # Opacity animation
        eff = card.graphicsEffect()
        if isinstance(eff, QGraphicsOpacityEffect):
            opacity_anim = QPropertyAnimation(eff, b"opacity", self)
            opacity_anim.setDuration(duration)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(ease)
            group.addAnimation(opacity_anim)

        # Position animation (slide-up)
        pos_anim = QPropertyAnimation(card, b"pos", self)
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(original_pos)
        pos_anim.setEasingCurve(ease)
        group.addAnimation(pos_anim)

        self._running_anims.append(group)
        group.finished.connect(lambda g=group: self._on_card_anim_finished(g))
        group.start()

    def _on_card_anim_finished(self, group):
        """Clean up finished animation reference."""
        if group in self._running_anims:
            self._running_anims.remove(group)

    def _update_hero_runtime(self):
        """Update the hero card's runtime display."""
        elapsed = int(_time.time() - self._hero_start_time)
        if elapsed < 60:
            self._hero_runtime.setText(f"已运行 {elapsed} 秒")
        else:
            mins = elapsed // 60
            self._hero_runtime.setText(f"已运行 {mins} 分钟")

    def _update_hero_summary(self, event):
        """Update hero card summary with latest notification."""
        tag = _EVENT_TAGS.get(event.event_type, "信息")
        summary = f"[{tag}] {event.message}"
        if len(summary) > 45:
            summary = summary[:42] + "..."
        self._last_notif_summary = summary
        self._hero_summary.setText(summary)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._glow.setGeometry(0, 0, self.width(), self.height())

    def closeEvent(self, event):
        # 保存窗口几何
        s = QSettings("AgentNotify", "SettingsWindow")
        s.setValue("geometry", self.saveGeometry())

        event.ignore()
        self.hide()
        # 首次关闭时在托盘显示提示
        if not getattr(self, "_close_hint_shown", False):
            self._close_hint_shown = True
            tray = self.parent()
            if tray and hasattr(tray, "showMessage"):
                tray.showMessage(
                    "Agent Notify",
                    "应用已最小化到系统托盘，仍在后台运行",
                    1,  # QSystemTrayIcon.Information
                    3000,
                )

    @property
    def is_paused(self) -> bool:
        return self._is_paused
