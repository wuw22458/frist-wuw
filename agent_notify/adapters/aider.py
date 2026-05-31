"""AiderAdapter — 基于 notify-cmd 信号文件的 Aider 检测.

Aider 原生支持 --notify-cmd 参数,在等待用户输入时执行指定命令.
用户配置 aider 写入 JSON 信号文件到 SIGNAL_DIR,本 adapter 轮询检测.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from adapters.registry import register_adapter
from adapters.signal_file import SignalFileAdapter
from events import EventType


@register_adapter
class AiderAdapter(SignalFileAdapter):
    """Aider 适配器 — 轮询信号目录检测 Aider 的 notify-cmd 信号."""

    agent_id = 'aider'
    display_name = 'Aider'
    description = '通过 --notify-cmd 机制监控 Aider CLI 的等待确认事件'
    glob_pattern = 'aider_*.json'
    exclude_names: set[str] = set()
    event_map = {
        'waiting': EventType.WAITING,
        'completed': EventType.COMPLETED,
    }

    @classmethod
    def detect(cls) -> bool:
        return shutil.which('aider') is not None

    @staticmethod
    def get_notify_cmd() -> str:
        """生成 Aider 的 --notify-cmd 配置字符串."""
        helper = Path(__file__).parent.parent / 'aider_notify_helper.py'
        return f'python "{helper}"'
