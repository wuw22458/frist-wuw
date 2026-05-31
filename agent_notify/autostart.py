"""开机自启管理 — Windows 注册表 Run 键操作.

独立模块,供 main.py 和 ui/settings.py 共用.
"""

import sys
import winreg
from pathlib import Path

from constants import APP_NAME, REGISTRY_KEY
from log import get_logger

logger = get_logger('autostart')


def get_exe_path() -> str:
    """获取当前 exe 或脚本路径."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return str(Path(__file__).resolve().parent / 'main.py')


def set_autostart(enable: bool = True) -> None:
    """设置/取消开机自启动(通过 Windows 注册表 Run 键)."""
    exe_path = get_exe_path()
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            cmd = f'"{exe_path}"'
            if not exe_path.endswith('.exe'):
                cmd = f'"{sys.executable}" "{exe_path}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            logger.info('已设置开机自启: %s', cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info('已取消开机自启')
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError as e:
        logger.error('设置开机自启失败: %s', e)


def is_autostart_enabled() -> bool:
    """检查是否已设置开机自启."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False
