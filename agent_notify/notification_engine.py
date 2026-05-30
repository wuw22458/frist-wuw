"""notification_engine.py — 通知引擎：EventBus → 声音 + Toast。

负责节流、免打扰、事件分发。从 main.py 中抽取以便独立测试。
"""

import time

from events import AgentEvent
from log import get_logger
from notification import notify

logger = get_logger("engine")


class NotificationEngine:
    """监听 EventBus 事件，根据配置发送 Toast + 声音通知。

    Features:
    - 节流：同一 agent+event_type 组合在 N 秒内不重复通知
    - 免打扰：在指定时段内静默
    - 暂停：外部控制暂停/恢复
    - 自动清理：防止内存泄漏
    """

    def __init__(self, throttle_sec: float = 3.0):
        self._throttle_sec = throttle_sec
        self._last_notif: dict[str, float] = {}
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def pause(self, paused: bool) -> None:
        self._paused = paused

    def handle_event(self, event: AgentEvent, config: dict) -> None:
        """处理一个 AgentEvent，决定是否发送通知。

        Args:
            event: 来自 EventBus 的事件。
            config: 用户配置（toast_enabled, sound_enabled, dnd_*, custom_sound 等）。
        """
        try:
            if self._paused:
                logger.debug("已暂停，忽略事件: %s", event.message[:60])
                return

            if self._is_dnd_active(config):
                logger.debug("免打扰时段，忽略事件: %s", event.message[:60])
                return

            dedup_key = f"{event.agent_id}:{event.event_type}"
            now = time.monotonic()
            last = self._last_notif.get(dedup_key, 0)
            if now - last < self._throttle_sec:
                logger.debug("节流抑制: %s (%.1fs)", dedup_key, now - last)
                return
            self._last_notif[dedup_key] = now

            # 清理超过 1 小时的旧条目
            if len(self._last_notif) > 100:
                cutoff = now - 3600
                stale = [k for k, v in self._last_notif.items() if v < cutoff]
                for k in stale:
                    del self._last_notif[k]

            title_map = {
                "waiting": "需要确认",
                "completed": "任务完成",
                "error": "出错了",
                "info": "通知",
            }
            title = title_map.get(event.event_type, "Agent Notify")
            if config.get("toast_enabled", True):
                notify(
                    title,
                    event.message,
                    sound=config.get("sound_enabled", True),
                    source=event.agent_id,
                    sound_path=config.get("custom_sound", ""),
                )
        except Exception:
            logger.exception("处理事件时出错")

    @staticmethod
    def _is_dnd_active(cfg: dict) -> bool:
        """检查当前是否在免打扰时段内。"""
        if not cfg.get("dnd_enabled", False):
            return False
        now = time.strftime("%H:%M")
        start = cfg.get("dnd_start", "22:00")
        end = cfg.get("dnd_end", "08:00")
        if start <= end:
            return start <= now < end
        return now >= start or now < end
