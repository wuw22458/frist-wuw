"""Agent Notify — 通用 AI Agent 状态通知工具

系统托盘应用，当 Claude Code、Cursor、Aider 等 AI agent 需要权限确认或任务完成时，
通过系统通知 + 声音提醒用户。

用法：
  python main.py                 # 启动托盘应用
  python main.py --install-hooks # 自动配置 Claude Code hooks
  python main.py --auto-start    # 设置开机自启动
"""

import argparse
import sys

from autostart import is_autostart_enabled, set_autostart
from constants import __version__, migrate_from_old_path
from crash_reporter import install_crash_handler
from event_bus import get_bus
from hook_utils import install_hooks, uninstall_hooks
from lock_utils import check_single_instance, cleanup_lock
from log import get_logger
from notification_engine import NotificationEngine
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from settings import load_config
from ui.tray import TrayApp

logger = get_logger("main")


def main() -> None:
    """入口函数 — 解析 CLI 参数后启动托盘应用或执行工具命令。"""
    parser = argparse.ArgumentParser(
        description="Agent Notify — 通用 AI Agent 状态通知工具"
    )
    parser.add_argument(
        "--version", action="version", version=f"Agent Notify {__version__}"
    )
    parser.add_argument(
        "--install-hooks", action="store_true", help="自动配置 Claude Code hooks"
    )
    parser.add_argument(
        "--uninstall-hooks", action="store_true", help="移除 Claude Code hooks 配置"
    )
    parser.add_argument("--auto-start", action="store_true", help="设置开机自启动")
    parser.add_argument("--no-auto-start", action="store_true", help="取消开机自启动")
    args = parser.parse_args()

    if args.install_hooks:
        if install_hooks():
            print("Hooks 已配置完成（Notification + Stop + PreToolUse）")
        return

    if args.uninstall_hooks:
        uninstall_hooks()
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

    # 安装崩溃处理器（覆盖 log.py 的基础 excepthook）
    install_crash_handler()

    # ── 启动 Splash Screen ──
    from ui.splash import AnimatedSplash

    splash = AnimatedSplash(__version__)
    splash.show_animated(1200)
    app.processEvents()

    # ── 首次运行向导 ──
    from ui.wizard import SetupWizard, mark_wizard_completed, should_run_wizard

    if should_run_wizard(config):
        wizard = SetupWizard()
        wizard.exec()
        config = load_config()

    # ── EventBus + Adapter 初始化 ──
    bus = get_bus()

    from adapters import AdapterRegistry  # noqa: F811

    adapter_defaults = AdapterRegistry.get_default_config()
    for key, val in adapter_defaults.items():
        if key not in config:
            config[key] = val

    first_run = not any(k.startswith("source_") for k in config)
    if first_run:
        for cls in AdapterRegistry.get_all_classes():
            key = f"source_{cls.agent_id}"
            if key not in config:
                try:
                    config[key] = cls.detect()
                except Exception:
                    config[key] = True
        from settings import save_config

        save_config(config)
        mark_wizard_completed()
        logger.info("[auto-detect] 已扫描已安装的 agent")

    adapters = AdapterRegistry.create_enabled(bus, config)
    for adapter in adapters:
        try:
            adapter.start()
            logger.info("[+] %s: %s", adapter.display_name, adapter.description)
        except Exception as e:
            logger.error("[!] %s 启动失败: %s", adapter.display_name, e)

    # ── TrayApp + 通知引擎 ──
    tray = TrayApp(bus, config=config)
    tray.set_adapters(adapters)
    tray.show()

    engine = NotificationEngine()
    bus.event_received.connect(
        lambda event: engine.handle_event(event, tray.get_config())
    )

    def _on_pause(is_paused):
        engine.pause(is_paused)
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
