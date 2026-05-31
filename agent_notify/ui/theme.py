"""主题管理 — Theme.

集中管理所有颜色常量和样式，实现"改一色而全换"。
"""

# ── 背景色 ─────────────────────────────────────────────────
BG_PRIMARY = '#0d1117'      # L1 底层背景
BG_CARD = '#161b22'         # L2 卡片背景
BG_INPUT = 'rgba(0,0,0,0.25)'  # L3 输入框背景

# ── 毛玻璃 ─────────────────────────────────────────────────
GLASS_BG = 'rgba(255, 255, 255, 0.06)'
GLASS_BORDER = 'rgba(255, 255, 255, 0.08)'
GLASS_HOVER = 'rgba(255, 255, 255, 0.10)'

# ── 文字色 ─────────────────────────────────────────────────
TEXT_PRIMARY = '#f0f3f6'    # T1 主文字
TEXT_SECONDARY = '#b0b8c4'  # T2 次级文字
TEXT_TERTIARY = '#6e7681'   # T3 辅助文字
TEXT_DISABLED = 'rgba(255,255,255,0.22)'
TEXT_PLACEHOLDER = 'rgba(255,255,255,0.25)'
TEXT_DESCRIPTION = 'rgba(255,255,255,0.50)'

# ── 主题色（Accent）─────────────────────────────────────────
ACCENT = '#58a6ff'
ACCENT_HOVER = '#79c0ff'
ACCENT_ACTIVE = '#a5d6ff'
ACCENT_BG = '#1e6ff0'       # Primary 按钮背景
ACCENT_BG_HOVER = '#3892ff'
ACCENT_BG_ACTIVE = '#1a5fcc'

# ── 语义色 ─────────────────────────────────────────────────
SUCCESS = '#3fb950'
WARNING = '#d29922'
ERROR = '#f85149'
INFO = '#58a6ff'

# ── 边框 ─────────────────────────────────────────────────
BORDER_DEFAULT = '#30363d'
BORDER_LIGHT = '#3d444d'
BORDER_SEPARATOR = 'rgba(255,255,255,0.08)'

# ── 字体 ─────────────────────────────────────────────────
FONT_FAMILY = '"Microsoft YaHei UI", "Segoe UI", sans-serif'
FONT_MONO = '"Cascadia Code", "Consolas", monospace'

# ── 圆角 ─────────────────────────────────────────────────
RADIUS_CARD = 14
RADIUS_BANNER = 10
RADIUS_BUTTON_PRIMARY = 18
RADIUS_BUTTON_GHOST = 15
RADIUS_INPUT = 6
RADIUS_TOGGLE = 11  # 50% of track height

# ── 间距 ─────────────────────────────────────────────────
SPACING_XS = 4
SPACING_SM = 6
SPACING_MD = 8
SPACING_LG = 12
SPACING_XL = 16
SPACING_XXL = 24

# ── 向导样式 ─────────────────────────────────────────────
WIZARD_BG = BG_PRIMARY  # 统一使用主面板背景色
WIZARD_BUTTON_BG = '#3a3a5c'
WIZARD_BUTTON_HOVER = '#4a4a7c'
WIZARD_PRIMARY_BG = '#2563eb'
WIZARD_PRIMARY_HOVER = '#3b82f6'


def get_wizard_style() -> str:
    """获取向导统一样式."""
    return f"""
        QWizard {{
            background-color: {WIZARD_BG};
            color: {TEXT_PRIMARY};
        }}
        QWizard QLabel {{ color: {TEXT_PRIMARY}; }}
        QWizard QPushButton {{
            background-color: {WIZARD_BUTTON_BG};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: 4px;
            padding: 6px 18px;
            font-size: 12px;
        }}
        QWizard QPushButton:hover {{ background-color: {WIZARD_BUTTON_HOVER}; }}
        QWizard QPushButton#qt_wizard_commit {{
            background-color: {WIZARD_PRIMARY_BG};
            border-color: {WIZARD_PRIMARY_HOVER};
        }}
        QWizard QPushButton#qt_wizard_commit:hover {{ background-color: {WIZARD_PRIMARY_HOVER}; }}
    """
