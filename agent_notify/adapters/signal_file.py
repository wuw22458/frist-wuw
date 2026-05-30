"""SignalFileAdapter — 基于 JSON 信号文件轮询的 adapter 中间层。

子类只需声明类属性即可工作：
    glob_pattern:   匹配信号文件的 glob 模式
    exclude_names:  需要排除的文件名集合
    event_map:      原始 event 字符串 → EventType 的映射
    poll_interval_ms: 轮询间隔（毫秒）
"""

from __future__ import annotations

import json
from collections import OrderedDict

from constants import SIGNAL_DIR
from events import AgentEvent, EventType
from log import get_logger

from adapters.base import PollingAdapter

logger = get_logger("signal_file")

_MAX_PROCESSED = 500


class SignalFileAdapter(PollingAdapter):
    """信号文件轮询 adapter。子类声明配置属性即可。"""

    glob_pattern: str = "*.json"
    exclude_names: set[str] = {"config.json"}
    event_map: dict[str, EventType] = {}
    poll_interval_ms: int = 1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processed: OrderedDict[str, None] = OrderedDict()
        SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

    def check(self) -> None:
        """轮询信号目录，解析新 JSON 文件并发射事件。"""
        for f in sorted(SIGNAL_DIR.glob(self.glob_pattern)):
            if f.name in self._processed or f.name in self.exclude_names:
                continue
            self._processed[f.name] = None
            # LRU 淘汰：超过上限时移除最旧的一半
            while len(self._processed) > _MAX_PROCESSED:
                self._processed.popitem(last=False)
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                raw_event = data.get("event", "unknown")
                message = data.get("message", "")
                event_type = self.event_map.get(raw_event, EventType.INFO)
                logger.debug(
                    "[%s] 收到信号: event=%s msg=%s",
                    self.agent_id,
                    raw_event,
                    message[:60],
                )
                self.emit(
                    AgentEvent(
                        agent_id=self.agent_id,
                        event_type=event_type,
                        message=message,
                        metadata={"raw_event": raw_event},
                    )
                )
                f.unlink()
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "[%s] 信号文件解析失败，已删除 %s: %s | path=%s",
                    self.agent_id,
                    f.name,
                    e,
                    f,
                )
                try:
                    f.unlink()
                except OSError:
                    pass
