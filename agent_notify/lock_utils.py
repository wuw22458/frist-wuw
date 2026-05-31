"""进程锁工具 — 基于 Windows Mutex 的单实例保证。

使用 kernel32.CreateMutexW 实现原子性单实例检查，避免 PID 文件的 TOCTOU 竞态条件。
Mutex 是内核对象，进程退出时自动释放，无需手动清理。

优势：
1. 原子性操作，无竞态条件
2. 进程崩溃后自动释放（内核对象生命周期管理）
3. 无需写入文件系统
"""

import ctypes
import ctypes.wintypes
from typing import Optional

# Windows API 常量
ERROR_ALREADY_EXISTS = 183
ERROR_SUCCESS = 0
SYNCHRONIZE = 0x00100000
MUTEX_ALL_ACCESS = 0x001F0001

# 全局 Mutex 句柄（防止被垃圾回收）
_mutex_handle: Optional[int] = None


def _get_kernel32():
    """获取 kernel32.dll 实例。"""
    return ctypes.windll.kernel32


def check_single_instance() -> bool:
    """检查是否已有实例在运行，如果没有则创建 Mutex。

    使用 CreateMutexW 创建命名 Mutex：
    - 如果 Mutex 已存在（ERROR_ALREADY_EXISTS），返回 False
    - 如果创建成功，返回 True

    Returns:
        True 表示当前是唯一实例，False 表示已有实例在运行。
    """
    global _mutex_handle

    kernel32 = _get_kernel32()

    # 创建命名 Mutex（全局唯一）
    # 名称格式：Local\AgentNotify_<version>
    # 使用 Local 前缀确保在当前会话中唯一
    from constants import __version__
    mutex_name = f"Local\\AgentNotify_{__version__.replace('.', '_')}"

    try:
        _mutex_handle = kernel32.CreateMutexW(
            None,      # 安全属性
            False,     # 初始所有者
            mutex_name # Mutex 名称
        )

        if _mutex_handle == 0:
            # CreateMutexW 失败
            return True

        # 检查是否已存在
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            # 已有实例在运行
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
            return False

        # 成功创建，当前是唯一实例
        return True

    except Exception:
        # 异常情况下允许启动（降级处理）
        _mutex_handle = None
        return True


def cleanup_lock() -> None:
    """释放 Mutex 句柄（应用退出时调用，通过 aboutToQuit 信号触发）。

    注意：进程退出时内核会自动释放 Mutex，此函数主要用于显式清理。
    """
    global _mutex_handle

    if _mutex_handle is not None:
        try:
            kernel32 = _get_kernel32()
            kernel32.CloseHandle(_mutex_handle)
        except Exception:
            pass
        _mutex_handle = None


def is_process_running(pid: int) -> bool:
    """检查指定 PID 的进程是否存活（Windows 专用）。

    保留此函数以兼容其他模块可能的调用，但不再用于单实例检查。

    Args:
        pid: 要检查的进程 ID。

    Returns:
        True 表示进程存在，False 表示不存在或无法查询。
    """
    try:
        kernel32 = _get_kernel32()
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        # WaitForSingleObject(timeout=0) 立即返回：
        # - WAIT_OBJECT_0 (0): 进程已终止
        # - WAIT_TIMEOUT (258): 进程仍在运行
        result = kernel32.WaitForSingleObject(handle, 0)
        kernel32.CloseHandle(handle)
        return result == 258  # WAIT_TIMEOUT = 进程存活
    except (ValueError, OSError):
        return False
