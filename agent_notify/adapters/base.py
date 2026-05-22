"""AgentAdapter — 所有 Agent 适配器的抽象基类。

继承层次：
    AgentAdapter (抽象基类)
      └── PollingAdapter (QTimer + 生命周期管理)
            ├── SignalFileAdapter (JSON 文件信号轮询)
            └── 其他自定义 adapter
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6.QtCore import QTimer

from event_bus import EventBus
from events import AgentEvent


class AgentAdapter(ABC):
    """Agent 适配器抽象基类。

    子类必须定义以下类属性：
        agent_id:      唯一标识符，如 "claude-code", "cursor", "aider"
        display_name:  UI 显示名称，如 "Claude Code", "Cursor"
        description:   一行功能描述
    """

    agent_id: str = ""
    display_name: str = ""
    description: str = ""

    def __init__(self, event_bus: EventBus, config: dict):
        self._bus = event_bus
        self._config = config
        self._running = False

    @abstractmethod
    def start(self) -> None:
        """启动 agent 状态检测。"""

    @abstractmethod
    def stop(self) -> None:
        """停止 agent 状态检测。"""

    @abstractmethod
    def is_running(self) -> bool:
        """返回当前是否正在运行。"""

    def emit(self, event: AgentEvent) -> None:
        """向 EventBus 发射事件。"""
        self._bus.event_received.emit(event)

    def update_config(self, config: dict) -> None:
        """运行时更新配置（由 SettingsWindow 触发）。"""
        self._config = config

    def get_status(self) -> dict:
        """返回 adapter 状态信息，用于 UI 展示。"""
        return {"running": self.is_running()}

    @classmethod
    def get_config_schema(cls) -> dict:
        """返回此 adapter 需要的配置项定义。"""
        return {}

    def is_enabled(self) -> bool:
        """检查此 adapter 在配置中是否启用。"""
        return self._config.get(f"source_{self.agent_id}", True)

    @classmethod
    def detect(cls) -> bool:
        """检测此 agent 是否已安装。子类可覆盖。默认返回 False。"""
        return False


class PollingAdapter(AgentAdapter):
    """基于 QTimer 轮询的 adapter 中间层。

    子类只需实现 check() 方法，timer 生命周期由本类管理。
    """

    poll_interval_ms: int = 1000

    def __init__(self, event_bus: EventBus, config: dict):
        super().__init__(event_bus, config)
        self._timer: QTimer | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self.check)
        self._timer.start(self.poll_interval_ms)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._running = False

    def is_running(self) -> bool:
        return self._running

    @abstractmethod
    def check(self) -> None:
        """单次轮询检测。由 QTimer 定时调用。"""
