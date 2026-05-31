"""兼容性 re-export — 实际代码已拆分到 ui/ 包.

- ui/widgets.py  — 共享 UI 组件和色板
- ui/settings.py — SettingsWindow
- ui/tray.py     — TrayApp

新代码应直接从 ui.tray / ui.settings 导入.
此文件仅为向后兼容保留.
"""

from ui.settings import SettingsWindow  # noqa: F401
from ui.tray import TrayApp  # noqa: F401
from ui.widgets import (  # noqa: F401
    _EVENT_COLORS,
    _EVENT_STATUS_PREFIX,
    _EVENT_TAGS,
    _GLASS_CARD_STYLE,
    ACCENT,
    ACCENT_HOVER,
    BG,
    BG_CARD,
    BORDER_CARD,
    FONT,
    GREEN,
    MONO,
    ORANGE,
    RED,
    T1,
    T2,
    T3,
    GlowBackground,
    SectionCard,
    StatusIndicator,
    ToggleSwitch,
    _make_icon,
    _shadow,
)
