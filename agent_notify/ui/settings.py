"""设置面板 — SettingsWindow（门面模式）.

对外接口保持不变，内部委托给：
- SettingsUIBuilder: 纯 UI 布局
- SettingsPresenter: 业务逻辑
- HistoryManager: 数据持久化
- AnimationController: 动画控制
"""

import time as _time

from PySide6.QtCore import QRegularExpression, QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QRegularExpressionValidator
from PySide6.QtWidgets import QWidget

from events import AgentEvent, EventType
from ui.animation_controller import AnimationController
from ui.history_manager import HistoryManager
from ui.settings_presenter import SettingsPresenter
from ui.settings_ui import SettingsUIBuilder
from ui.widgets import _EVENT_TAGS, GREEN, ORANGE


def _relative_time(ts: float) -> str:
    """Convert timestamp to relative time string."""
    diff = int(_time.time() - ts)
    if diff < 60:
        return '刚刚'
    elif diff < 3600:
        return f'{diff // 60} 分钟前'
    elif diff < 86400:
        return f'{diff // 3600} 小时前'
    else:
        return f'{diff // 86400} 天前'


class SettingsWindow(QWidget):
    config_changed = Signal()
    pause_toggled = Signal(bool)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Agent Notify')
        self.setMinimumSize(470, 560)
        self.resize(500, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # 初始化子模块
        from settings import load_config
        self._config = config if config is not None else load_config()
        self._ui = SettingsUIBuilder(self)
        self._presenter = SettingsPresenter(self._config, self._ui)
        self._history = HistoryManager()
        self._anim = AnimationController(self)

        # adapter 显示名映射
        self._adapter_display_names: dict[str, str] = {}

        # 构建 UI
        self._ui.build()
        self._setup_connections()
        self._init_state()

        # 注册动画卡片
        for card in self._ui.get_animatable_cards():
            self._anim.register_card(card)
        self._anim.setup_entrance()

    def _setup_connections(self) -> None:
        """设置信号连接."""
        ui = self._ui

        # Hero 卡片
        ui._pause_btn.clicked.connect(self.toggle_pause)

        # 通知选项
        ui._sound_sw.toggled.connect(self._on_sound_toggled)
        ui._toast_sw.toggled.connect(self._save)
        ui._vol_slider.valueChanged.connect(self._on_volume_changed)
        ui._autostart_sw.toggled.connect(self._on_autostart_toggled)

        # 提示音按钮
        ui._sound_btn.clicked.connect(self._pick_sound)
        ui._reset_btn.clicked.connect(self._reset_sound)
        ui._preview_btn.clicked.connect(self._preview_sound)
        ui._test_btn.clicked.connect(self._send_test_notification)

        # 免打扰
        ui._dnd_sw.toggled.connect(self._on_dnd_toggled)
        ui._dnd_start_input.editingFinished.connect(self._save_dnd_times)
        ui._dnd_end_input.editingFinished.connect(self._save_dnd_times)

        # 历史筛选
        for key, btn in ui._filter_btns.items():
            btn.clicked.connect(lambda checked, k=key: self._set_history_filter(k))

        # 历史操作按钮（需要通过父布局找到）
        self._connect_history_buttons()

        # 横幅
        ui._update_bar.action_clicked.connect(lambda: self._presenter.open_download(self._presenter._config.get('update_url', '')))
        ui._crash_bar.action_clicked.connect(self._dismiss_crash)
        ui._crash_bar.closed.connect(self._dismiss_crash)

    def _connect_history_buttons(self) -> None:
        """连接历史卡片的操作按钮."""
        ui = self._ui
        # 查找历史卡片中的按钮
        history_card = ui._history_list.parent()
        if history_card:
            for btn in history_card.findChildren(__import__('PySide6.QtWidgets', fromlist=['QPushButton']).QPushButton):
                text = btn.text()
                if '清除' in text:
                    btn.clicked.connect(self._clear_history)
                elif '日志' in text:
                    btn.clicked.connect(self._presenter.open_log_folder)
                elif '诊断' in text:
                    btn.clicked.connect(self._run_diagnostics)
                elif '帮助' in text:
                    btn.clicked.connect(self._presenter.open_troubleshooting)

    def _init_state(self) -> None:
        """初始化控件状态."""
        ui = self._ui

        # 配置值
        ui._sound_sw.setChecked(self._config.get('sound_enabled', True))
        ui._toast_sw.setChecked(self._config.get('toast_enabled', True))
        ui._vol_slider.setValue(self._config.get('sound_volume', 70))
        ui._vol_value.setText(f'{self._config.get("sound_volume", 70)}%')

        from autostart import is_autostart_enabled
        ui._autostart_sw.setChecked(is_autostart_enabled())

        ui._dnd_sw.setChecked(self._config.get('dnd_enabled', False))
        ui._dnd_start_input.setText(self._config.get('dnd_start', '22:00'))
        ui._dnd_end_input.setText(self._config.get('dnd_end', '08:00'))

        # 提示音路径
        ui._sound_label.setText(self._presenter.get_sound_display_path())
        ui._sound_label.setToolTip(self._presenter.get_sound_full_path())
        ui._reset_btn.setVisible(bool(self._config.get('custom_sound')))

        # 音量容器可见性
        ui._vol_container.setVisible(ui._sound_sw.isChecked())

        # 免打扰控件状态
        ui._dnd_start_input.setEnabled(ui._dnd_sw.isChecked())
        ui._dnd_end_input.setEnabled(ui._dnd_sw.isChecked())

        # 时间校验器
        _time_re = QRegularExpression(r'^(?:[01]\d|2[0-3]):[0-5]\d$')
        _time_validator = QRegularExpressionValidator(_time_re)
        ui._dnd_start_input.setValidator(_time_validator)
        ui._dnd_end_input.setValidator(_time_validator)

        # 历史记录
        self._refresh_history()
        self._update_stats()

        # 运行时长定时器
        self._hero_start_time = _time.time()
        self._runtime_timer = QTimer(self)
        self._runtime_timer.timeout.connect(self._update_hero_runtime)
        self._runtime_timer.start(30000)

        # 检测崩溃日志
        self._check_crash_report()

    def _check_crash_report(self) -> None:
        """检测并显示崩溃报告."""
        from crash_reporter import has_crash_report, read_crash_report

        if has_crash_report():
            crash_text = read_crash_report()
            summary = '上次运行异常退出'
            if crash_text:
                for line in crash_text.splitlines():
                    if line.startswith('崩溃时间:'):
                        summary = f'上次崩溃: {line.split(":", 1)[1].strip()}'
                        break
            self._ui._crash_bar.set_text(f'{summary}，日志已记录到 crash.log')
            self._ui._crash_bar.setVisible(True)

    def sizeHint(self):
        return QSize(500, 700)

    # ── Adapter 信息注入 ────────────────────────────────────

    def set_adapter_info(self, adapters: list) -> None:
        """由 TrayApp 调用，注入 adapter 信息并动态创建 source switches."""
        self._adapter_display_names = {a.agent_id: a.display_name for a in adapters}

        # 清除旧的 source switches
        for sw in self._ui._source_switches.values():
            sw.setParent(None)
            sw.deleteLater()
        self._ui._source_switches.clear()

        # 动态创建
        for adapter in adapters:
            key = f'source_{adapter.agent_id}'
            sw = self._ui._make_toggle(adapter.display_name)
            sw.setChecked(self._config.get(key, True))
            sw.toggled.connect(self._save)
            sw.setToolTip(adapter.description)
            self._ui._source_switches[key] = sw
            self._ui._sources_card.add_widget(sw)

    # ── 公开方法（对外接口保持不变）────────────────────────

    def set_status(self, text: str, color: QColor = None):
        self._ui._status.set_status(text, color)
        self._ui._hero_status_text.setText(text)
        if color is not None:
            self._ui._hero_icon.setStyleSheet(
                f'font-size: 24px; color: {color.name()}; background: transparent; border: none;'
            )

    def set_notif_count(self, count: int):
        self._ui._status.set_count(count)
        if count > 0:
            self._ui._hero_summary.setText(f'已捕获 {count} 个事件')

    def show_last_notification(self, event: AgentEvent):
        """从 AgentEvent 添加历史记录."""
        entry = self._presenter.handle_event(event)
        self._history.add(entry)
        self._refresh_history()
        self._update_hero_summary(event)
        self._update_stats()

    def set_update_info(self, info) -> None:
        """显示更新提示横幅。由 TrayApp 调用."""
        self._ui._update_bar.set_text(f'新版本 {info.latest_version} 可用（当前 v{__import__("constants").__version__}）')
        self._presenter._config['update_url'] = info.download_url or info.html_url
        self._ui._update_bar.setVisible(True)

    # ── 内部方法 ──────────────────────────────────────────

    def _refresh_history(self):
        ui = self._ui
        ui._history_list.clear()

        filtered = self._history.get_filtered(self._ui._history_filter)
        if not filtered:
            ui._history_list.hide()
            ui._empty_label.show()
            return

        ui._empty_label.hide()
        ui._history_list.show()

        for entry in reversed(filtered):
            agent_id = entry.get('agent_id', '')
            source_display = self._adapter_display_names.get(agent_id, agent_id or '?')

            event_type = entry.get('event_type', 'info')
            event_tag = _EVENT_TAGS.get(event_type, '信息')
            rel = _relative_time(entry.get('timestamp', 0))
            text = f'{rel}  [{event_tag}]  {entry["message"]}'
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(text)
            item.setToolTip(f'来源: {source_display}\n时间: {entry.get("time", "")}')
            ui._history_list.addItem(item)

        ui._history_list.scrollToBottom()

    def _update_stats(self):
        stats = self._history.get_today_stats()
        if hasattr(self._ui, '_stat_today'):
            self._ui._stat_today[1].setText(str(stats['total']))
            self._ui._stat_waiting[1].setText(str(stats['waiting']))
            self._ui._stat_errors[1].setText(str(stats['errors']))

    def _update_hero_summary(self, event):
        summary = self._presenter.update_hero_summary(event)
        self._ui._hero_summary.setText(summary)

    def _update_hero_runtime(self):
        elapsed = int(_time.time() - self._hero_start_time)
        if elapsed < 60:
            self._ui._hero_runtime.setText(f'已运行 {elapsed} 秒')
        else:
            mins = elapsed // 60
            self._ui._hero_runtime.setText(f'已运行 {mins} 分钟')

    def _set_history_filter(self, key: str):
        self._ui._history_filter = key
        for k, btn in self._ui._filter_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(__import__('ui.settings_styles', fromlist=['filter_btn_style']).filter_btn_style(k == key))
        self._refresh_history()

    def _clear_history(self) -> None:
        self._history.clear()
        self._refresh_history()

    def _dismiss_crash(self) -> None:
        from crash_reporter import clear_crash_report
        clear_crash_report()
        self._ui._crash_bar.hide()

    def _on_sound_toggled(self, checked: bool):
        ui = self._ui
        ui._sound_btn.setEnabled(checked)
        ui._reset_btn.setEnabled(checked)
        ui._preview_btn.setEnabled(checked)
        ui._sound_icon.setVisible(checked)
        ui._sound_label.setVisible(checked)
        ui._vol_container.setVisible(checked)
        self._save()

    def _on_volume_changed(self, value: int):
        self._ui._vol_value.setText(f'{value}%')
        self._save()

    def _on_autostart_toggled(self, checked: bool):
        from autostart import set_autostart
        set_autostart(checked)

    def _pick_sound(self):
        path = self._presenter.pick_sound()
        if path:
            self.config_changed.emit()
            self._ui._sound_label.setText(self._presenter.get_sound_display_path())
            self._ui._sound_label.setToolTip(path)
            self._ui._reset_btn.setVisible(True)

    def _reset_sound(self):
        self._presenter.reset_sound()
        self.config_changed.emit()
        self._ui._sound_label.setText(self._presenter.get_sound_display_path())
        self._ui._sound_label.setToolTip(self._presenter.get_sound_full_path())
        self._ui._reset_btn.setVisible(False)

    def _preview_sound(self):
        self._presenter.preview_sound()

    def _send_test_notification(self):
        test_event = AgentEvent(
            agent_id='test',
            event_type=EventType.INFO,
            message='这是一条测试通知，设置已生效',
        )
        self.show_last_notification(test_event)

        success, error_msg = self._presenter.send_test_notification()

        if success:
            self._ui._test_btn.setText('✓ 已发送')
            self._ui._test_btn.setStyleSheet(__import__('ui.settings_styles', fromlist=['btn_success']).btn_success())
        else:
            self._ui._test_btn.setText('✗ 失败')
            self._ui._test_btn.setStyleSheet(__import__('ui.settings_styles', fromlist=['btn_danger']).btn_danger())

        QTimer.singleShot(2000, self._reset_test_btn)

    def _reset_test_btn(self):
        self._ui._test_btn.setText('测试通知')
        self._ui._test_btn.setStyleSheet(__import__('ui.settings_styles', fromlist=['btn_ghost']).btn_ghost())

    def toggle_pause(self):
        from ui.settings_styles import btn_danger, btn_primary

        is_paused = self._presenter.toggle_pause()
        if is_paused:
            self._ui._pause_btn.setText('继续')
            self._ui._pause_btn.setStyleSheet(btn_danger())
            self.set_status('已暂停', ORANGE)
            self._ui._hero_summary.setText('监控已暂停，不会接收新通知')
        else:
            self._ui._pause_btn.setText('暂停')
            self._ui._pause_btn.setStyleSheet(btn_primary())
            self.set_status('监控中', GREEN)
            self._ui._hero_summary.setText(self._presenter.last_notif_summary)

        self._anim.apply_pause_filter(self._ui._scroll, is_paused)
        self.pause_toggled.emit(is_paused)

    def _save(self):
        ui = self._ui
        self._config['sound_enabled'] = ui._sound_sw.isChecked()
        self._config['toast_enabled'] = ui._toast_sw.isChecked()
        self._config['sound_volume'] = ui._vol_slider.value()
        for key, sw in ui._source_switches.items():
            self._config[key] = sw.isChecked()
        self._presenter.save_config()
        self.config_changed.emit()

    def _on_dnd_toggled(self, checked: bool):
        self._config['dnd_enabled'] = checked
        self._presenter.save_config()
        self.config_changed.emit()
        self._ui._dnd_start_input.setEnabled(checked)
        self._ui._dnd_end_input.setEnabled(checked)

    def _save_dnd_times(self):
        import re
        ui = self._ui
        start = ui._dnd_start_input.text().strip()
        end = ui._dnd_end_input.text().strip()

        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', start):
            start = '22:00'
            ui._dnd_start_input.setText(start)
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', end):
            end = '08:00'
            ui._dnd_end_input.setText(end)

        self._config['dnd_start'] = start
        self._config['dnd_end'] = end
        self._presenter.save_config()
        self.config_changed.emit()

    def _run_diagnostics(self):
        results = self._presenter.run_diagnostics()
        self._show_diagnostics_results(results)

    def _show_diagnostics_results(self, results: list) -> None:
        from PySide6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        msg.setWindowTitle('诊断结果')
        msg.setIcon(QMessageBox.Information)

        text = '诊断检查结果：\n\n'
        all_ok = True
        for name, ok, detail in results:
            status = '✓' if ok else '✗'
            text += f'{status} {name}: {detail}\n'
            if not ok:
                all_ok = False

        if all_ok:
            text += '\n所有检查通过，配置正常。'
        else:
            text += '\n部分检查失败，请根据提示修复。'

        msg.setText(text)
        msg.exec()

    # ── 窗口事件 ──────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_geometry_restored', False):
            self._geometry_restored = True
            s = QSettings('AgentNotify', 'SettingsWindow')
            geo = s.value('geometry')
            if geo:
                self.restoreGeometry(geo)
            else:
                self.resize(500, 700)
        self.layout().activate()
        QTimer.singleShot(0, self._ui.sync_glow)
        QTimer.singleShot(80, self._anim.play_entrance)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ui.sync_glow()

    def closeEvent(self, event):
        s = QSettings('AgentNotify', 'SettingsWindow')
        s.setValue('geometry', self.saveGeometry())

        event.ignore()
        self.hide()
        if not getattr(self, '_close_hint_shown', False):
            self._close_hint_shown = True
            tray = self.parent()
            if tray and hasattr(tray, 'showMessage'):
                tray.showMessage(
                    'Agent Notify',
                    '应用已最小化到系统托盘，仍在后台运行',
                    1,
                    3000,
                )

    @property
    def is_paused(self) -> bool:
        return self._presenter.is_paused
