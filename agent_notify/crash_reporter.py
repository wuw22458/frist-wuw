"""崩溃报告 — 捕获未处理异常并写入 crash.log.

在 main.py 中通过 sys.excepthook 和 Qt 信号安装全局处理器.
崩溃日志包含 traceback、系统信息、最近 N 行应用日志.
"""

import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

from constants import SIGNAL_DIR, __version__
from log import get_logger

logger = get_logger('crash')

# 崩溃日志路径
CRASH_LOG = SIGNAL_DIR / 'crash.log'
# 应用日志路径
APP_LOG = SIGNAL_DIR / 'agent-notify.log'
SEPARATOR = '=' * 80
# 附带的应用日志行数
_TAIL_LOG_LINES = 30


def _collect_system_info() -> dict:
    """收集系统信息用于崩溃报告."""
    return {
        'os': f'{platform.system()} {platform.release()} ({platform.version()})',
        'python': sys.version,
        'app_version': __version__,
        'frozen': getattr(sys, 'frozen', False),
    }


def _tail_file(path: Path, lines: int) -> str:
    """读取文件末尾 N 行."""
    if not path.exists():
        return '(日志文件不存在)'
    try:
        content = path.read_text(encoding='utf-8', errors='replace')
        all_lines = content.splitlines()
        return '\n'.join(all_lines[-lines:])
    except Exception:
        return '(无法读取日志文件)'


def write_crash_report(exc_type, exc_value, exc_tb) -> str:
    """写入崩溃报告到 crash.log.

    Returns:
        崩溃日志的绝对路径,供 UI 展示.
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

    sys_info = _collect_system_info()
    app_log_tail = _tail_file(APP_LOG, _TAIL_LOG_LINES)

    report = f"""\
{SEPARATOR}
崩溃时间: {now}
应用版本: {sys_info['app_version']}
打包模式: {sys_info['frozen']}
操作系统: {sys_info['os']}
Python:    {sys_info['python']}
{SEPARATOR}

Traceback:
{tb_str}
{SEPARATOR}
最近 {_TAIL_LOG_LINES} 行应用日志:
{app_log_tail}
{SEPARATOR}
"""

    try:
        SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
        # 轮转：超过 5 个报告块时删除最早的一个
        existing = ''
        if CRASH_LOG.exists():
            existing = CRASH_LOG.read_text(encoding='utf-8', errors='replace')
        combined = report + existing
        # 按分隔符分割报告块
        blocks = combined.split(SEPARATOR)
        # 保留最多 5 个完整报告块（包括分隔符）
        if len(blocks) > 5 * 2:  # 每个块有前后两个分隔符
            blocks = blocks[: 5 * 2]
            combined = SEPARATOR.join(blocks) + SEPARATOR
        CRASH_LOG.write_text(combined, encoding='utf-8')
        return str(CRASH_LOG)
    except OSError:
        return ''


def has_crash_report() -> bool:
    """检查是否存在未读的崩溃报告."""
    return CRASH_LOG.exists() and CRASH_LOG.stat().st_size > 0


def read_crash_report() -> str | None:
    """读取最新的崩溃报告(第一个报告块)."""
    if not CRASH_LOG.exists():
        return None
    try:
        content = CRASH_LOG.read_text(encoding='utf-8', errors='replace')
        # 跳过文件开头可能的分隔符
        start = len(SEPARATOR) + 1 if content.startswith(SEPARATOR) else 0
        # 查找下一个报告的开始标记（下一个 SEPARATOR + 崩溃时间）
        next_report = content.find(f'{SEPARATOR}\n崩溃时间:', start + 10)
        if next_report > 0:
            return content[start:next_report].strip()
        return content[start:].strip()
    except OSError:
        return None


def clear_crash_report() -> None:
    """清除崩溃报告文件."""
    try:
        if CRASH_LOG.exists():
            CRASH_LOG.unlink()
    except OSError:
        pass


def install_crash_handler() -> None:
    """安装全局异常处理器.

    捕获 Python 层和 Qt 层的未处理异常,写入崩溃日志.
    应在 QApplication 创建后调用.
    """

    def _excepthook(exc_type, exc_value, exc_tb):
        crash_path = write_crash_report(exc_type, exc_value, exc_tb)
        logger.critical('未处理异常，崩溃日志已写入: %s', crash_path)
        # 调用默认处理器（打印到 stderr）
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    # 捕获 Qt 层的未处理异常
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler

        def _qt_message_handler(msg_type, context, message):
            if msg_type in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                logger.error(
                    'Qt 错误 [%s]: %s (context: %s)',
                    msg_type.name,
                    message,
                    context,
                )
                # Qt Fatal 写入崩溃日志
                if msg_type == QtMsgType.QtFatalMsg:
                    write_crash_report(
                        RuntimeError,
                        RuntimeError(f'Qt Fatal: {message}'),
                        None,
                    )

        qInstallMessageHandler(_qt_message_handler)
    except ImportError:
        pass
