# -*- coding: utf-8 -*-
"""UI 动画与视觉特效工具类。"""

from PyQt6.QtCore import (QPropertyAnimation, QEasingCurve, QObject, QEvent,
                          QParallelAnimationGroup, QSequentialAnimationGroup,
                          QTimer, QVariantAnimation)
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
                blur_start=effect.blurRadius(),
                blur_end=36,
                y_start=effect.yOffset(),
                y_end=4,
                alpha_start=effect.color().alpha(),
                alpha_end=200,
                duration=200,
                color=(37, 99, 235),
            )
        elif event.type() == QEvent.Type.Leave:
            UIAnimator.animate_shadow(
                effect,
                blur_start=effect.blurRadius(),
                blur_end=8,
                y_start=effect.yOffset(),
                y_end=1,
                alpha_start=effect.color().alpha(),
                alpha_end=30,
                duration=220,
                color=(37, 99, 235),
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
        shadow.setColor(QColor(37, 99, 235, alpha))
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
                       duration: int = 180,
                       color: tuple = (0, 212, 255)):
        """阴影动态变化，用于悬停/霓虹动效。"""
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

        r, g, b = color
        start_color = QColor(r, g, b, alpha_start)
        end_color   = QColor(r, g, b, alpha_end)
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
        """为按钮安装霓虹悬浮发光动画。"""
        effect = QGraphicsDropShadowEffect(button)
        effect.setBlurRadius(8)
        effect.setXOffset(0)
        effect.setYOffset(1)
        effect.setColor(QColor(37, 99, 235, 30))   # 科技蓝阴影（初始就稍微可见）
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

    @staticmethod
    def spring_height(widget: QWidget, start_h: int, end_h: int,
                      duration: int = 320) -> QSequentialAnimationGroup:
        """弹簧展开/收起高度动画（先过冲再回弹）。"""
        overshoot = end_h + int((end_h - start_h) * 0.08) if end_h > start_h else end_h
        group = QSequentialAnimationGroup(widget)

        a1 = QPropertyAnimation(widget, b"maximumHeight", widget)
        a1.setStartValue(start_h)
        a1.setEndValue(overshoot)
        a1.setDuration(int(duration * 0.72))
        a1.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(a1)

        a2 = QPropertyAnimation(widget, b"maximumHeight", widget)
        a2.setStartValue(overshoot)
        a2.setEndValue(end_h)
        a2.setDuration(int(duration * 0.28))
        a2.setEasingCurve(QEasingCurve.Type.InOutSine)
        group.addAnimation(a2)

        group.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return group

    @staticmethod
    def neon_install(widget: QWidget, r=0, g=212, b_=255, blur=22, alpha=60):
        """为控件添加静态霓虹发光阴影（持久存在，不需触发）。"""
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setXOffset(0)
        effect.setYOffset(0)
        effect.setColor(QColor(r, g, b_, alpha))
        widget.setGraphicsEffect(effect)
        return effect


class NeonPulse(QObject):
    """
    无限循环的霓虹脉冲动画，适合状态指示器/连接按钮/进度条边框。

    用法:
        self._pulse = NeonPulse(some_widget)
        self._pulse.start()
        # 停止: self._pulse.stop()
    """

    def __init__(self, widget: QWidget,
                 r: int = 0, g: int = 212, b: int = 255,
                 blur_min: int = 8, blur_max: int = 32,
                 alpha_min: int = 30, alpha_max: int = 160,
                 period: int = 1600,
                 parent: QObject = None):
        super().__init__(parent or widget)
        self._widget = widget
        self._r, self._g, self._b = r, g, b
        self._blur_min, self._blur_max = blur_min, blur_max
        self._alpha_min, self._alpha_max = alpha_min, alpha_max
        self._period = period
        self._effect = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._t = 0

    def start(self):
        self._effect = QGraphicsDropShadowEffect(self._widget)
        self._effect.setXOffset(0)
        self._effect.setYOffset(0)
        self._widget.setGraphicsEffect(self._effect)
        self._t = 0
        self._timer.start(16)   # ~60 fps

    def stop(self):
        self._timer.stop()
        if self._widget and self._effect:
            self._widget.setGraphicsEffect(None)
        self._effect = None

    def _tick(self):
        if not self._effect:
            return
        import math
        try:
            phase = (self._t % self._period) / self._period   # 0‧1
            s = (math.sin(phase * 2 * math.pi) + 1) / 2       # 0‧1
            blur  = self._blur_min  + s * (self._blur_max  - self._blur_min)
            alpha = int(self._alpha_min + s * (self._alpha_max - self._alpha_min))
            self._effect.setBlurRadius(blur)
            self._effect.setColor(QColor(self._r, self._g, self._b, alpha))
            self._t += 16
        except RuntimeError:
            # C++ 对象已被外部替换或销毁，停止定时器
            self._timer.stop()
            self._effect = None


class TypewriterEffect(QObject):
    """
    打字机文字逐字显示效果。

    用法:
        tw = TypewriterEffect(label_or_textedit, "正在连接设备...", speed=40)
        tw.start()
    """

    def __init__(self, widget, text: str, speed: int = 35, parent: QObject = None):
        super().__init__(parent or widget)
        self._widget = widget
        self._text = text
        self._speed = speed   # ms per char
        self._idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._idx = 0
        if hasattr(self._widget, 'setText'):
            self._widget.setText("")
        elif hasattr(self._widget, 'setPlainText'):
            self._widget.setPlainText("")
        self._timer.start(self._speed)

    def stop(self):
        self._timer.stop()

    def _tick(self):
        self._idx += 1
        partial = self._text[:self._idx]
        if hasattr(self._widget, 'setText'):
            self._widget.setText(partial)
        elif hasattr(self._widget, 'setPlainText'):
            self._widget.setPlainText(partial)
        if self._idx >= len(self._text):
            self._timer.stop()

