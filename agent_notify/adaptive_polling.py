"""自适应轮询 — 根据系统负载动态调整轮询间隔。"""

import time
from typing import Optional

from log import get_logger

logger = get_logger("adaptive_polling")


class AdaptivePolling:
    """自适应轮询管理器。

    根据以下因素动态调整轮询间隔：
    1. 系统负载（通过事件频率推断）
    2. 用户活跃度（最近是否有交互）
    3. 时间段（夜间降低频率）

    属性：
        min_interval: 最小轮询间隔（毫秒）
        max_interval: 最大轮询间隔（毫秒）
        base_interval: 基础轮询间隔（毫秒）
    """

    def __init__(
        self,
        min_interval: int = 500,
        max_interval: int = 5000,
        base_interval: int = 1000,
    ):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.base_interval = base_interval

        self._current_interval = base_interval
        self._last_event_time: float = 0
        self._event_count: int = 0
        self._last_adjust_time: float = time.time()

        # 性能监控
        self._total_checks: int = 0
        self._total_events: int = 0
        self._interval_changes: int = 0

    @property
    def current_interval(self) -> int:
        """当前轮询间隔（毫秒）。"""
        return self._current_interval

    def record_event(self) -> None:
        """记录一个事件（用于调整轮询频率）。"""
        self._last_event_time = time.time()
        self._event_count += 1
        self._total_events += 1

    def record_check(self) -> None:
        """记录一次轮询检查。"""
        self._total_checks += 1

    def update_interval(self) -> int:
        """更新并返回新的轮询间隔。

        调整策略：
        1. 如果最近有事件，降低间隔（更快响应）
        2. 如果长时间无事件，增加间隔（节省资源）
        3. 夜间时段自动降低频率

        Returns:
            新的轮询间隔（毫秒）。
        """
        now = time.time()
        time_since_last_event = now - self._last_event_time if self._last_event_time else 60

        # 计算目标间隔
        if time_since_last_event < 5:
            # 最近 5 秒内有事件，使用最小间隔
            target_interval = self.min_interval
        elif time_since_last_event < 30:
            # 最近 30 秒内有事件，使用基础间隔
            target_interval = self.base_interval
        elif time_since_last_event < 300:
            # 最近 5 分钟内有事件，稍微增加间隔
            target_interval = self.base_interval * 2
        else:
            # 长时间无事件，使用最大间隔
            target_interval = self.max_interval

        # 夜间时段（22:00 - 06:00）额外增加间隔
        hour = time.localtime().tm_hour
        if 22 <= hour or hour < 6:
            target_interval = min(target_interval * 2, self.max_interval)

        # 平滑调整（避免频繁变化）
        if abs(target_interval - self._current_interval) > 100:
            # 差异较大时，逐步调整
            if target_interval > self._current_interval:
                self._current_interval = min(
                    self._current_interval + 200,
                    target_interval,
                )
            else:
                self._current_interval = max(
                    self._current_interval - 200,
                    target_interval,
                )
            self._interval_changes += 1

        self._last_adjust_time = now
        return self._current_interval

    def get_stats(self) -> dict:
        """获取性能统计信息。"""
        return {
            "current_interval_ms": self._current_interval,
            "total_checks": self._total_checks,
            "total_events": self._total_events,
            "interval_changes": self._interval_changes,
            "avg_events_per_check": (
                self._total_events / self._total_checks
                if self._total_checks > 0
                else 0
            ),
        }

    def reset(self) -> None:
        """重置为默认状态。"""
        self._current_interval = self.base_interval
        self._last_event_time = 0
        self._event_count = 0
        self._last_adjust_time = time.time()
