"""日志配置 — 统一的 logging 设置,所有模块通过 get_logger() 获取 logger.

日志文件: ~/.agent-notify/agent-notify.log
轮转策略: 5 个文件,每个最大 1MB
崩溃日志由 crash_reporter.py 统一处理.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from constants import SIGNAL_DIR

_LOG_DIR = SIGNAL_DIR
_LOG_FILE = _LOG_DIR / 'agent-notify.log'
_initialized = False


def _init() -> None:
    """初始化根 logger(仅执行一次)."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger('agent_notify')
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)-7s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # 文件 handler（轮转）
    fh = RotatingFileHandler(_LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # stderr handler（WARNING 以上，开发时可见）
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)
    root.addHandler(sh)


def get_logger(name: str) -> logging.Logger:
    """获取子 logger.首次调用时自动初始化根 logger.

    Args:
        name: logger 名称,通常传 __name__.

    Returns:
        logging.Logger 实例.
    """
    _init()
    return logging.getLogger(f'agent_notify.{name}')
