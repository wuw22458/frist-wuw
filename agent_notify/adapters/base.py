"""AgentAdapter — 所有 Agent 适配器的抽象基类.

继承层次:
    AgentAdapter (抽象基类)
      └── PollingAdapter (QTimer + 生命周期管理)
            ├── SignalFileAdapter (JSON 文件信号轮询)
            └── 其他自定义 adapter
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
from abc import ABC, abstractmethod

from PySide6.QtCore import QTimer

from adaptive_polling import AdaptivePolling
from event_bus import EventBus
from events import AgentEvent, EventType


class AgentAdapter(ABC):
    """Agent 适配器抽象基类.

    子类必须定义以下类属性:
        agent_id:      唯一标识符,如 "claude-code", "cursor", "aider"
        display_name:  UI 显示名称,如 "Claude Code", "Cursor"
        description:   一行功能描述
    """

    agent_id: str = ''
    display_name: str = ''
    description: str = ''

    def __init__(self, event_bus: EventBus, config: dict):
        self._bus = event_bus
        self._config = config
        self._running = False

    @abstractmethod
    def start(self) -> None:
        """启动 agent 状态检测."""

    @abstractmethod
    def stop(self) -> None:
        """停止 agent 状态检测."""

    @abstractmethod
    def is_running(self) -> bool:
        """返回当前是否正在运行."""

    def emit(self, event: AgentEvent) -> None:
        """向 EventBus 发射事件."""
        self._bus.event_received.emit(event)

    def update_config(self, config: dict) -> None:
        """运行时更新配置(由 SettingsWindow 触发)."""
        self._config = config

    def get_status(self) -> dict:
        """返回 adapter 状态信息,用于 UI 展示."""
        return {'running': self.is_running()}

    @classmethod
    def get_config_schema(cls) -> dict:
        """返回此 adapter 需要的配置项定义."""
        return {}

    def is_enabled(self) -> bool:
        """检查此 adapter 在配置中是否启用."""
        return self._config.get(f'source_{self.agent_id}', True)

    @classmethod
    def detect(cls) -> bool:
        """检测此 agent 是否已安装.子类可覆盖.默认返回 False."""
        return False


class PollingAdapter(AgentAdapter):
    """基于 QTimer 轮询的 adapter 中间层.

    子类只需实现 check() 方法,timer 生命周期由本类管理.
    支持自适应轮询:根据事件频率动态调整轮询间隔.
    """

    poll_interval_ms: int = 1000
    use_adaptive_polling: bool = True

    def __init__(self, event_bus: EventBus, config: dict):
        super().__init__(event_bus, config)
        self._timer: QTimer | None = None
        self._adaptive: AdaptivePolling | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True

        # 初始化自适应轮询
        if self.use_adaptive_polling:
            self._adaptive = AdaptivePolling(
                min_interval=self.poll_interval_ms // 2,
                max_interval=self.poll_interval_ms * 5,
                base_interval=self.poll_interval_ms,
            )

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        self._timer.start(self.poll_interval_ms)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _on_timer(self) -> None:
        """定时器回调,执行检查并更新轮询间隔."""
        if self._adaptive:
            self._adaptive.record_check()

        self.check()

        # 更新轮询间隔
        if self._adaptive and self._timer:
            new_interval = self._adaptive.update_interval()
            if new_interval != self._timer.interval():
                self._timer.setInterval(new_interval)

    def emit(self, event: AgentEvent) -> None:
        """发射事件并记录(用于自适应轮询)."""
        if self._adaptive:
            self._adaptive.record_event()
        super().emit(event)

    @abstractmethod
    def check(self) -> None:
        """单次轮询检测.由 QTimer 定时调用."""


def _enum_window_titles(title_filter: str) -> list[str]:
    """枚举所有窗口标题,返回含 title_filter 且含 'needs attention' 的标题."""
    titles: list[str] = []

    def _enum_callback(hwnd, _):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if title_filter in title and 'needs attention' in title.lower():
                titles.append(title)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(_enum_callback), 0)
    return titles


class WindowPollingAdapter(PollingAdapter):
    """基于窗口标题轮询的 adapter 基类(Cursor / Windsurf 等 IDE).

    子类只需声明:
        agent_id, display_name, description, poll_interval_ms
        _window_title_filter: 窗口标题中需包含的字符串(如 "Cursor")
        _attention_message:   需要确认时的消息
        _continue_message:    继续运行时的消息
        detect():             检测是否已安装
    """

    _window_title_filter: str = ''
    _attention_message: str = 'Agent 需要你的确认'
    _continue_message: str = 'Agent 已继续运行'
    poll_interval_ms: int = 3000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._waiting = False

    def start(self) -> None:
        super().start()
        self._waiting = False

    def check(self) -> None:
        try:
            titles = _enum_window_titles(self._window_title_filter)
        except Exception:
            return

        has_attention = len(titles) > 0

        if has_attention and not self._waiting:
            self._waiting = True
            self.emit(
                AgentEvent(
                    agent_id=self.agent_id,
                    event_type=EventType.WAITING,
                    message=self._attention_message,
                    metadata={'window_titles': titles},
                )
            )
        elif not has_attention and self._waiting:
            self._waiting = False
            self.emit(
                AgentEvent(
                    agent_id=self.agent_id,
                    event_type=EventType.COMPLETED,
                    message=self._continue_message,
                )
            )
