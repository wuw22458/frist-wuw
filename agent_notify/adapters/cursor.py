"""CursorAdapter — 基于窗口标题轮询的 Cursor IDE 检测。"""

from __future__ import annotations

import shutil
from pathlib import Path

from adapters.base import WindowPollingAdapter
from adapters.registry import register_adapter


@register_adapter
class CursorAdapter(WindowPollingAdapter):
    """Cursor IDE 适配器 — 轮询窗口标题检测 Agent 等待状态。"""

    agent_id = "cursor"
    display_name = "Cursor"
    description = "通过窗口标题监控 Cursor IDE 的 Agent 等待确认状态"
    _window_title_filter = "Cursor"
    _attention_message = "Cursor Agent 需要你的确认"
    _continue_message = "Cursor Agent 已继续运行"

    @classmethod
    def detect(cls) -> bool:
        candidates = [
            Path.home() / "AppData" / "Local" / "Programs" / "Cursor" / "Cursor.exe",
            Path(r"C:\Program Files\Cursor\Cursor.exe"),
        ]
        if shutil.which("cursor"):
            return True
        return any(p.exists() for p in candidates)
