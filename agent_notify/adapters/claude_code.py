"""ClaudeCodeAdapter — 基于 JSON 信号文件的 Claude Code 检测。

Claude Code 的 hook 脚本写入 JSON 信号文件到 SIGNAL_DIR，
本 adapter 轮询目录解析新文件后发射 AgentEvent。
"""

from __future__ import annotations

import shutil

from adapters.signal_file import SignalFileAdapter
from adapters.registry import register_adapter
from events import EventType


@register_adapter
class ClaudeCodeAdapter(SignalFileAdapter):
    """Claude Code 适配器 — 轮询信号目录检测 Notification/Stop 事件。"""

    agent_id = "claude-code"
    display_name = "Claude Code"
    description = "通过 hook 机制监控 Claude Code CLI 的通知和任务完成事件"
    glob_pattern = "*.json"
    exclude_names = {"config.json"}
    event_map = {
        "notification": EventType.WAITING,
        "tool_use": EventType.WAITING,
        "permission": EventType.WAITING,
        "stop": EventType.COMPLETED,
    }

    @classmethod
    def detect(cls) -> bool:
        return shutil.which("claude") is not None
