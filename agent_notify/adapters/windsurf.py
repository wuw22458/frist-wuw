"""WindsurfAdapter — 基于窗口标题轮询的 Windsurf IDE 检测."""

from __future__ import annotations

import shutil
from pathlib import Path

from adapters.base import WindowPollingAdapter
from adapters.registry import register_adapter


@register_adapter
class WindsurfAdapter(WindowPollingAdapter):
    """Windsurf IDE 适配器 — 轮询窗口标题检测 Agent 等待状态."""

    agent_id = 'windsurf'
    display_name = 'Windsurf'
    description = '通过窗口标题监控 Windsurf IDE 的 Agent 等待确认状态'
    _window_title_filter = 'Windsurf'
    _attention_message = 'Windsurf Agent 需要你的确认'
    _continue_message = 'Windsurf Agent 已继续运行'

    @classmethod
    def detect(cls) -> bool:
        candidates = [
            Path.home() / 'AppData' / 'Local' / 'Programs' / 'Windsurf' / 'Windsurf.exe',
            Path(r'C:\Program Files\Windsurf\Windsurf.exe'),
        ]
        if shutil.which('windsurf'):
            return True
        return any(p.exists() for p in candidates)
