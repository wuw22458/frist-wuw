"""Agent Notify — 通用 AI Agent 状态通知工具

系统托盘应用，当 Claude Code、Cursor、Aider 等 AI agent 需要权限确认或任务完成时，
通过系统通知 + 声音提醒用户。

用法：
  python main.py                 # 启动托盘应用
  python main.py --install-hooks # 自动配置 Claude Code hooks
  python main.py --auto-start    # 设置开机自启动
"""

import argparse
import json
import sys
import shutil
import time
import winreg
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor, QPalette

from tray_app import TrayApp
from notification import notify
from settings import load_config
from constants import SIGNAL_DIR, APP_NAME, REGISTRY_KEY, migrate_from_old_path, __version__
from lock_utils import check_single_instance, cleanup_lock
from event_bus import EventBus, get_bus
from log import get_logger

logger = get_logger("main")


def get_exe_path() -> str:
    """获取当前 exe 或脚本路径（打包模式返回 exe 路径，开发模式返回脚本路径）"""
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(__file__).resolve())


def set_autostart(enable: bool = True) -> None:
    """设置/取消开机自启动（通过 Windows 注册表 Run 键）。"""
    exe_path = get_exe_path()
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            cmd = f'"{exe_path}"'
            if not exe_path.endswith(".exe"):
                cmd = f'"{sys.executable}" "{exe_path}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            logger.info("已设置开机自启: %s", cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("已取消开机自启")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError as e:
        logger.error("设置开机自启失败: %s", e)


