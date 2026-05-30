"""共享常量 — 集中管理路径、配置默认值和 Windows API 常量。

所有模块通过 import 复用这些常量，避免硬编码重复。
目录布局:
    ~/.agent-notify/
    ├── .lock           # PID 锁文件
    ├── config.json     # 用户配置
    ├── *.json          # 信号文件（由各 agent hook 写入，adapter 读取后删除）
    └── hooks/          # 打包模式下 hook 脚本的安装位置
"""

import shutil
from pathlib import Path

__version__ = "1.2.1"

# ── 路径（解耦自 ~/.claude，使用独立的 ~/.agent-notify）──
SIGNAL_DIR = Path.home() / ".agent-notify"
LOCK_FILE = SIGNAL_DIR / ".lock"
CONFIG_FILE = SIGNAL_DIR / "config.json"
HISTORY_FILE = SIGNAL_DIR / "history.json"

# 旧版路径（用于迁移）
_OLD_SIGNAL_DIR = Path.home() / ".claude" / "agent-notify"

# ── Windows 注册表 ──
APP_NAME = "AgentNotify"
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Windows API 常量 — OpenProcess 所需的最低权限
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# ── 基础默认配置（adapter 无关的全局配置）──
DEFAULT_CONFIG = {
    "sound_enabled": True,  # 播放提示音
    "toast_enabled": True,  # 显示系统通知
    "auto_start": True,  # 开机自启动
    "max_history": 200,  # 已处理信号记录上限
    "custom_sound": "",  # 自定义提示音路径（为空使用默认）
    "dnd_enabled": False,  # 免打扰模式
    "dnd_start": "22:00",  # 免打扰开始时间
    "dnd_end": "08:00",  # 免打扰结束时间
}

# ── 迁移逻辑 ──


def migrate_from_old_path() -> None:
    """首次启动时检测旧路径 ~/.claude/agent-notify/，自动迁移数据到新路径。"""
    if not _OLD_SIGNAL_DIR.exists():
        return
    if SIGNAL_DIR.exists():
        # 新路径已存在，不覆盖
        return

    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

    # 迁移 config.json
    old_config = _OLD_SIGNAL_DIR / "config.json"
    if old_config.exists():
        shutil.copy2(old_config, CONFIG_FILE)

    # 迁移 hooks 目录
    old_hooks = _OLD_SIGNAL_DIR / "hooks"
    if old_hooks.exists():
        new_hooks = SIGNAL_DIR / "hooks"
        shutil.copytree(old_hooks, new_hooks, dirs_exist_ok=True)

    # 迁移 .lock 文件不复制（新实例会重新创建）
    # 信号文件也不迁移（已经是历史数据）
