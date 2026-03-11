# -*- coding: utf-8 -*-
"""UI 动画与视觉特效工具类。"""

from PyQt6.QtCore import (QPropertyAnimation, QEasingCurve, QObject, QEvent,
                          QParallelAnimationGroup)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


class _ButtonHoverFilter(QObject):
    """按钮悬停时的轻微悬浮阴影动画。"""

    def eventFilter(self, obj, event):
        effect = getattr(obj, "_hover_shadow_effect", None)
        if effect is None:
            return False

        if event.type() == QEvent.Type.Enter:
            UIAnimator.animate_shadow(
                effect,
                blur_start=18,
                blur_end=30,
                y_start=3,
                y_end=8,
                alpha_start=38,
                alpha_end=72,
                duration=180,
            )
        elif event.type() == QEvent.Type.Leave:
            UIAnimator.animate_shadow(
                effect,
                blur_start=effect.blurRadius(),
                blur_end=18,
                y_start=effect.yOffset(),
                y_end=3,
                alpha_start=effect.color().alpha(),
                alpha_end=38,
                duration=180,
            )
        return False

class UIAnimator:
    """提供各种平滑 UI 动画效果"""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """淡入动画（动画结束后移除 effect）"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)

        def _cleanup():
            widget.setGraphicsEffect(None)

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim

    @staticmethod
    def slide_and_fade(widget: QWidget, duration: int = 400, offset: int = 20) -> QPropertyAnimation:
        """页面切换淡入动画（仅透明度渐变）。
        
        动画结束后主动移除 QGraphicsOpacityEffect，避免 effect 持续存在导致：
        - 鼠标坐标偏移 / hover 位置错乱
        - 子控件渲染被离屏缓冲区接管引起错位重叠
        """
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 动画结束后移除 effect，恢复正常渲染路径
        # 使用 KeepWhenStopped：由调用方持有引用并负责清理，
        # 避免 DeleteWhenStopped 导致 C++ 对象被销毁后 Python 侧调用崩溃
        def _cleanup():
            widget.setGraphicsEffect(None)

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim
        
    @staticmethod
    def add_soft_shadow(widget: QWidget, blur_radius: int = 15, x_offset: int = 0, y_offset: int = 4, alpha: int = 40):
        """为面板/卡片添加现代感柔和阴影"""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setXOffset(x_offset)
        shadow.setYOffset(y_offset)
        shadow.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(shadow)
        return shadow

    @staticmethod
    def animate_shadow(effect: QGraphicsDropShadowEffect,
                       blur_start: float,
                       blur_end: float,
                       y_start: float,
                       y_end: float,
                       alpha_start: int,
                       alpha_end: int,
                       duration: int = 180):
        """阴影动态变化，用于悬停微动效。"""
        group = QParallelAnimationGroup(effect)

        blur_anim = QPropertyAnimation(effect, b"blurRadius", effect)
        blur_anim.setStartValue(blur_start)
        blur_anim.setEndValue(blur_end)
        blur_anim.setDuration(duration)
        blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(blur_anim)

        y_anim = QPropertyAnimation(effect, b"yOffset", effect)
        y_anim.setStartValue(y_start)
        y_anim.setEndValue(y_end)
        y_anim.setDuration(duration)
        y_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(y_anim)

        start_color = QColor(65, 124, 255, alpha_start)
        end_color = QColor(65, 124, 255, alpha_end)
        color_anim = QPropertyAnimation(effect, b"color", effect)
        color_anim.setStartValue(start_color)
        color_anim.setEndValue(end_color)
        color_anim.setDuration(duration)
        color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(color_anim)

        group.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return group

    @staticmethod
    def install_button_hover(button: QWidget):
        """为按钮安装轻微悬浮动画。"""
        effect = QGraphicsDropShadowEffect(button)
        effect.setBlurRadius(18)
        effect.setXOffset(0)
        effect.setYOffset(3)
        effect.setColor(QColor(65, 124, 255, 38))
        button.setGraphicsEffect(effect)
        button._hover_shadow_effect = effect
        button._hover_filter = _ButtonHoverFilter(button)
        button.installEventFilter(button._hover_filter)

    @staticmethod
    def animate_width(widget: QWidget, start: int, end: int, duration: int = 220):
        """面板宽度动画。"""
        anim = QPropertyAnimation(widget, b"maximumWidth", widget)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim

    @staticmethod
    def pulse_widget(widget: QWidget, duration: int = 260,
                     start_opacity: float = 0.25,
                     end_opacity: float = 1.0) -> QPropertyAnimation:
        """对小型装饰控件做安全的淡入脉冲动画。"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setStartValue(start_opacity)
        anim.setEndValue(end_opacity)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _cleanup():
            widget.setGraphicsEffect(None)

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim
