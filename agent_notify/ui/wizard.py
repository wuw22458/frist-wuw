"""首次运行向导 — 引导用户完成初始配置。

向导步骤：
  1. 欢迎页 → 检测已安装的 Agent
  2. 选择要监控的 Agent
  3. 配置 Agent 集成（Claude Code hook 自动配置）
  4. 通知偏好（声音、Toast）
  5. 是否开机自启
  6. 完成页
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from constants import APP_NAME, SIGNAL_DIR
from log import get_logger
from settings import load_config, save_config

logger = get_logger("wizard")

# ── 样式常量 ──
STYLE_WELCOME_TITLE = (
    "font-size: 22px; font-weight: bold; color: #e0e0e0; margin-bottom: 8px;"
)
STYLE_SUBTITLE = "font-size: 13px; color: #909090; line-height: 1.4;"
STYLE_CHECKBOX = """
    QCheckBox { font-size: 13px; color: #c0c0c0; spacing: 8px; }
    QCheckBox::indicator { width: 18px; height: 18px; }
"""
STYLE_RADIO = """
    QRadioButton { font-size: 13px; color: #c0c0c0; spacing: 8px; }
    QRadioButton::indicator { width: 16px; height: 16px; }
"""


class WelcomePage(QWizardPage):
    """步骤 1：欢迎页 & 自动检测。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")
        self._detected: dict[str, bool] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 30, 30, 20)

        title = QLabel(f"欢迎使用 {APP_NAME}")
        title.setStyleSheet(STYLE_WELCOME_TITLE)
        layout.addWidget(title)

        desc = QLabel(
            "Agent Notify 帮你实时监控 AI Agent（Cursor、Claude Code 等）的通知事件，"
            "通过 Windows Toast 弹窗提醒，再也不错过 AI 的任务完成。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(STYLE_SUBTITLE)
        layout.addWidget(desc)

        detect_frame = QGroupBox("自动检测已安装的 Agent")
        detect_frame.setStyleSheet(
            "QGroupBox { font-size: 13px; color: #b0b0b0;"
            " border: 1px solid #404040; border-radius: 6px;"
            " margin-top: 14px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " left: 12px; padding: 0 6px; }"
        )
        detect_layout = QVBoxLayout()
        detect_layout.setSpacing(6)
        detect_layout.setContentsMargins(12, 12, 12, 12)

        progress = QLabel("正在检测...")
        progress.setStyleSheet("color: #808080; font-size: 12px;")
        detect_layout.addWidget(progress)
        detect_frame.setLayout(detect_layout)
        layout.addWidget(detect_frame)

        layout.addStretch()
        hint = QLabel("点击「下一步」开始配置")
        hint.setStyleSheet("color: #606060; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hint)

        self.setLayout(layout)
        self._progress_label = progress
        self._detect_layout = detect_layout
        self._detect_frame = detect_frame

    def initializePage(self):
        """当进入此页面时自动检测 Agent。"""
        from adapters.registry import AdapterRegistry

        for cls in AdapterRegistry.get_all_classes():
            try:
                self._detected[cls.agent_id] = cls.detect()
            except Exception:
                self._detected[cls.agent_id] = False

        # 清除旧检测结果
        while self._detect_layout.count():
            item = self._detect_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._detected:
            not_found = QLabel("未检测到任何已安装的 AI Agent")
            not_found.setStyleSheet("color: #707070; font-size: 12px;")
            self._detect_layout.addWidget(not_found)
            return

        agent_names = {
            "claude-code": "Claude Code",
            "cursor": "Cursor",
            "windsurf": "Windsurf / Cascade",
            "aider": "Aider",
        }

        for key, installed in self._detected.items():
            row = QHBoxLayout()
            name = QLabel(agent_names.get(key, key))
            name.setStyleSheet("font-size: 12px; color: #c0c0c0;")
            row.addWidget(name)
            row.addStretch()
            status = QLabel("已检测到" if installed else "未安装")
            status.setStyleSheet(
                "font-size: 11px; color: #4ecf6e;" if installed
                else "font-size: 11px; color: #606060;"
            )
            row.addWidget(status)
            self._detect_layout.addLayout(row)

    @property
    def detected(self) -> dict[str, bool]:
        return self._detected


class SelectAgentsPage(QWizardPage):
    """步骤 2：选择要监控的 Agent。"""

    def __init__(self, welcome_page: WelcomePage, parent=None):
        super().__init__(parent)
        self._welcome = welcome_page
        self._checks: dict[str, QCheckBox] = {}
        self.setTitle("选择要监控的 Agent")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30, 24, 30, 20)

        hint = QLabel("勾选你希望接收通知的 AI Agent（可多选）")
        hint.setStyleSheet(STYLE_SUBTITLE)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        group = QGroupBox()
        group.setStyleSheet(
            "QGroupBox { border: 1px solid #404040;"
            " border-radius: 6px; padding: 10px; }"
        )
        group_layout = QVBoxLayout()
        group_layout.setSpacing(8)

        agent_labels = {
            "claude-code": "Claude Code — 命令行 AI 编码助手",
            "cursor": "Cursor — VS Code 风格 AI 编辑器",
            "windsurf": "Windsurf — AI Flow 编码 IDE",
            "aider": "Aider — 终端 AI 结对编程",
        }

        for key, label in agent_labels.items():
            cb = QCheckBox(label)
            cb.setStyleSheet(STYLE_CHECKBOX)
            detected = self._welcome.detected.get(key, False)
            if detected:
                cb.setChecked(True)
            cb.setEnabled(detected)
            group_layout.addWidget(cb)
            self._checks[key] = cb

        group.setLayout(group_layout)
        layout.addWidget(group)

        layout.addStretch()
        self.setLayout(layout)

    @property
    def selected_agents(self) -> dict[str, bool]:
        return {k: cb.isChecked() for k, cb in self._checks.items()}


class HookConfigPage(QWizardPage):
    """步骤 3：配置 Agent 集成（Claude Code hook 自动配置）。"""

    def __init__(self, select_page: SelectAgentsPage, parent=None):
        super().__init__(parent)
        self._select = select_page
        self.setTitle("配置 Agent 集成")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 24, 30, 20)

        hint = QLabel(
            "以下 Agent 支持深度集成，可以自动配置 Hook 实现实时通知。"
        )
        hint.setStyleSheet(STYLE_SUBTITLE)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Claude Code hook 配置
        self._claude_group = QGroupBox("Claude Code")
        self._claude_group.setStyleSheet(
            "QGroupBox { font-size: 13px; color: #b0b0b0;"
            " border: 1px solid #404040; border-radius: 6px;"
            " margin-top: 14px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " left: 12px; padding: 0 6px; }"
        )
        claude_layout = QVBoxLayout()
        claude_layout.setSpacing(8)
        claude_layout.setContentsMargins(12, 12, 12, 12)

        desc = QLabel(
            "自动将 Agent Notify 的 Hook 写入 Claude Code 的 settings.json，"
            "这样 Claude Code 在需要确认或任务完成时会自动发送通知。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #a0a0a0;")
        claude_layout.addWidget(desc)

        self._claude_hook_cb = QCheckBox("自动配置 Claude Code Hook（推荐）")
        self._claude_hook_cb.setStyleSheet(STYLE_CHECKBOX)
        self._claude_hook_cb.setChecked(True)
        claude_layout.addWidget(self._claude_hook_cb)

        hint2 = QLabel("💡 你也可以稍后在托盘菜单 → 设置中手动配置")
        hint2.setStyleSheet("font-size: 11px; color: #606060;")
        claude_layout.addWidget(hint2)

        self._claude_group.setLayout(claude_layout)
        layout.addWidget(self._claude_group)

        # 预留其他 Agent 集成的位置
        self._other_label = QLabel("其他 Agent 无需额外配置，会自动通过信号文件接收通知。")
        self._other_label.setStyleSheet("font-size: 12px; color: #707070; margin-top: 8px;")
        self._other_label.setWordWrap(True)
        layout.addWidget(self._other_label)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        """根据选择的 Agent 动态显示/隐藏配置项。"""
        selected = self._select.selected_agents
        claude_selected = selected.get("claude-code", False)
        self._claude_group.setVisible(claude_selected)
        if not claude_selected:
            self._other_label.setText("你选择的 Agent 无需额外配置，会自动通过信号文件接收通知。")
        else:
            self._other_label.setText(
                "其他 Agent 无需额外配置，会自动通过信号文件接收通知。"
            )

    @property
    def configure_claude_hook(self) -> bool:
        return self._claude_hook_cb.isChecked() and self._claude_group.isVisible()


