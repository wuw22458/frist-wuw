"""动画控制 — AnimationController.

负责入场动画、暂停滤镜、脉冲效果等动画控制。
"""

from PySide6.QtCore import (
    QParallelAnimationGroup,
    QPropertyAnimation,
    QTimer,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from ui.style import ANIM_NORMAL, ANIM_STAGGER, EASE_OUT_QUART


class AnimationController:
    """动画控制器."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._animatable_cards: list[QWidget] = []
        self._running_anims: list = []
        self._animations_played = False

    def register_card(self, card: QWidget) -> None:
        """注册一个卡片用于入场动画."""
        self._animatable_cards.append(card)

    def setup_entrance(self) -> None:
        """预配置入场动画：将所有卡片设为不可见."""
        for card in self._animatable_cards:
            eff = QGraphicsOpacityEffect(card)
            eff.setOpacity(0.0)
            card.setGraphicsEffect(eff)

    def play_entrance(self) -> None:
        """播放错开的 fade-in + slide-up 入场动画."""
        if self._animations_played:
            return
        self._animations_played = True

        for i, card in enumerate(self._animatable_cards):
            delay = i * ANIM_STAGGER
            QTimer.singleShot(
                delay,
                lambda c=card, idx=i: self._animate_single_card(c, idx),
            )

    def _animate_single_card(self, card: QWidget, index: int) -> None:
        """动画单个卡片：fade-in + slide-up."""
        from PySide6.QtCore import QPoint

        slide_offset = 20  # pixels

        original_pos = card.pos()
        start_pos = QPoint(int(original_pos.x()), int(original_pos.y()) + slide_offset)

        group = QParallelAnimationGroup(self._parent)

        # Opacity animation
        eff = card.graphicsEffect()
        if isinstance(eff, QGraphicsOpacityEffect):
            opacity_anim = QPropertyAnimation(eff, b'opacity', self._parent)
            opacity_anim.setDuration(ANIM_NORMAL)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(EASE_OUT_QUART)
            group.addAnimation(opacity_anim)

        # Position animation (slide-up)
        pos_anim = QPropertyAnimation(card, b'pos', self._parent)
        pos_anim.setDuration(ANIM_NORMAL)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(original_pos)
        pos_anim.setEasingCurve(EASE_OUT_QUART)
        group.addAnimation(pos_anim)

        self._running_anims.append(group)
        group.finished.connect(lambda g=group: self._on_anim_finished(g))
        group.start()

    def _on_anim_finished(self, group) -> None:
        """清理已完成的动画引用."""
        if group in self._running_anims:
            self._running_anims.remove(group)

    @staticmethod
    def apply_pause_filter(widget: QWidget, paused: bool) -> None:
        """应用或移除暂停滤镜（淡出到 40%）."""
        if paused:
            eff = QGraphicsOpacityEffect(widget)
            eff.setOpacity(1.0)
            widget.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b'opacity', widget)
            anim.setDuration(300)
            anim.setStartValue(1.0)
            anim.setEndValue(0.4)
            anim.start()
        else:
            eff = widget.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                anim = QPropertyAnimation(eff, b'opacity', widget)
                anim.setDuration(300)
                anim.setStartValue(eff.opacity())
                anim.setEndValue(1.0)
                anim.finished.connect(lambda: widget.setGraphicsEffect(None))
                anim.start()