def is_autostart_enabled() -> bool:
    """检查是否已设置开机自启"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def install_hooks():
    """自动配置 Claude Code hooks（将 hook 脚本写入 ~/.claude/settings.json）"""
    settings_path = Path.home() / ".claude" / "settings.json"

    if getattr(sys, "frozen", False):
        bundled_hook = Path(sys._MEIPASS) / "hooks" / "claude_hook.py"
        hook_dest = SIGNAL_DIR / "hooks" / "claude_hook.py"
        hook_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled_hook, hook_dest)
        hook_script = hook_dest
    else:
        hook_script = Path(__file__).parent / "hooks" / "claude_hook.py"

    config = {}
    if settings_path.exists():
        try:
            config = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取 Claude Code settings 失败: %s", e)

    hooks = config.get("hooks", {})
    python_exe = f'"{sys.executable}"'
    hooks["Notification"] = [
        {
            "type": "command",
            "command": f'{python_exe} "{hook_script}" --event notification',
        }
    ]
    hooks["Stop"] = [
        {
            "type": "command",
            "command": f'{python_exe} "{hook_script}" --event stop',
        }
    ]
    config["hooks"] = hooks

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Hooks 已配置到 %s", settings_path)


def main() -> None:
    """入口函数 — 解析 CLI 参数后启动托盘应用或执行工具命令。"""
    parser = argparse.ArgumentParser(description="Agent Notify — 通用 AI Agent 状态通知工具")
    parser.add_argument("--install-hooks", action="store_true", help="自动配置 Claude Code hooks")
    parser.add_argument("--auto-start", action="store_true", help="设置开机自启动")
    parser.add_argument("--no-auto-start", action="store_true", help="取消开机自启动")
    args = parser.parse_args()

    if args.install_hooks:
        install_hooks()
        return

    if args.auto_start:
        set_autostart(True)
        return

    if args.no_auto_start:
        set_autostart(False)
        return

    # 旧版数据迁移（首次启动时自动执行）
    migrate_from_old_path()

    # 单实例检查
    if not check_single_instance():
        logger.info("Agent Notify 已在运行中，退出")
        sys.exit(0)

    # 自动设置开机自启
    config = load_config()
    if config.get("auto_start", True) and not is_autostart_enabled():
        set_autostart(True)

    # 初始化 Qt 应用
    app = QCoreApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Fusion 样式 + 暗色 Palette
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(13, 17, 23))
    palette.setColor(QPalette.WindowText, QColor(240, 243, 246))
    palette.setColor(QPalette.Base, QColor(22, 27, 34))
    palette.setColor(QPalette.AlternateBase, QColor(48, 54, 61))
    palette.setColor(QPalette.Text, QColor(240, 243, 246))
    palette.setColor(QPalette.Button, QColor(48, 54, 61))
    palette.setColor(QPalette.ButtonText, QColor(240, 243, 246))
    palette.setColor(QPalette.Highlight, QColor(88, 166, 255))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    app.setStyleSheet("""
        QToolTip {
            background-color: #161b22;
            color: #e0e7ff;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
        }
    """)

    # ── EventBus + Adapter 初始化 ──
    bus = get_bus()

    # 导入 adapters 包触发所有 @register_adapter 注册
    from adapters import AdapterRegistry  # noqa: F811

    # 收集 adapter 默认配置并与用户配置合并
    adapter_defaults = AdapterRegistry.get_default_config()
    for key, val in adapter_defaults.items():
        if key not in config:
            config[key] = val

    # 首次运行：自动检测已安装的 agent 并预填配置
    first_run = not any(k.startswith("source_") for k in config)
    if first_run:
        for cls in AdapterRegistry.get_all_classes():
            key = f"source_{cls.agent_id}"
            if key not in config:
                try:
                    config[key] = cls.detect()
                except Exception:
                    config[key] = True  # 检测失败时默认启用
        from settings import save_config
        save_config(config)
        logger.info("[auto-detect] 已扫描已安装的 agent")

    # 实例化并启动所有启用的 adapter
    adapters = AdapterRegistry.create_enabled(bus, config)
    for adapter in adapters:
        adapter.start()
        logger.info("[+] %s: %s", adapter.display_name, adapter.description)

    # ── TrayApp + 通知引擎 ──
    tray = TrayApp(bus)
    tray.set_adapters(adapters)
    tray.show()

    # 通知引擎：EventBus → 声音 + Toast（含节流 + 免打扰）
    _last_notif: dict[str, float] = {}  # key → timestamp，用于去重
    _THROTTLE_SEC = 3  # 同一事件 3 秒内不重复通知

    def _is_dnd_active(cfg: dict) -> bool:
        """检查当前是否在免打扰时段内。"""
        if not cfg.get("dnd_enabled", False):
            return False
        now = time.strftime("%H:%M")
        start = cfg.get("dnd_start", "22:00")
        end = cfg.get("dnd_end", "08:00")
        if start <= end:
            return start <= now < end
        return now >= start or now < end

    def _on_event(event):
        if tray.is_paused:
            logger.debug("已暂停，忽略事件: %s", event.message[:60])
            return
        cfg = tray.get_config()

        # 免打扰检查
        if _is_dnd_active(cfg):
            logger.debug("免打扰时段，忽略事件: %s", event.message[:60])
            return

        # 节流：同一 agent + event_type 组合在 N 秒内不重复通知
        dedup_key = f"{event.agent_id}:{event.event_type}"
        now = time.monotonic()
        last = _last_notif.get(dedup_key, 0)
        if now - last < _THROTTLE_SEC:
            logger.debug("节流抑制: %s (%.1fs)", dedup_key, now - last)
            return
        _last_notif[dedup_key] = now

        title_map = {
            "waiting": "需要确认",
            "completed": "任务完成",
            "error": "出错了",
            "info": "通知",
        }
        title = title_map.get(event.event_type, "Agent Notify")
        if cfg.get("toast_enabled", True):
            notify(
                title, event.message,
                sound=cfg.get("sound_enabled", True),
                source=event.agent_id,
                sound_path=cfg.get("custom_sound", ""),
            )

    bus.event_received.connect(_on_event)

    # 暂停信号：暂停/恢复所有 adapter
    def _on_pause(is_paused):
        if is_paused:
            for a in adapters:
                a.stop()
        else:
            for a in adapters:
                a.start()

    tray.pause_toggled.connect(_on_pause)

    app.aboutToQuit.connect(cleanup_lock)
    app.aboutToQuit.connect(AdapterRegistry.stop_all)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