class NotificationPrefsPage(QWizardPage):
    """步骤 4：通知偏好。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("通知偏好设置")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 24, 30, 20)

        hint = QLabel("你可以随时在托盘菜单的「设置」中调整")
        hint.setStyleSheet(STYLE_SUBTITLE)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._sound_cb = QCheckBox("播放提示音")
        self._sound_cb.setChecked(True)
        self._sound_cb.setStyleSheet(STYLE_CHECKBOX)
        layout.addWidget(self._sound_cb)

        self._toast_cb = QCheckBox("显示系统通知")
        self._toast_cb.setChecked(True)
        self._toast_cb.setStyleSheet(STYLE_CHECKBOX)
        layout.addWidget(self._toast_cb)

        layout.addStretch()
        self.setLayout(layout)

    @property
    def notify_sound(self) -> bool:
        return self._sound_cb.isChecked()

    @property
    def notify_toast(self) -> bool:
        return self._toast_cb.isChecked()


class AutostartPage(QWizardPage):
    """步骤 5：开机自启。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("开机自动启动")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 24, 30, 20)

        hint = QLabel(
            "建议开启，这样你每次开机后 Agent Notify 会自动运行，无需手动打开。"
        )
        hint.setStyleSheet(STYLE_SUBTITLE)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._autostart_yes = QRadioButton("开机自动启动（推荐）")
        self._autostart_no = QRadioButton("暂不开启，我手动打开")
        self._autostart_yes.setStyleSheet(STYLE_RADIO)
        self._autostart_no.setStyleSheet(STYLE_RADIO)
        self._autostart_yes.setChecked(True)
        layout.addWidget(self._autostart_yes)
        layout.addWidget(self._autostart_no)

        layout.addStretch()
        self.setLayout(layout)

    @property
    def autostart_enabled(self) -> bool:
        return self._autostart_yes.isChecked()


