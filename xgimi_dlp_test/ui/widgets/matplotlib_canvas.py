# -*- coding: utf-8 -*-
"""
matplotlib 嵌入 PyQt6 的 Canvas 组件

使用 FigureCanvasQTAgg 将 matplotlib Figure 嵌入到 Qt 界面。
支持工具栏（缩放/平移/保存）。
"""

import matplotlib
matplotlib.use('Agg')  # 在导入 pyplot 前设置后端

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QWheelEvent, QMouseEvent

# 缩放等级预设（倍率）
_ZOOM_STEPS = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0]


class MatplotlibCanvas(FigureCanvasQTAgg):
    """matplotlib Figure 的 Qt Widget 封装"""

    def __init__(self, fig: Figure = None, parent=None):
        if fig is None:
            fig = Figure(figsize=(10, 6), dpi=100)
        super().__init__(fig)
        self.setParent(parent)

    def update_figure(self, fig: Figure):
        """替换当前 Figure"""
        # 清理旧 figure
        old_fig = self.figure
        if old_fig is not None:
            plt.close(old_fig)

        self.figure = fig
        self.draw()


class PlotWidget(QWidget):
    """
    带工具栏的 matplotlib 绘图区域。

    包含:
    - 图表显示区 (FigureCanvasQTAgg)
    - 导航工具栏 (缩放/平移/保存/Home)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 初始空白 Figure
        self._fig = Figure(figsize=(10, 6), dpi=100)
        self._canvas = MatplotlibCanvas(self._fig, self)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)
        self._image_paths = []
        self._current_image_index = -1
        self._current_source_pixmap = None
        self._zoom_factor = 0.0   # 0.0 = 适应窗口；>0 = 固定倍率
        self._drag_start: QPoint | None = None  # 拖拽起始位置

        self._image_nav = QWidget(self)
        nav_layout = QHBoxLayout(self._image_nav)
        nav_layout.setContentsMargins(8, 6, 8, 6)
        nav_layout.setSpacing(8)
        self._btn_prev = QPushButton("◀ 上一张")
        self._btn_prev.clicked.connect(self._show_prev_image)
        nav_layout.addWidget(self._btn_prev)
        self._image_combo = QComboBox()
        self._image_combo.currentIndexChanged.connect(self._show_image_at)
        nav_layout.addWidget(self._image_combo, 1)
        self._btn_next = QPushButton("下一张 ▶")
        self._btn_next.clicked.connect(self._show_next_image)
        nav_layout.addWidget(self._btn_next)
        self._image_info = QLabel("")
        self._image_info.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._image_info.setStyleSheet("color: #666; font-size: 11px; padding-right: 6px;")
        nav_layout.addWidget(self._image_info)

        # 缩放控制按钮 — 紧凑样式覆盖全局 QPushButton padding
        _ZOOM_S = (
            "QPushButton { font-size:12px; padding:3px 8px 4px 8px; "
            "min-height:22px; min-width:28px; border-radius:6px; }"
            "QPushButton:hover { padding:2px 8px 5px 8px; }"
            "QPushButton:pressed { padding:5px 8px 2px 8px; }"
        )

        _btn_sep = QLabel("│")
        _btn_sep.setStyleSheet("color:#ccc; font-size:16px;")
        nav_layout.addWidget(_btn_sep)

        self._btn_zoom_out = QPushButton("缩小 -")
        self._btn_zoom_out.setStyleSheet(_ZOOM_S)
        self._btn_zoom_out.setToolTip("缩小图片  (Ctrl + 滚轮↓)")
        self._btn_zoom_out.clicked.connect(self._zoom_out)
        nav_layout.addWidget(self._btn_zoom_out)

        self._btn_zoom_fit = QPushButton("适应")
        self._btn_zoom_fit.setStyleSheet(_ZOOM_S)
        self._btn_zoom_fit.setToolTip("适应窗口大小（双击图片也可切换）")
        self._btn_zoom_fit.clicked.connect(self._zoom_fit)
        nav_layout.addWidget(self._btn_zoom_fit)

        self._btn_zoom_100 = QPushButton("1:1")
        self._btn_zoom_100.setStyleSheet(_ZOOM_S)
        self._btn_zoom_100.setToolTip("原始大小 (100%)")
        self._btn_zoom_100.clicked.connect(lambda: self._set_zoom(1.0))
        nav_layout.addWidget(self._btn_zoom_100)

        self._btn_zoom_in = QPushButton("放大 +")
        self._btn_zoom_in.setStyleSheet(_ZOOM_S)
        self._btn_zoom_in.setToolTip("放大图片  (Ctrl + 滚轮↑)")
        self._btn_zoom_in.clicked.connect(self._zoom_in)
        nav_layout.addWidget(self._btn_zoom_in)

        self._zoom_label = QLabel("适应")
        self._zoom_label.setStyleSheet(
            "color:#555; font-size:11px; min-width:42px; text-align:center;"
        )
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self._zoom_label)

        self._image_scroll = QScrollArea(self)
        self._image_scroll.setWidgetResizable(False)   # 手动控制 label 大小以支持缩放滚动
        self._image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background: #FAFAFA; padding: 0px;")
        # 鼠标拖拽滚动
        self._image_label.setMouseTracking(True)
        self._image_label.mousePressEvent   = self._img_mouse_press
        self._image_label.mouseMoveEvent    = self._img_mouse_move
        self._image_label.mouseReleaseEvent = self._img_mouse_release
        self._image_label.mouseDoubleClickEvent = self._img_double_click
        self._image_scroll.setWidget(self._image_label)

        layout.addWidget(self._toolbar)
        layout.addWidget(self._image_nav)
        layout.addWidget(self._canvas)
        layout.addWidget(self._image_scroll)

        self._set_mode('figure')

    def _set_mode(self, mode: str):
        is_figure = mode == 'figure'
        self._toolbar.setVisible(is_figure)
        self._canvas.setVisible(is_figure)
        self._image_nav.setVisible(not is_figure)
        self._image_scroll.setVisible(not is_figure)

    def display_figure(self, fig: Figure):
        """
        在界面中显示一个 matplotlib Figure。

        Args:
            fig: 由分析模块生成的 Figure 对象
        """
        # 移除旧的 canvas 和 toolbar
        layout = self.layout()
        layout.removeWidget(self._toolbar)
        layout.removeWidget(self._canvas)
        self._toolbar.deleteLater()
        self._canvas.deleteLater()

        # 创建新的 canvas
        self._fig = fig
        self._canvas = MatplotlibCanvas(fig, self)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        layout.insertWidget(0, self._toolbar)
        layout.insertWidget(2, self._canvas)
        self._set_mode('figure')
        self._image_paths = []
        self._current_image_index = -1
        self._current_source_pixmap = None

    def display_image_paths(self, image_paths: list[str]):
        """显示一个或多个输出图片，并支持切换。"""
        self._image_paths = [p for p in image_paths if p]
        self._image_combo.blockSignals(True)
        self._image_combo.clear()
        for p in self._image_paths:
            self._image_combo.addItem(os.path.basename(p), p)
        self._image_combo.blockSignals(False)
        self._zoom_factor = 0.0          # 每次新图片重置为适应窗口
        self._zoom_label.setText("适应")
        self._set_mode('image')
        if self._image_paths:
            self._show_image_at(0)
        else:
            self._image_label.setText("未找到可显示的图片")
            self._image_info.setText("")
            self._btn_prev.setEnabled(False)
            self._btn_next.setEnabled(False)

    def _show_image_at(self, index: int):
        if not self._image_paths or index < 0 or index >= len(self._image_paths):
            return
        self._current_image_index = index
        path = self._image_paths[index]
        pixmap = QPixmap(path)
        self._current_source_pixmap = pixmap if not pixmap.isNull() else None
        self._refresh_current_image()
        self._image_combo.blockSignals(True)
        self._image_combo.setCurrentIndex(index)
        self._image_combo.blockSignals(False)
        self._image_info.setText(f"{index + 1} / {len(self._image_paths)}")
        self._btn_prev.setEnabled(index > 0)
        self._btn_next.setEnabled(index < len(self._image_paths) - 1)

    def _refresh_current_image(self):
        if not self._current_source_pixmap or self._current_source_pixmap.isNull():
            self._image_label.setText("图片加载失败")
            self._image_label.setPixmap(QPixmap())
            return
        pw = self._current_source_pixmap.width()
        ph = self._current_source_pixmap.height()
        vp = self._image_scroll.viewport().size()
        vw = max(100, vp.width() - 4)
        vh = max(100, vp.height() - 4)

        if self._zoom_factor <= 0:
            # 适应窗口模式：按比例缩放至视口
            scaled = self._current_source_pixmap.scaled(
                vw, vh,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._zoom_label.setText("适应")
        else:
            new_w = max(1, int(pw * self._zoom_factor))
            new_h = max(1, int(ph * self._zoom_factor))
            scaled = self._current_source_pixmap.scaled(
                new_w, new_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._zoom_label.setText(f"{int(self._zoom_factor * 100)}%")

        self._image_label.setFixedSize(scaled.size())
        self._image_label.setPixmap(scaled)

    # ──────────────────── 缩放控制 ────────────────────

    def _zoom_in(self):
        """放大一级"""
        cur = self._current_zoom_ratio()
        for step in _ZOOM_STEPS:
            if step > cur + 0.01:
                self._set_zoom(step)
                return
        self._set_zoom(_ZOOM_STEPS[-1])

    def _zoom_out(self):
        """缩小一级"""
        cur = self._current_zoom_ratio()
        for step in reversed(_ZOOM_STEPS):
            if step < cur - 0.01:
                self._set_zoom(step)
                return
        self._set_zoom(_ZOOM_STEPS[0])

    def _zoom_fit(self):
        """切换为适应窗口模式"""
        self._zoom_factor = 0.0
        self._refresh_current_image()

    def _set_zoom(self, factor: float):
        """设置具体倍率并刷新"""
        self._zoom_factor = factor
        self._refresh_current_image()

    def _current_zoom_ratio(self) -> float:
        """返回当前实际缩放倍率（fit 模式下动态计算）"""
        if self._zoom_factor > 0:
            return self._zoom_factor
        if self._current_source_pixmap and not self._current_source_pixmap.isNull():
            pw = self._current_source_pixmap.width()
            ph = self._current_source_pixmap.height()
            vp = self._image_scroll.viewport().size()
            vw = max(1, vp.width() - 4)
            vh = max(1, vp.height() - 4)
            return min(vw / pw, vh / ph)
        return 1.0

    # ──────────────────── 拖拽滚动 ────────────────────

    def _img_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self._image_label.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _img_mouse_move(self, event: QMouseEvent):
        if self._drag_start is not None:
            delta = event.globalPosition().toPoint() - self._drag_start
            self._drag_start = event.globalPosition().toPoint()
            hbar = self._image_scroll.horizontalScrollBar()
            vbar = self._image_scroll.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())

    def _img_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            self._image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def _img_double_click(self, event: QMouseEvent):
        """双击切换适应窗口 ↔ 100%"""
        if self._zoom_factor <= 0:
            self._set_zoom(1.0)
        else:
            self._zoom_fit()

    # ──────────────────── 滚轮缩放 ────────────────────

    def wheelEvent(self, event: QWheelEvent):
        if (self._image_nav.isVisible() and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def _show_prev_image(self):
        if self._current_image_index > 0:
            self._show_image_at(self._current_image_index - 1)

    def _show_next_image(self):
        if self._current_image_index < len(self._image_paths) - 1:
            self._show_image_at(self._current_image_index + 1)

    def clear(self):
        """清空图表"""
        self._fig.clear()
        self._canvas.draw()
        self._image_paths = []
        self._current_image_index = -1
        self._current_source_pixmap = None
        self._zoom_factor = 0.0
        self._image_combo.clear()
        self._image_label.clear()
        self._image_label.setFixedSize(self._image_scroll.viewport().size())
        self._image_info.clear()
        self._zoom_label.setText("适应")
        self._set_mode('figure')

    def save_figure(self, filepath: str, dpi: int = 150):
        """保存当前图表到文件"""
        if self._toolbar.isVisible():
            self._fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        elif self._current_source_pixmap and not self._current_source_pixmap.isNull():
            self._current_source_pixmap.save(filepath)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._image_nav.isVisible():
            self._refresh_current_image()

    @property
    def figure(self) -> Figure:
        return self._fig

    @property
    def canvas(self) -> MatplotlibCanvas:
        return self._canvas
