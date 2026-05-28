"""日志配置 — 统一的 logging 设置，所有模块通过 get_logger() 获取 logger。

日志文件: ~/.agent-notify/agent-notify.log
轮转策略: 5 个文件，每个最大 1MB
崩溃日志: ~/.agent-notify/crash.log
"""

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from constants import SIGNAL_DIR

_LOG_DIR = SIGNAL_DIR
_LOG_FILE = _LOG_DIR / "agent-notify.log"
_CRASH_FILE = _LOG_DIR / "crash.log"
_initialized = False


def _init() -> None:
    """初始化根 logger（仅执行一次）。"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("agent_notify")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件 handler（轮转）
    fh = RotatingFileHandler(
        _LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # stderr handler（WARNING 以上，开发时可见）
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    # 全局异常钩子 — 写入 crash.log
    sys.excepthook = _crash_hook


def _crash_hook(exc_type, exc_value, exc_tb):
    """未处理异常 → 写入 crash.log + 原始 stderr。"""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        with open(_CRASH_FILE, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"\n{'='*60}\n")
            f.write(f"Crash at {datetime.datetime.now().isoformat()}\n")
            f.write(tb)
    except OSError:
        pass
    # 仍然输出到 stderr
    sys.stderr.write(tb)


def check_crash_log() -> str | None:
    """检查是否存在上次崩溃日志。有则返回内容摘要并删除文件，无则返回 None。"""
    if not _CRASH_FILE.exists():
        return None
    try:
        content = _CRASH_FILE.read_text(encoding="utf-8").strip()
        _CRASH_FILE.unlink()
        if content:
            # 取最后 500 字符作为摘要
            return content[-500:] if len(content) > 500 else content
    except OSError:
        pass
    return None


def get_logger(name: str) -> logging.Logger:
    """获取子 logger。首次调用时自动初始化根 logger。

    Args:
        name: logger 名称，通常传 __name__。

    Returns:
        logging.Logger 实例。
    """
    _init()
    return logging.getLogger(f"agent_notify.{name}")
