# -*- coding: utf-8 -*-
"""
matplotlib 嵌入 PyQt6 的 Canvas 组件

使用 FigureCanvasQTAgg 将 matplotlib Figure 嵌入到 Qt 界面。
支持工具栏（缩放/平移/保存）。
"""

import matplotlib
matplotlib.use('Agg')  # 在导入 pyplot 前设置后端

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt


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

        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

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

        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

    def clear(self):
        """清空图表"""
        self._fig.clear()
        self._canvas.draw()

    def save_figure(self, filepath: str, dpi: int = 150):
        """保存当前图表到文件"""
        self._fig.savefig(filepath, dpi=dpi, bbox_inches='tight')

    @property
    def figure(self) -> Figure:
        return self._fig

    @property
    def canvas(self) -> MatplotlibCanvas:
        return self._canvas
