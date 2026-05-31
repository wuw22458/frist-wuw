"""设置面板业务逻辑 — SettingsPresenter.

负责配置读写、诊断逻辑、暂停控制、事件处理。
"""

import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from events import AgentEvent
from log import get_logger
from notification import notify, play_sound
from settings import save_config

logger = get_logger('settings_presenter')


class SettingsPresenter:
    """设置面板业务逻辑控制器."""

    def __init__(self, config: dict, ui):
        self._config = config
        self._ui = ui  # SettingsUIBuilder 实例
        self._is_paused = False
        self._last_notif_summary = '等待来自 AI agent 的通知...'

    @property
    def config(self) -> dict:
        return self._config

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def last_notif_summary(self) -> str:
        return self._last_notif_summary

    def save_config(self) -> None:
        """保存当前配置到磁盘."""
        save_config(self._config)

    def update_config(self, key: str, value) -> None:
        """更新配置项并保存."""
        self._config[key] = value
        self.save_config()

    def toggle_pause(self) -> bool:
        """切换暂停状态，返回新状态."""
        self._is_paused = not self._is_paused
        return self._is_paused

    def handle_event(self, event: AgentEvent) -> dict:
        """处理 AgentEvent，返回历史记录条目."""
        entry = {
            'time': __import__('time').strftime('%H:%M:%S'),
            'timestamp': __import__('time').time(),
            'event_type': event.event_type,
            'message': event.message,
            'agent_id': event.agent_id,
        }
        return entry

    def update_hero_summary(self, event: AgentEvent) -> str:
        """更新 Hero 卡片摘要，返回截断后的文本."""
        from ui.widgets import _EVENT_TAGS
        tag = _EVENT_TAGS.get(event.event_type, '信息')
        summary = f'[{tag}] {event.message}'
        if len(summary) > 45:
            summary = summary[:42] + '...'
        self._last_notif_summary = summary
        return summary

    def send_test_notification(self) -> tuple[bool, str]:
        """发送测试通知，返回 (成功, 错误信息)."""
        test_msg = '这是一条测试通知，设置已生效'

        if self._config.get('toast_enabled', True):
            try:
                notify(
                    'Agent Notify 测试',
                    test_msg,
                    sound=self._config.get('sound_enabled', True),
                    source='test',
                    sound_path=self._config.get('custom_sound', ''),
                )
            except Exception as e:
                logger.warning('测试通知发送失败: %s', e)
                return False, str(e)

        return True, ''

    def preview_sound(self) -> None:
        """试听当前提示音."""
        vol = self._config.get('sound_volume', 70)
        play_sound(self._config.get('custom_sound', ''), volume=vol)

    def pick_sound(self) -> str | None:
        """选择自定义提示音文件，返回路径或 None."""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            None,
            '选择提示音',
            '',
            '音频文件 (*.wav *.mp3);;WAV 文件 (*.wav);;MP3 文件 (*.mp3);;所有文件 (*)',
        )
        if path:
            self._config['custom_sound'] = path
            self.save_config()
            return path
        return None

    def reset_sound(self) -> None:
        """恢复默认提示音."""
        self._config.pop('custom_sound', None)
        self.save_config()

    def get_sound_display_path(self) -> str:
        """获取提示音的显示路径."""
        custom = self._config.get('custom_sound', '')
        if custom:
            name = Path(custom).name
        else:
            from notification import _default_sound
            d = _default_sound()
            name = d.name if d else '—'
        return f'提示音: {name}'

    def get_sound_full_path(self) -> str:
        """获取提示音的完整路径."""
        custom = self._config.get('custom_sound', '')
        if custom:
            return custom
        from notification import _default_sound
        d = _default_sound()
        return str(d) if d else ''

    def open_log_folder(self) -> None:
        """打开日志文件夹."""
        from constants import SIGNAL_DIR
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(SIGNAL_DIR)))

    def open_troubleshooting(self) -> None:
        """打开故障排除指南."""
        import webbrowser
        webbrowser.open('https://github.com/wuw22458/agent_notify/blob/main/docs/troubleshooting.md')

    def open_download(self, url: str) -> None:
        """打开下载链接."""
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def run_diagnostics(self) -> list[tuple[str, bool, str]]:
        """运行诊断检查，返回结果列表."""
        from constants import SIGNAL_DIR

        results = []

        # 1. 检查信号目录
        if SIGNAL_DIR.exists():
            if os.access(SIGNAL_DIR, os.W_OK):
                results.append(('信号目录', True, str(SIGNAL_DIR)))
            else:
                results.append(('信号目录', False, f'目录存在但不可写: {SIGNAL_DIR}'))
        else:
            results.append(('信号目录', False, f'目录不存在: {SIGNAL_DIR}'))

        # 2. 检查 Claude Code Hook 配置
        try:
            from hook_utils import _read_settings
            settings = _read_settings()
            hooks = settings.get('hooks', {})
            if hooks:
                results.append(('Claude Code Hook', True, '已配置'))
            else:
                results.append(('Claude Code Hook', False, '未配置'))
        except Exception as e:
            results.append(('Claude Code Hook', False, f'检查失败: {e}'))

        # 3. 检查 Toast 通知权限
        try:
            from notification import _HAS_WINOTOAST
            if _HAS_WINOTOAST:
                results.append(('Toast 通知', True, 'winotify 可用'))
            else:
                results.append(('Toast 通知', True, '使用 PowerShell 回退'))
        except Exception as e:
            results.append(('Toast 通知', False, f'检查失败: {e}'))

        # 4. 检查配置文件
        from constants import CONFIG_FILE
        if CONFIG_FILE.exists():
            try:
                import json
                json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
                results.append(('配置文件', True, '格式正确'))
            except Exception as e:
                results.append(('配置文件', False, f'格式错误: {e}'))
        else:
            results.append(('配置文件', True, '使用默认配置'))

        return results