class FinishPage(QWizardPage):
    """步骤 6：完成。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

    def _setup_ui(self, selected: list[str], sound: bool, toast: bool, autostart: bool, hooks_configured: bool):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 30, 30, 20)

        title = QLabel("配置完成！")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ecf6e;")
        layout.addWidget(title)

        hook_status = "已自动配置" if hooks_configured else "未配置"
        summary = QLabel(
            f"监控 Agent：{', '.join(selected) if selected else '暂无'}\n"
            f"Claude Code Hook：{hook_status}\n"
            f"提示音：{'开启' if sound else '关闭'}\n"
            f"系统通知：{'开启' if toast else '关闭'}\n"
            f"开机自启：{'开启' if autostart else '关闭'}"
        )
        summary.setStyleSheet("font-size: 13px; color: #c0c0c0; line-height: 1.5;")
        layout.addWidget(summary)

        tip = QLabel("Agent Notify 已在系统托盘中运行，右键托盘图标可打开设置。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #808080; font-size: 12px; margin-top: 10px;")
        layout.addWidget(tip)

        layout.addStretch()
        self.setLayout(layout)

    def initializePage(self):
        wizard: SetupWizard = self.wizard()
        self._setup_ui(
            [k for k, v in wizard.selected_agents.items() if v],
            wizard.notify_sound,
            wizard.notify_toast,
            wizard.autostart_enabled,
            wizard.configure_claude_hook,
        )


class SetupWizard(QWizard):
    """引导式安装向导。"""

    STYLE_SHEET = """
        QWizard {
            background-color: #1e1e2e;
            color: #d0d0d0;
        }
        QWizard QLabel { color: #d0d0d0; }
        QWizard QPushButton {
            background-color: #3a3a5c;
            color: #e0e0e0;
            border: 1px solid #505070;
            border-radius: 4px;
            padding: 6px 18px;
            font-size: 12px;
        }
        QWizard QPushButton:hover { background-color: #4a4a7c; }
        QWizard QPushButton#qt_wizard_commit {
            background-color: #2563eb;
            border-color: #3b82f6;
        }
        QWizard QPushButton#qt_wizard_commit:hover { background-color: #3b82f6; }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — 初始配置")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(560, 440)
        self.setStyleSheet(self.STYLE_SHEET)
        self.setOptions(
            QWizard.WizardOption.NoBackButtonOnStartPage
            | QWizard.WizardOption.NoCancelButtonOnLastPage
        )
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, QPixmap())

        self._welcome = WelcomePage()
        self._select = SelectAgentsPage(self._welcome)
        self._hooks = HookConfigPage(self._select)
        self._prefs = NotificationPrefsPage()
        self._autostart = AutostartPage()
        self._finish = FinishPage()

        self.addPage(self._welcome)
        self.addPage(self._select)
        self.addPage(self._hooks)
        self.addPage(self._prefs)
        self.addPage(self._autostart)
        self.addPage(self._finish)

        self.finished.connect(self._on_finished)

    @property
    def selected_agents(self) -> dict[str, bool]:
        return self._select.selected_agents

    @property
    def notify_sound(self) -> bool:
        return self._prefs.notify_sound

    @property
    def notify_toast(self) -> bool:
        return self._prefs.notify_toast

    @property
    def autostart_enabled(self) -> bool:
        return self._autostart.autostart_enabled

    @property
    def configure_claude_hook(self) -> bool:
        return self._hooks.configure_claude_hook

    def _on_finished(self, result: int):
        """向导完成后保存配置。"""
        if result != QWizard.DialogCode.Accepted:
            return

        config = load_config()

        # 应用 Agent 选择
        for key, enabled in self.selected_agents.items():
            config[f"source_{key}"] = enabled

        # 应用通知偏好
        config["sound_enabled"] = self.notify_sound
        config["toast_enabled"] = self.notify_toast

        # 开机自启
        from autostart import set_autostart
        config["auto_start"] = self.autostart_enabled
        set_autostart(self.autostart_enabled)

        save_config(config)
        mark_wizard_completed()

        # 自动配置 Claude Code Hook
        if self.configure_claude_hook:
            try:
                from hook_utils import install_hooks
                install_hooks()
                logger.info("向导自动配置 Claude Code Hook 完成")
            except Exception as e:
                logger.warning("向导自动配置 Claude Code Hook 失败: %s", e)

        logger.info(
            "首次配置向导完成: agents=%s, sound=%s, toast=%s, autostart=%s",
            self.selected_agents, self.notify_sound,
            self.notify_toast, self.autostart_enabled,
        )


def should_run_wizard(config: dict) -> bool:
    """判断是否需要运行首次向导。"""
    if config.get("_wizard_completed"):
        return False
    marker = SIGNAL_DIR / ".wizard_completed"
    return not marker.exists()


def mark_wizard_completed() -> None:
    """标记向导已完成。"""
    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
    (SIGNAL_DIR / ".wizard_completed").touch()
