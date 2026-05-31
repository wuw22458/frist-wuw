"""EventBus — 中央事件总线,解耦 adapter 与 UI/通知层.

所有 AgentAdapter 向 EventBus emit 事件,TrayApp 和通知引擎从 EventBus subscribe.
使用 Qt Signal 实现线程安全的跨组件通信.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from events import AgentEvent


class EventBus(QObject):
    """全局事件总线(单例模式,通过 module-level 变量访问).

    Signals:
        event_received: 收到任意 agent 事件
        adapter_registered: 新 adapter 注册
        adapter_removed: adapter 移除
    """

    event_received = Signal(AgentEvent)
    adapter_registered = Signal(str)  # agent_id
    adapter_removed = Signal(str)  # agent_id


# 模块级单例 — main.py 初始化后所有模块共享
_bus: EventBus | None = None


def get_bus() -> EventBus:
    """获取全局 EventBus 实例.必须在 QApplication 创建后调用."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def reset_bus() -> None:
    """重置全局 EventBus(仅用于测试)."""
    global _bus
    _bus = None
