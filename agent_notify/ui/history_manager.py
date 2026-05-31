"""通知历史数据管理 — HistoryManager.

负责通知历史的加载、保存、过滤、统计。
"""

import json
import time as _time

from constants import HISTORY_FILE
from log import get_logger

logger = get_logger('history_manager')


class HistoryManager:
    """通知历史数据管理器."""

    def __init__(self, max_history: int = 200):
        self._history: list[dict] = []
        self._max_history = max_history
        self._load()

    def _load(self) -> None:
        """从磁盘加载通知历史."""
        try:
            if HISTORY_FILE.exists():
                self._history = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            self._history = []

    def _save(self) -> None:
        """将通知历史写入磁盘."""
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(
                json.dumps(self._history, ensure_ascii=False),
                encoding='utf-8',
            )
        except OSError:
            pass

    def add(self, entry: dict) -> None:
        """添加一条历史记录并保存."""
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        self._save()

    def clear(self) -> None:
        """清空所有历史记录."""
        self._history.clear()
        self._save()

    def get_all(self) -> list[dict]:
        """返回所有历史记录."""
        return self._history

    def get_filtered(self, event_type: str = 'all') -> list[dict]:
        """按事件类型过滤历史记录."""
        if event_type == 'all':
            return self._history
        return [e for e in self._history if e.get('event_type') == event_type]

    def get_today_stats(self) -> dict:
        """获取今日统计数据."""
        now = _time.time()
        today_start = now - (now % 86400)
        today_entries = [e for e in self._history if e.get('timestamp', 0) >= today_start]

        waiting = sum(1 for e in today_entries if e.get('event_type') == 'waiting')
        errors = sum(1 for e in today_entries if e.get('event_type') == 'error')

        return {
            'total': len(today_entries),
            'waiting': waiting,
            'errors': errors,
        }

    def get_filter_counts(self) -> dict:
        """获取各类型的历史记录数量."""
        counts = {'all': len(self._history)}
        for entry in self._history:
            event_type = entry.get('event_type', 'info')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
