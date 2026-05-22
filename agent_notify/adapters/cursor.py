"""CursorAdapter — 基于窗口标题轮询的 Cursor IDE 检测。

Cursor 在 Agent 模式下等待用户确认时，窗口标题包含 "needs attention"。
通过 ctypes 调用 Windows API 枚举窗口标题，状态机检测变化。
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import shutil
from pathlib import Path

from adapters.base import PollingAdapter
from adapters.registry import register_adapter
from events import AgentEvent, EventType


def _get_cursor_window_titles() -> list[str]:
    """枚举所有窗口标题，返回含 'Cursor' 且含 'needs attention' 的标题。"""
    titles: list[str] = []

    def _enum_callback(hwnd, _):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            if "Cursor" in title and "needs attention" in title.lower():
                titles.append(title)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(_enum_callback), 0)
    return titles


@register_adapter
class CursorAdapter(PollingAdapter):
    """Cursor IDE 适配器 — 轮询窗口标题检测 Agent 等待状态。"""

    agent_id = "cursor"
    display_name = "Cursor"
    description = "通过窗口标题监控 Cursor IDE 的 Agent 等待确认状态"
    poll_interval_ms = 3000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._waiting = False

    def start(self) -> None:
        super().start()
        self._waiting = False

    def check(self) -> None:
        """检测 Cursor 窗口标题，状态变化时发射事件。"""
        try:
            titles = _get_cursor_window_titles()
        except Exception:
            return

        has_attention = len(titles) > 0

        if has_attention and not self._waiting:
            self._waiting = True
            self.emit(AgentEvent(
                agent_id=self.agent_id,
                event_type=EventType.WAITING,
                message="Cursor Agent 需要你的确认",
                metadata={"window_titles": titles},
            ))
        elif not has_attention and self._waiting:
            self._waiting = False
            self.emit(AgentEvent(
                agent_id=self.agent_id,
                event_type=EventType.COMPLETED,
                message="Cursor Agent 已继续运行",
            ))

    @classmethod
    def detect(cls) -> bool:
        # 检查常见安装路径
        candidates = [
            Path.home() / "AppData" / "Local" / "Programs" / "Cursor" / "Cursor.exe",
            Path(r"C:\Program Files\Cursor\Cursor.exe"),
        ]
        if shutil.which("cursor"):
            return True
        return any(p.exists() for p in candidates)
