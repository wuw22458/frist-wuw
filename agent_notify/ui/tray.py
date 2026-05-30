"""托盘图标 + 右键菜单 — TrayApp。"""

from constants import __version__
from events import AgentEvent
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)
from settings import load_config
from updater import UpdateChecker, UpdateInfo, mark_checked, should_check

from ui.settings import SettingsWindow
from ui.widgets import (
    _EVENT_COLORS,
    _EVENT_STATUS_PREFIX,
    ACCENT,
    T1,
    _make_icon,
)


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

        # 全局快捷键（Ctrl+Shift+P 暂停/恢复）
        self._hotkey_host = QWidget(parent)  # 父对象管理生命周期
        self._pause_shortcut = QShortcut(
            QKeySequence("Ctrl+Shift+P"), self._hotkey_host
        )
        self._pause_shortcut.activated.connect(self.toggle_pause_from_menu)

        # 注入 adapter 信息到 SettingsWindow（延迟到 main.py 中 adapters 创建后）
        self._adapters = []

        self.setIcon(_make_icon())
        self.setToolTip(f"Agent Notify v{__version__}")

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

        a_check = QAction("检查更新", menu)
        a_check.triggered.connect(self._check_update_manual)
        menu.addAction(a_check)

        a_about = QAction("关于", menu)
        a_about.triggered.connect(self._show_about)
        menu.addAction(a_about)
        menu.addSeparator()

        self._pause_act = QAction("暂停 (Ctrl+Shift+P)", menu)
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

        # 后台检查更新（限频：6 小时内不重复检查）
        if should_check():
            self._update_checker = UpdateChecker(self)
            self._update_checker.result.connect(self._on_update_result)
            self._update_checker.start()
        else:
            self._update_checker = None

    def _on_update_result(self, info: UpdateInfo):
        mark_checked()
        if info.available:
            self.setToolTip(
                f"Agent Notify v{__version__} → 新版本 {info.latest_version} 可用"
            )
            self._settings.set_update_info(info)

    def set_adapters(self, adapters: list) -> None:
        """注入 adapter 列表，用于 SettingsWindow 动态生成 source switches。"""
        self._adapters = adapters
        self._settings.set_adapter_info(adapters)

    def _reload_config(self):
        self._config = load_config()

    def get_config(self) -> dict:
        """返回当前配置字典。"""
        return self._config

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
            self.setToolTip(f"Agent Notify v{__version__}")
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

    def _check_update_manual(self):
        """手动检查更新。"""
        self.showMessage("Agent Notify", "正在检查更新...", 0, 2000)
        checker = UpdateChecker(self)
        checker.result.connect(self._on_manual_update_result)
        checker.start()

    def _on_manual_update_result(self, info: UpdateInfo):
        mark_checked()
        if info.available:
            self.showMessage(
                "Agent Notify",
                f"发现新版本 {info.latest_version}，请在设置中下载更新",
                0,
                5000,
            )
            self._settings.set_update_info(info)
        else:
            self.showMessage("Agent Notify", "当前已是最新版本", 0, 3000)

    def _show_about(self):
        """显示关于信息。"""
        self.showMessage(
            "关于 Agent Notify",
            f"v{__version__}\n统一的 AI Agent 通知中心\nhttps://github.com/wuw22458/agent_notify",
            0,
            5000,
        )

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
