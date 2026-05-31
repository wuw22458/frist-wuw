"""设置面板样式 — 按钮、输入框等样式定义。"""

from ui.widgets import FONT, T1, MONO, ACCENT


def btn_primary() -> str:
    """主要按钮样式。"""
    return f"""
        QPushButton {{
            background: #1e6ff0;
            color: white;
            border: none;
            border-radius: 18px;
            padding: 6px 20px;
            font-size: 13px;
            font-weight: 600;
            font-family: {FONT};
        }}
        QPushButton:hover {{ background: #3892ff; }}
        QPushButton:pressed {{ background: #1a5fcc; }}
    """


def btn_ghost() -> str:
    """幽灵按钮样式。"""
    return f"""
        QPushButton {{
            background: rgba(255,255,255,0.08);
            color: rgba(255,255,255,0.75);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 15px;
            padding: 5px 16px;
            font-size: 12px;
            font-family: {FONT};
        }}
        QPushButton:hover {{
            background: rgba(255,255,255,0.14);
            border-color: rgba(255,255,255,0.28);
            color: white;
        }}
        QPushButton:disabled {{
            background: rgba(255,255,255,0.04);
            color: rgba(255,255,255,0.22);
            border-color: rgba(255,255,255,0.06);
        }}
    """


def btn_danger() -> str:
    """危险按钮样式。"""
    return f"""
        QPushButton {{
            background: rgba(248,81,73,0.18);
            color: #f85149;
            border: 1px solid rgba(248,81,73,0.35);
            border-radius: 18px;
            padding: 6px 20px;
            font-size: 13px;
            font-weight: 600;
            font-family: {FONT};
        }}
        QPushButton:hover {{ background: rgba(248,81,73,0.30); }}
    """


def btn_success() -> str:
    """成功按钮样式。"""
    return f"""
        QPushButton {{
            background: rgba(63,185,80,0.18);
            color: #3fb950;
            border: 1px solid rgba(63,185,80,0.35);
            border-radius: 18px;
            padding: 6px 20px;
            font-size: 13px;
            font-weight: 600;
            font-family: {FONT};
        }}
        QPushButton:hover {{ background: rgba(63,185,80,0.30); }}
    """


def input_style() -> str:
    """输入框样式。"""
    return f"""
        QLineEdit {{
            background: rgba(0,0,0,0.25);
            color: {T1};
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
            font-family: {MONO};
        }}
        QLineEdit:focus {{
            border-color: {ACCENT.name()};
        }}
    """


def filter_btn_style(active: bool) -> str:
    """历史过滤按钮样式。"""
    if active:
        return """
            QPushButton {
                background: rgba(88, 166, 255, 0.2);
                color: #58a6ff;
                border: 1px solid rgba(88, 166, 255, 0.3);
                border-radius: 12px;
                padding: 0 10px;
                font-size: 11px;
            }
        """
    return """
        QPushButton {
            background: transparent;
            color: rgba(255,255,255,0.5);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 0 10px;
            font-size: 11px;
        }
        QPushButton:hover {
            border-color: rgba(255,255,255,0.2);
        }
    """
