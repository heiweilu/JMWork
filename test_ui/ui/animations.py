# -*- coding: utf-8 -*-
"""
UI 动画与视觉特效工具类
为 PyQt6 界面提供类似 Web (动漫/平滑) 的动画效果
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

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
