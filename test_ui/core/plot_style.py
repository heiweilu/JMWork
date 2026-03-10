# -*- coding: utf-8 -*-
"""
matplotlib 样式统一配置模块

合并了 9 个可视化脚本中的字体配置变体，提供统一函数。
"""

import matplotlib
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def setup_style(backend: str = 'Agg'):
    """
    统一配置 matplotlib 中文字体和全局样式。

    在所有可视化模块调用前执行一次即可。

    Args:
        backend: matplotlib 后端。'Agg' 用于无 GUI 环境（子线程/服务器），
                 None 使用默认后端。
    """
    if backend:
        matplotlib.use(backend)

    # 统一中文字体配置（兼容多个 Windows 环境）
    plt.rcParams['font.sans-serif'] = [
        'Microsoft YaHei', 'SimHei', 'PingFang SC',
        'WenQuanYi Micro Hei', 'DejaVu Sans'
    ]
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 10
    plt.rcParams['figure.dpi'] = 100


def create_figure(figsize: Tuple[float, float] = (16, 10),
                  dpi: int = 150) -> Tuple[plt.Figure, any]:
    """
    创建一个标准 Figure 对象（不依赖 plt.show()）。

    返回的 Figure 可用于:
    1. fig.savefig() 保存到文件
    2. FigureCanvasQTAgg(fig) 嵌入 PyQt6 界面

    Args:
        figsize: 图片尺寸 (宽, 高) 英寸
        dpi: 分辨率

    Returns:
        (fig, ax) 或 (fig, axes)
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.tight_layout(pad=2.0)
    return fig, ax


def create_gridspec_figure(figsize: Tuple[float, float] = (18, 12),
                           dpi: int = 150,
                           nrows: int = 2,
                           ncols: int = 2,
                           height_ratios: Optional[list] = None,
                           width_ratios: Optional[list] = None) -> Tuple[plt.Figure, any]:
    """
    创建带 GridSpec 布局的 Figure（多子图+结论文本区的常见布局）。

    Args:
        figsize: 图片尺寸
        dpi: 分辨率
        nrows: 网格行数
        ncols: 网格列数
        height_ratios: 行高比例
        width_ratios: 列宽比例

    Returns:
        (fig, gs) — gs 是 GridSpec 对象，使用 fig.add_subplot(gs[i, j]) 添加子图
    """
    from matplotlib.gridspec import GridSpec

    fig = plt.figure(figsize=figsize, dpi=dpi)
    gs = GridSpec(nrows, ncols, figure=fig,
                  height_ratios=height_ratios,
                  width_ratios=width_ratios)
    return fig, gs


def close_figure(fig: plt.Figure):
    """安全关闭 Figure，释放内存。"""
    plt.close(fig)
