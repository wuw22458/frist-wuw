"""设置面板 UI 布局 — SettingsUIBuilder.

纯 UI 布局构建，不包含业务逻辑。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from constants import __version__
from ui.style import SCROLLBAR_STYLE
from ui.widgets import (
    MONO,
    RADIUS_BTN,
    RADIUS_MD,
    T1,
    T2,
    T3,
    BannerWidget,
    GlowBackground,
    SectionCard,
    StatusIndicator,
    ToggleSwitch,
    VolumeSlider,
    _shadow,
    btn_danger,
    btn_ghost,
    btn_primary,
    filter_btn_style,
    input_style,
)


class SettingsUIBuilder:
    """设置面板 UI 构建器."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._animatable_cards: list[QWidget] = []

        # UI 组件引用
        self._glow: GlowBackground = None
        self._scroll: QScrollArea = None
        self._update_bar: BannerWidget = None
        self._crash_bar: BannerWidget = None
        self._hero_icon: QLabel = None
        self._hero_status_text: QLabel = None
        self._hero_summary: QLabel = None
        self._pause_btn: QPushButton = None
        self._hero_runtime: QLabel = None
        self._status: StatusIndicator = None
        self._stat_today: tuple = None
        self._stat_waiting: tuple = None
        self._stat_errors: tuple = None
        self._sources_card: SectionCard = None
        self._source_switches: dict[str, ToggleSwitch] = {}
        self._sources_empty_label: QLabel = None
        self._sound_sw: ToggleSwitch = None
        self._toast_sw: ToggleSwitch = None
        self._vol_slider: VolumeSlider = None
        self._vol_value: QLabel = None
        self._vol_container: QWidget = None
        self._autostart_sw: ToggleSwitch = None
        self._sound_icon: QLabel = None
        self._sound_label: QLabel = None
        self._sound_btn: QPushButton = None
        self._reset_btn: QPushButton = None
        self._preview_btn: QPushButton = None
        self._test_btn: QPushButton = None
        self._dnd_sw: ToggleSwitch = None
        self._dnd_start_input: QLineEdit = None
        self._dnd_end_input: QLineEdit = None
        self._history_list: QListWidget = None
        self._history_filter: str = 'all'
        self._filter_btns: dict[str, QPushButton] = {}
        self._empty_label: QLabel = None

        # 历史操作按钮引用
        self._clear_btn: QPushButton = None
        self._log_btn: QPushButton = None
        self._diag_btn: QPushButton = None
        self._help_btn: QPushButton = None

    def build(self) -> QVBoxLayout:
        """构建完整的设置面板布局."""
        self._glow = GlowBackground(self._parent)
        self._glow.setGeometry(0, 0, self._parent.width(), self._parent.height())

        outer = QVBoxLayout(self._parent)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        scroll = self._scroll
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }' + SCROLLBAR_STYLE)

        content = QWidget()
        content.setStyleSheet('background: transparent;')
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # 构建各个区域
        self._build_title_area(root)
        self._build_banners(root)
        self._build_hero_card(root)
        self._build_history_card(root)
        self._build_stats_card(root)
        self._build_sources_card(root)
        self._build_notification_card(root)
        self._build_dnd_card(root)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        return outer

    def _build_title_area(self, root: QVBoxLayout) -> None:
        """构建标题区."""
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        icon_label = QLabel('◆')
        icon_label.setStyleSheet('color: #58a6ff; font-size: 18px; border: none;')
        title_row.addWidget(icon_label)

        title = QLabel(f'Agent Notify v{__version__}')
        title.setStyleSheet(f'color: {T1}; font-size: 18px; font-weight: 700; border: none;')
        title_row.addWidget(title)
        title_row.addStretch()
        root.addLayout(title_row)

        desc = QLabel('当 AI agent 需要确认或任务完成时通知你')
        desc.setStyleSheet('color: rgba(255,255,255,0.50); font-size: 12px; border: none;')
        desc.setWordWrap(True)
        root.addWidget(desc)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: rgba(255,255,255,0.08); border: none;')
        root.addWidget(sep)

    def _build_banners(self, root: QVBoxLayout) -> None:
        """构建横幅."""
        self._update_bar = BannerWidget('', action_text='下载更新', banner_type='info')
        self._update_bar.setVisible(False)
        root.addWidget(self._update_bar)

        self._crash_bar = BannerWidget('', action_text='清除', banner_type='error')
        self._crash_bar.setVisible(False)
        root.addWidget(self._crash_bar)

    def _build_hero_card(self, root: QVBoxLayout) -> None:
        """构建 Hero Status 卡片."""
        hero_card = QFrame()
        hero_card.setFixedHeight(80)
        hero_card.setAttribute(Qt.WA_StyledBackground, True)
        hero_card.setObjectName('hero-card')
        hero_card.setStyleSheet(
            'QFrame#hero-card {'
            '  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,'
            '    stop:0 rgba(30, 45, 65, 0.85),'
            '    stop:1 rgba(22, 27, 34, 0.95));'
            '  border: 1px solid rgba(255, 255, 255, 0.08);'
            f'  border-radius: {RADIUS_MD}px;'
            '}'
        )
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(16, 0, 16, 0)
        hero_layout.setSpacing(14)

        self._hero_icon = QLabel('●')
        self._hero_icon.setFixedSize(32, 32)
        self._hero_icon.setAlignment(Qt.AlignCenter)
        self._hero_icon.setStyleSheet('font-size: 24px; color: #3fb950; background: transparent; border: none;')
        hero_layout.addWidget(self._hero_icon)

        hero_text_col = QVBoxLayout()
        hero_text_col.setSpacing(2)
        self._hero_status_text = QLabel('正在监听')
        self._hero_status_text.setStyleSheet(
            f'color: {T1}; font-size: 15px; font-weight: 700; background: transparent; border: none;'
        )
        hero_text_col.addWidget(self._hero_status_text)
        self._hero_summary = QLabel('等待来自 AI agent 的通知...')
        self._hero_summary.setStyleSheet(f'color: {T3}; font-size: 11px; background: transparent; border: none;')
        hero_text_col.addWidget(self._hero_summary)
        hero_layout.addLayout(hero_text_col, 1)

        hero_right_col = QVBoxLayout()
        hero_right_col.setSpacing(4)
        hero_right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._pause_btn = QPushButton('暂停')
        self._pause_btn.setFixedSize(90, 32)
        self._pause_btn.setCursor(Qt.PointingHandCursor)
        self._pause_btn.setStyleSheet(btn_primary())
        _shadow(self._pause_btn)
        self._pause_btn.setToolTip('暂停或恢复监控')
        hero_right_col.addWidget(self._pause_btn)

        self._hero_runtime = QLabel('已运行 0 分钟')
        self._hero_runtime.setStyleSheet(
            f'color: {T3}; font-size: 10px; font-family: {MONO}; background: transparent; border: none;'
        )
        self._hero_runtime.setAlignment(Qt.AlignRight)
        hero_right_col.addWidget(self._hero_runtime)

        hero_layout.addLayout(hero_right_col)
        self._animatable_cards.append(hero_card)
        root.addWidget(hero_card)

        self._status = StatusIndicator()
        self._status.hide()

    def _build_stats_card(self, root: QVBoxLayout) -> None:
        """构建今日概览卡片."""
        stats_card = SectionCard('今日概览')
        stats_inner = QHBoxLayout()
        stats_inner.setSpacing(24)

        self._stat_today = self._make_stat_item('0', '条通知')
        stats_inner.addWidget(self._stat_today[0])

        self._stat_waiting = self._make_stat_item('0', '等待中')
        stats_inner.addWidget(self._stat_waiting[0])

        self._stat_errors = self._make_stat_item('0', '错误')
        stats_inner.addWidget(self._stat_errors[0])

        stats_card.add_layout(stats_inner)
        root.addWidget(stats_card)
        self._animatable_cards.append(stats_card)

    def _build_sources_card(self, root: QVBoxLayout) -> None:
        """构建监控来源卡片."""
        self._sources_card = SectionCard('监控来源')

        # 空状态提示（adapter 未注入时显示）
        self._sources_empty_label = QLabel('启动后自动检测已安装的 Agent')
        self._sources_empty_label.setStyleSheet(
            f'color: {T3}; font-size: 12px; border: none; padding: 8px 0;'
        )
        self._sources_card.add_widget(self._sources_empty_label)

        root.addWidget(self._sources_card)
        self._animatable_cards.append(self._sources_card)

    def _build_notification_card(self, root: QVBoxLayout) -> None:
        """构建通知选项卡片."""
        notif_card = SectionCard('通知')

        check_row = QHBoxLayout()
        check_row.setSpacing(20)

        self._sound_sw = self._make_toggle('播放提示音')
        self._sound_sw.setToolTip('收到通知时播放提示音')
        check_row.addWidget(self._sound_sw)

        self._toast_sw = self._make_toggle('显示系统通知')
        self._toast_sw.setToolTip('收到通知时弹出 Windows Toast')
        check_row.addWidget(self._toast_sw)

        notif_card.add_layout(check_row)

        # 音量滑块行（使用自定义 VolumeSlider）
        vol_row = QHBoxLayout()
        vol_row.setSpacing(10)
        vol_label = QLabel('🔊')
        vol_label.setFixedWidth(20)
        vol_label.setStyleSheet(f'color: {T2}; font-size: 14px; border: none;')
        vol_row.addWidget(vol_label)

        self._vol_slider = VolumeSlider(value=70)
        vol_row.addWidget(self._vol_slider, 1)

        self._vol_value = QLabel('70%')
        self._vol_value.setFixedWidth(35)
        self._vol_value.setAlignment(Qt.AlignRight)
        self._vol_value.setStyleSheet(f'color: {T3}; font-size: 11px; font-family: {MONO}; border: none;')
        vol_row.addWidget(self._vol_value)

        self._vol_container = QWidget()
        self._vol_container.setStyleSheet('background: transparent;')
        self._vol_container.setLayout(vol_row)
        notif_card.add_widget(self._vol_container)

        # 开机自启
        autostart_row = QHBoxLayout()
        autostart_row.setSpacing(20)
        self._autostart_sw = self._make_toggle('开机自启')
        self._autostart_sw.setToolTip('开机时自动启动 Agent Notify')
        autostart_row.addWidget(self._autostart_sw)
        autostart_row.addStretch()
        notif_card.add_layout(autostart_row)

        # 提示音路径
        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self._sound_icon = QLabel('♪')
        self._sound_icon.setFixedWidth(16)
        self._sound_icon.setStyleSheet('color: rgba(255,255,255,0.35); font-size: 12px; border: none;')

        self._sound_label = QLabel('提示音: —')
        self._sound_label.setStyleSheet(
            f'color: rgba(255,255,255,0.38); font-size: 10px; font-family: {MONO}; border: none;'
        )
        path_row.addWidget(self._sound_icon)
        path_row.addWidget(self._sound_label)
        path_row.addStretch()
        notif_card.add_layout(path_row)

        # 按钮行（全部使用 btn_ghost，统一圆角）
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._sound_btn = QPushButton('更换')
        self._sound_btn.setFixedHeight(30)
        self._sound_btn.setCursor(Qt.PointingHandCursor)
        self._sound_btn.setStyleSheet(btn_ghost())
        btn_row.addWidget(self._sound_btn)

        self._reset_btn = QPushButton('恢复默认')
        self._reset_btn.setFixedHeight(30)
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setStyleSheet(btn_ghost())
        btn_row.addWidget(self._reset_btn)

        self._preview_btn = QPushButton('试听')
        self._preview_btn.setFixedHeight(30)
        self._preview_btn.setCursor(Qt.PointingHandCursor)
        self._preview_btn.setStyleSheet(btn_ghost())
        btn_row.addWidget(self._preview_btn)

        btn_row.addStretch()

        self._test_btn = QPushButton('测试通知')
        self._test_btn.setFixedHeight(30)
        self._test_btn.setCursor(Qt.PointingHandCursor)
        self._test_btn.setStyleSheet(btn_ghost())
        btn_row.addWidget(self._test_btn)

        notif_card.add_layout(btn_row)

        root.addWidget(notif_card)
        self._animatable_cards.append(notif_card)

    def _build_dnd_card(self, root: QVBoxLayout) -> None:
        """构建免打扰卡片."""
        dnd_card = SectionCard('免打扰')

        self._dnd_sw = self._make_toggle('启用免打扰时段')
        self._dnd_sw.setToolTip('在指定时段内静音所有通知')
        dnd_card.add_widget(self._dnd_sw)

        dnd_time_row = QHBoxLayout()
        dnd_time_row.setSpacing(8)

        dnd_time_row.addWidget(self._make_label('从'))

        self._dnd_start_input = QLineEdit('22:00')
        self._dnd_start_input.setFixedWidth(60)
        self._dnd_start_input.setMaxLength(5)
        self._dnd_start_input.setStyleSheet(input_style())
        self._dnd_start_input.setPlaceholderText('HH:MM')
        dnd_time_row.addWidget(self._dnd_start_input)

        dnd_time_row.addWidget(self._make_label('到'))
        self._dnd_end_input = QLineEdit('08:00')
        self._dnd_end_input.setFixedWidth(60)
        self._dnd_end_input.setMaxLength(5)
        self._dnd_end_input.setStyleSheet(input_style())
        self._dnd_end_input.setPlaceholderText('HH:MM')
        dnd_time_row.addWidget(self._dnd_end_input)

        dnd_time_row.addStretch()
        dnd_card.add_layout(dnd_time_row)

        root.addWidget(dnd_card)
        self._animatable_cards.append(dnd_card)

    def _build_history_card(self, root: QVBoxLayout) -> None:
        """构建最近通知卡片."""
        history_card = SectionCard('最近通知')
        history_card.setMinimumHeight(100)

        self._history_list = QListWidget()
        self._history_list.setStyleSheet(
            f"""
            QListWidget {{
                background: rgba(0,0,0,0.20);
                border: none;
                border-radius: {RADIUS_MD}px;
                padding: 4px;
            }}
            QListWidget::item {{
                color: rgba(255,255,255,0.65);
                font-size: 11px;
                padding: 5px 8px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
                border-radius: {RADIUS_BTN}px;
            }}
            QListWidget::item:hover {{
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.85);
            }}
            QListWidget::item:selected {{
                background: rgba(88,166,255,0.15);
                color: rgba(255,255,255,0.95);
            }}
            QListWidget::item:last {{
                border-bottom: none;
            }}
        """
            + SCROLLBAR_STYLE
        )
        self._history_list.setMaximumHeight(160)
        self._history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._history_list.setToolTip('最近收到的通知记录')

        history_card.add_widget(self._history_list)

        # 筛选按钮（统一圆角）
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        for key, label in [
            ('all', '全部'),
            ('waiting', '等待'),
            ('running', '运行'),
            ('error', '错误'),
            ('success', '完成'),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == 'all')
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(24)
            btn.setStyleSheet(filter_btn_style(key == 'all'))
            self._filter_btns[key] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        history_card.add_layout(filter_row)

        self._empty_label = QLabel('暂无通知')
        self._empty_label.setStyleSheet('color: rgba(255,255,255,0.25); font-size: 12px; border: none;')
        self._empty_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        history_card.add_widget(self._empty_label)

        # 操作按钮（统一圆角，全部 btn_ghost/btn_danger）
        btn_row_hist = QHBoxLayout()
        btn_row_hist.setSpacing(8)

        self._clear_btn = QPushButton('🗑 清除历史')
        self._clear_btn.setFixedHeight(30)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setStyleSheet(btn_danger())
        self._clear_btn.setToolTip('清空所有通知记录')
        btn_row_hist.addWidget(self._clear_btn)

        self._log_btn = QPushButton('📂 查看日志')
        self._log_btn.setFixedHeight(30)
        self._log_btn.setCursor(Qt.PointingHandCursor)
        self._log_btn.setStyleSheet(btn_ghost())
        self._log_btn.setToolTip('打开日志文件夹')
        btn_row_hist.addWidget(self._log_btn)

        self._diag_btn = QPushButton('🔍 诊断')
        self._diag_btn.setFixedHeight(30)
        self._diag_btn.setCursor(Qt.PointingHandCursor)
        self._diag_btn.setStyleSheet(btn_ghost())
        self._diag_btn.setToolTip('检查配置是否正常')
        btn_row_hist.addWidget(self._diag_btn)

        self._help_btn = QPushButton('❓ 帮助')
        self._help_btn.setFixedHeight(30)
        self._help_btn.setCursor(Qt.PointingHandCursor)
        self._help_btn.setStyleSheet(btn_ghost())
        self._help_btn.setToolTip('查看故障排除指南')
        btn_row_hist.addWidget(self._help_btn)

        btn_row_hist.addStretch()
        history_card.add_layout(btn_row_hist)

        root.addWidget(history_card, stretch=1)
        self._animatable_cards.append(history_card)

    # ── 辅助方法 ──────────────────────────────────────────

    def _make_toggle(self, text: str) -> ToggleSwitch:
        return ToggleSwitch(text, self._parent)

    def _make_stat_item(self, num: str, label: str) -> tuple:
        w = QWidget()
        w.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(w)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        num_lbl = QLabel(num)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(f'color: {T1}; font-size: 22px; font-weight: 700; border: none;')
        layout.addWidget(num_lbl)

        desc = QLabel(label)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f'color: {T3}; font-size: 11px; border: none;')
        layout.addWidget(desc)

        return (w, num_lbl)

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f'color: {T2}; font-size: 12px; border: none;')
        return lbl

    def get_animatable_cards(self) -> list[QWidget]:
        return self._animatable_cards

    def sync_glow(self) -> None:
        if self._glow:
            self._glow.setGeometry(0, 0, self._parent.width(), self._parent.height())
