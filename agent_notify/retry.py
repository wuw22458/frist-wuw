"""重试机制 — 为关键操作提供自动重试功能."""

import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from log import get_logger

logger = get_logger('retry')

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """重试装饰器.

    Args:
        max_attempts: 最大尝试次数(包含首次调用).
        delay: 首次重试延迟(秒).
        backoff: 延迟倍增系数.
        exceptions: 需要重试的异常类型.

    Returns:
        装饰后的函数.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            '%s 第 %d 次尝试失败: %s，%.1f 秒后重试',
                            func.__name__,
                            attempt + 1,
                            e,
                            current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            '%s 所有 %d 次尝试均失败: %s',
                            func.__name__,
                            max_attempts,
                            e,
                        )

            raise last_exception

        return wrapper

    return decorator


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """异步重试装饰器(用于 QThread 等场景).

    Args:
        max_attempts: 最大尝试次数(包含首次调用).
        delay: 首次重试延迟(秒).
        backoff: 延迟倍增系数.
        exceptions: 需要重试的异常类型.

    Returns:
        装饰后的函数.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            '%s 第 %d 次尝试失败: %s，%.1f 秒后重试',
                            func.__name__,
                            attempt + 1,
                            e,
                            current_delay,
                        )
                        # 使用 Qt 的延迟机制（如果可用）
                        try:
                            from PySide6.QtCore import QThread

                            QThread.msleep(int(current_delay * 1000))
                        except ImportError:
                            time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            '%s 所有 %d 次尝试均失败: %s',
                            func.__name__,
                            max_attempts,
                            e,
                        )

            raise last_exception

        return wrapper

    return decorator
