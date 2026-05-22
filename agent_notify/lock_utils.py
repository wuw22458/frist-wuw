"""进程锁工具 — 基于 PID 文件的单实例保证。

通过在 ~/.agent-notify/.lock 写入当前 PID，
启动时检测该 PID 对应的进程是否存活，防止重复启动。

使用 Windows kernel32.OpenProcess 而非 os.kill，因为：
1. 不会向目标进程发送信号
2. 仅查询进程是否存在，权限最小化
"""

import ctypes
import os
from constants import LOCK_FILE, PROCESS_QUERY_LIMITED_INFORMATION


def is_process_running(pid: int) -> bool:
    """检查指定 PID 的进程是否存活（Windows 专用）。

    通过 kernel32.OpenProcess 以最低权限查询进程状态，
    查询失败（权限不足/PID 不存在）统一返回 False。

    Args:
        pid: 要检查的进程 ID。

    Returns:
        True 表示进程存在，False 表示不存在或无法查询。
    """
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
    except (ValueError, OSError):
        pass
    return False


def check_single_instance() -> bool:
    """检查是否已有实例在运行，如果没有则写入当前 PID 的锁文件。

    读取锁文件中的 PID 并检查其对应进程是否存活：
    - 存活 → 返回 False（已有实例）
    - 不存在/文件损坏 → 写入当前 PID，返回 True（当前是唯一实例）

    Returns:
        True 表示当前是唯一实例（锁文件已写入），False 表示已有实例在运行。
    """
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if is_process_running(pid):
                return False
        except (ValueError, OSError):
            pass

    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def cleanup_lock() -> None:
    """删除锁文件（应用退出时调用，通过 aboutToQuit 信号触发）。"""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass
