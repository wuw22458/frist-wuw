"""设计 Token — 动画时长、缓动曲线、全局样式常量。

供 UI 动画代码统一引用，避免魔法数字散落各处。
"""

from PySide6.QtCore import QEasingCurve

# === Animation ===
# Durations (ms)
ANIM_MICRO = 80          # 微交互: hover, press
ANIM_FAST = 150          # 快速状态变化
ANIM_NORMAL = 250        # 标准过渡
ANIM_SLOW = 400          # 复杂动画
ANIM_STAGGER = 60        # 列表错开延迟

# Easing curves (PySide6 QEasingCurve.Type 枚举)
EASE_OUT_QUART = QEasingCurve.Type.OutQuart       # 入场 / 减速停止
EASE_IN_OUT = QEasingCurve.Type.InOutCubic         # 双向对称过渡
EASE_SPRING = QEasingCurve.Type.OutElastic          # 弹性效果

# === Scrollbar ===
# GitHub Dark 风格的细滚动条，全局可复用
SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: rgba(255,255,255,0.15);
        min-height: 32px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(255,255,255,0.28);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
        border: none;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        margin: 0;
        border: none;
    }
    QScrollBar::handle:horizontal {
        background: rgba(255,255,255,0.15);
        min-width: 32px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(255,255,255,0.28);
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
        border: none;
    }
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: transparent;
    }
"""
