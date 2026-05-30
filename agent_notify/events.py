"""统一事件模型 — 所有 AgentAdapter 共享的事件数据结构。

事件类型：
    waiting   — Agent 需要用户确认（权限请求、命令审批等）
    completed — Agent 任务完成
    error     — Agent 运行出错
    info      — 一般信息通知
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class EventType(str, Enum):
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    INFO = "info"


@dataclass
class AgentEvent:
    """Agent 产生的统一事件。

    Attributes:
        agent_id:  产生事件的 agent 标识，如 "claude-code", "cursor", "aider"
        event_type: 事件类型，见 EventType 枚举
        message:   人类可读的事件消息
        timestamp: 事件产生时间（epoch seconds），默认为当前时间
        metadata:  agent 特有的附加数据，如 session_id、notification_type 等
    """

    agent_id: str
    event_type: EventType
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    @property
    def is_waiting(self) -> bool:
        return self.event_type == EventType.WAITING

    @property
    def is_completed(self) -> bool:
        return self.event_type == EventType.COMPLETED

    @property
    def is_error(self) -> bool:
        return self.event_type == EventType.ERROR
