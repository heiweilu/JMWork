# -*- coding: utf-8 -*-
"""
粒子流背景 Widget
=================
在窗口最底层绘制漂浮粒子与连接线，营造赛博朋克科技感背景。

用法::

    from ui.widgets.particle_bg import ParticleBg

    # 在 QMainWindow 或任意 QWidget 中
    self._particle_bg = ParticleBg(parent=some_widget)
    self._particle_bg.resize(some_widget.size())
    some_widget.resizeEvent = lambda e: (
        some_widget.__class__.resizeEvent(some_widget, e),
        self._particle_bg.resize(e.size()),
    )
"""

import math
import random

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


# ─── 可调参数 ────────────────────────────────────────────────
PARTICLE_COUNT   = 80        # 粒子总数
LINK_DIST        = 130       # 连线最大距离（像素）
SPEED_MAX        = 0.45      # 最大速度（像素/帧）
RADIUS_MIN       = 1.5       # 粒子最小半径
RADIUS_MAX       = 4.0       # 粒子最大半径
FPS              = 30        # 刷新率
ALPHA_BG         = 0         # 背景 alphaﾈ0 = 全透明，由父窗口决定）

# 粒子颜色（浅色科技感，作为全屏叠加层少量显露即可）
_COLORS = [
    QColor(37,  99,  235),   # 科技蓝
    QColor(8,  145, 178),    # 青蓝
    QColor(124, 58,  237),   # 紫罗兰
    QColor(5,  150, 105),    # 科技绿
    QColor(100, 130, 200),   # 淡蓝
]
# ─────────────────────────────────────────────────────────────


class _Particle:
    """单个粒子数据"""
    __slots__ = ("x", "y", "vx", "vy", "radius", "color", "alpha")

    def __init__(self, w: int, h: int):
        self.reset(w, h, initial=True)

    def reset(self, w: int, h: int, initial: bool = False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if initial else random.uniform(-10, h + 10)
        speed = random.uniform(0.08, SPEED_MAX)
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(RADIUS_MIN, RADIUS_MAX)
        self.color  = random.choice(_COLORS)
        self.alpha  = random.randint(22, 58)    # 当作全屏加层：超低透明度，微妖动态纹理

    def move(self, w: int, h: int):
        self.x += self.vx
        self.y += self.vy
        # 反弹出边界的粒子从对侧重置
        pad = self.radius + 2
        if self.x < -pad:
            self.x = w + pad
        elif self.x > w + pad:
            self.x = -pad
        if self.y < -pad:
            self.y = h + pad
        elif self.y > h + pad:
            self.y = -pad


class ParticleBg(QWidget):
    """
    全透明粒子背景图层，置于父 Widget 最底层。

    Parameters
    ----------
    parent : QWidget
        父控件——粒子层将跟随该控件的大小。
    count : int
        粒子数量，默认 PARTICLE_COUNT。
    """

    def __init__(self, parent: QWidget = None, count: int = PARTICLE_COUNT):
        super().__init__(parent)

        # 使鼠标事件穿透，不影响下层控件
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        # 不绘制背景（全透明叠加）
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.Widget)

        w, h = max(self.width(), 1200), max(self.height(), 800)
        self._particles: list[_Particle] = [_Particle(w, h) for _ in range(count)]

        self._timer = QTimer(self)
        self._timer.setInterval(1000 // FPS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        # 不强制 lower/raise，由调用方决定层级
        if parent:
            self.resize(parent.size())

    # ── 公共方法 ──────────────────────────────────────────────

    def start(self):
        """（重）启动动画"""
        self._timer.start()

    def stop(self):
        """暂停动画"""
        self._timer.stop()

    # ── 内部 ─────────────────────────────────────────────────

    def _tick(self):
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return
        for p in self._particles:
            p.move(w, h)
        self.update()

    def paintEvent(self, event):  # noqa: N802
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pts = self._particles

        # ── 连线 ──────────────────────────────────────────────
        for i in range(len(pts)):
            pi = pts[i]
            for j in range(i + 1, len(pts)):
                pj = pts[j]
                dx = pi.x - pj.x
                dy = pi.y - pj.y
                dist = math.hypot(dx, dy)
                if dist < LINK_DIST:
                    # 距离越近越不透明
                    ratio = 1.0 - dist / LINK_DIST
                    a = int(min(pi.alpha, pj.alpha) * ratio * 0.55)
                    if a < 4:
                        continue
                    # 颜色取两粒子颜色均值
                    rc = (pi.color.red()   + pj.color.red())   // 2
                    gc = (pi.color.green() + pj.color.green()) // 2
                    bc = (pi.color.blue()  + pj.color.blue())  // 2
                    line_color = QColor(rc, gc, bc, a)
                    pen = QPen(line_color)
                    pen.setWidthF(0.75)
                    painter.setPen(pen)
                    painter.drawLine(int(pi.x), int(pi.y), int(pj.x), int(pj.y))

        # ── 粒子圆点 ──────────────────────────────────────────
        painter.setPen(Qt.PenStyle.NoPen)
        for p in pts:
            c = QColor(p.color.red(), p.color.green(), p.color.blue(), p.alpha)
            painter.setBrush(c)
            r = p.radius
            painter.drawEllipse(int(p.x - r), int(p.y - r), int(r * 2), int(r * 2))

        painter.end()

    def sizeHint(self) -> QSize:  # noqa: N802
        parent = self.parent()
        if parent and hasattr(parent, "size"):
            return parent.size()
        return QSize(1400, 900)
