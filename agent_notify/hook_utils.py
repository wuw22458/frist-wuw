"""hook_utils.py — Claude Code hooks 的安装与卸载。

从 main.py 和 wizard.py 中抽取，避免循环依赖。
"""

import json
import shutil
import sys
from pathlib import Path

from constants import SIGNAL_DIR
from log import get_logger

logger = get_logger("hook_utils")

# 需要注册的 hooks 列表
_HOOK_KEYS = ("Notification", "Stop", "PreToolUse")

# 每个 hook 对应的 --event 参数
_HOOK_EVENTS = {
    "Notification": "notification",
    "Stop": "stop",
    "PreToolUse": "permission",
}


def _get_hook_script_path() -> Path:
    """获取 claude_hook.py 的路径（区分打包和开发模式）。"""
    if getattr(sys, "frozen", False):
        bundled_hook = Path(sys._MEIPASS) / "hooks" / "claude_hook.py"
        hook_dest = SIGNAL_DIR / "hooks" / "claude_hook.py"
        hook_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled_hook, hook_dest)
        return hook_dest
    return Path(__file__).parent / "hooks" / "claude_hook.py"


def _load_settings() -> tuple[Path, dict]:
    """加载 ~/.claude/settings.json，返回 (路径, 配置字典)。"""
    settings_path = Path.home() / ".claude" / "settings.json"
    config = {}
    if settings_path.exists():
        try:
            config = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取 Claude Code settings 失败: %s", e)
    return settings_path, config


def _save_settings(settings_path: Path, config: dict) -> bool:
    """保存配置到 settings.json，返回是否成功。"""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        settings_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError as e:
        logger.error("写入 Claude Code settings 失败: %s", e)
        print(f"错误: 无法写入 {settings_path}: {e}", file=sys.stderr)
        return False


def install_hooks() -> bool:
    """自动配置 Claude Code hooks（将 hook 脚本写入 ~/.claude/settings.json）。

    注册三个 hook：
    - Notification: Agent 状态通知
    - Stop: 任务完成
    - PreToolUse: 需要用户选择/确认（如 AskUserQuestion）

    Returns:
        是否成功。
    """
    hook_script = _get_hook_script_path()
    settings_path, config = _load_settings()

    hooks = config.get("hooks", {})
    python_exe = f'"{sys.executable}"'

    for hook_key in _HOOK_KEYS:
        event = _HOOK_EVENTS[hook_key]
        hooks[hook_key] = [
            {
                "type": "command",
                "command": f'{python_exe} "{hook_script}" --event {event}',
            }
        ]

    config["hooks"] = hooks

    if _save_settings(settings_path, config):
        logger.info("Hooks 已配置到 %s", settings_path)
        return True
    return False


def uninstall_hooks() -> tuple[bool, list[str]]:
    """从 ~/.claude/settings.json 中移除 Agent Notify 的 hooks 配置。

    Returns:
        (是否成功, 已移除的 hook 名称列表)
    """
    settings_path, config = _load_settings()

    if not settings_path.exists():
        print("Claude Code settings 文件不存在，无需卸载")
        return True, []

    hooks = config.get("hooks", {})
    removed = []
    for key in _HOOK_KEYS:
        if key in hooks:
            del hooks[key]
            removed.append(key)

    if not removed:
        print("未找到 Agent Notify 的 hooks 配置")
        return True, []

    if not hooks:
        del config["hooks"]
    else:
        config["hooks"] = hooks

    if _save_settings(settings_path, config):
        print(f"已移除 hooks: {', '.join(removed)}")
        return True, removed
    return False, []
